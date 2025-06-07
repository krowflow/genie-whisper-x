"""
Voice Activity Detection Module - Silero VAD Implementation
Production-grade VAD for detecting voice segments in audio stream
"""
import asyncio
import numpy as np
import torch
import logging
from typing import Optional, AsyncGenerator, Tuple
import sounddevice as sd
from collections import deque
import os

class SileroVAD:
    """
    Production Voice Activity Detection using Silero VAD model
    Detects voice segments and yields audio chunks for wake word processing
    """
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 chunk_duration_ms: int = 30,
                 threshold: float = 0.5,
                 min_speech_duration_ms: int = 250,
                 min_silence_duration_ms: int = 500):
        """
        Initialize Silero VAD detector
        
        Args:
            sample_rate: Audio sample rate (16kHz recommended)
            chunk_duration_ms: Size of audio chunks to process
            threshold: VAD threshold (0.0-1.0, higher = more sensitive)
            min_speech_duration_ms: Minimum speech duration to trigger
            min_silence_duration_ms: Minimum silence to end speech
        """
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        
        # Calculate chunk size in samples
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        
        # VAD model and state
        self.model = None
        self.is_initialized = False
        self.is_listening = False
        
        # Audio buffer and state tracking
        self.audio_buffer = deque(maxlen=100)  # Keep last ~3 seconds
        self.speech_state = False
        self.speech_start_time = None
        self.silence_start_time = None
        
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> bool:
        """Initialize Silero VAD model"""
        try:
            self.logger.info("Initializing Silero VAD model...")
            
            # Load Silero VAD model
            model_path = "models/silero_vad.onnx"
            if not os.path.exists(model_path):
                self.logger.warning(f"Silero model not found at {model_path}, using torch hub")
                # Download from torch hub if local model not available
                self.model, utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False,
                    onnx=False
                )
            else:
                # Load local ONNX model (preferred for production)
                import onnxruntime as ort
                self.model = ort.InferenceSession(model_path)
                self.logger.info("Loaded local Silero ONNX model")
            
            self.is_initialized = True
            self.logger.info("Silero VAD initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize VAD: {e}")
            return False
    
    def _detect_voice_in_chunk(self, audio_chunk: np.ndarray) -> float:
        """
        Detect voice activity in audio chunk
        
        Args:
            audio_chunk: Audio data as numpy array
            
        Returns:
            Confidence score (0.0-1.0)
        """
        try:
            # Ensure audio is float32 and normalized
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            # Normalize to [-1, 1] range
            if np.max(np.abs(audio_chunk)) > 1.0:
                audio_chunk = audio_chunk / 32768.0
            
            # Convert to torch tensor for Silero
            audio_tensor = torch.from_numpy(audio_chunk).unsqueeze(0)
            
            # Get VAD prediction
            if hasattr(self.model, '__call__'):
                # Torch model
                with torch.no_grad():
                    confidence = self.model(audio_tensor, self.sample_rate).item()
            else:
                # ONNX model
                ort_inputs = {'input': audio_tensor.numpy()}
                confidence = self.model.run(None, ort_inputs)[0][0]
            
            return float(confidence)
            
        except Exception as e:
            self.logger.error(f"VAD detection error: {e}")
            return 0.0
    
    async def listen_for_voice(self) -> AsyncGenerator[Tuple[np.ndarray, bool], None]:
        """
        Continuously listen for voice activity and yield audio segments
        
        Yields:
            Tuple of (audio_data, is_speech_detected)
        """
        if not self.is_initialized:
            raise RuntimeError("VAD not initialized. Call initialize() first.")
        
        self.is_listening = True
        self.logger.info("Starting voice activity detection...")
        
        # Audio stream callback
        audio_queue = asyncio.Queue()
        
        def audio_callback(indata, frames, time, status):
            if status:
                self.logger.warning(f"Audio callback status: {status}")
            # Convert to mono if stereo
            if indata.shape[1] > 1:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata[:, 0]
            audio_queue.put_nowait(audio_data.copy())
        
        # Start audio stream
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            blocksize=self.chunk_size,
            callback=audio_callback
        ):
            self.logger.info(f"Audio stream started: {self.sample_rate}Hz, chunk_size={self.chunk_size}")
            
            try:
                while self.is_listening:
                    # Get audio chunk
                    audio_chunk = await audio_queue.get()
                    
                    # Add to buffer
                    self.audio_buffer.append(audio_chunk)
                    
                    # Detect voice activity
                    confidence = self._detect_voice_in_chunk(audio_chunk)
                    is_speech = confidence > self.threshold
                    
                    # State machine for speech detection
                    current_time = asyncio.get_event_loop().time()
                    
                    if is_speech and not self.speech_state:
                        # Speech started
                        self.speech_start_time = current_time
                        self.speech_state = True
                        self.silence_start_time = None
                        self.logger.debug(f"Speech started (confidence: {confidence:.3f})")
                        
                    elif not is_speech and self.speech_state:
                        # Potential speech end
                        if self.silence_start_time is None:
                            self.silence_start_time = current_time
                        elif (current_time - self.silence_start_time) * 1000 >= self.min_silence_duration_ms:
                            # Speech ended
                            speech_duration = (current_time - self.speech_start_time) * 1000
                            if speech_duration >= self.min_speech_duration_ms:
                                self.logger.debug(f"Speech ended (duration: {speech_duration:.0f}ms)")
                                # Yield complete speech segment
                                speech_audio = np.concatenate(list(self.audio_buffer))
                                yield speech_audio, True
                            
                            self.speech_state = False
                            self.speech_start_time = None
                            self.silence_start_time = None
                    
                    # Yield current chunk for real-time processing
                    yield audio_chunk, is_speech
                    
            except asyncio.CancelledError:
                self.logger.info("VAD listening cancelled")
                raise
            except Exception as e:
                self.logger.error(f"VAD listening error: {e}")
                raise
            finally:
                self.is_listening = False
    
    async def stop(self):
        """Stop voice activity detection"""
        self.is_listening = False
        self.logger.info("VAD stopped")
    
    def get_audio_buffer(self) -> np.ndarray:
        """Get current audio buffer as numpy array"""
        if self.audio_buffer:
            return np.concatenate(list(self.audio_buffer))
        return np.array([], dtype=np.float32)


class VoiceActivityDetector:
    """
    Main VAD interface - wraps Silero VAD implementation
    Provides async interface for voice activity detection
    """
    
    def __init__(self, vad_sensitivity: float = 0.6):
        """
        Initialize Voice Activity Detector
        
        Args:
            vad_sensitivity: VAD threshold from .env (0.0-1.0)
        """
        self.silero_vad = SileroVAD(threshold=vad_sensitivity)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize VAD system"""
        return await self.silero_vad.initialize()
    
    async def listen_for_voice(self) -> AsyncGenerator[Tuple[np.ndarray, bool], None]:
        """
        Listen for voice activity
        
        Yields:
            Tuple of (audio_data, is_speech_detected)
        """
        async for audio_data, is_speech in self.silero_vad.listen_for_voice():
            yield audio_data, is_speech
    
    async def stop(self):
        """Stop VAD"""
        await self.silero_vad.stop()
    
    def is_active(self) -> bool:
        """Check if VAD is currently listening"""
        return self.silero_vad.is_listening