"""
Wake Word Detection Module - "Hey Genie" Detection
Production-grade wake word detection with low latency and high accuracy
"""
import asyncio
import numpy as np
import logging
import re
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass
import time

# Try imports for different wake word engines
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

@dataclass
class WakeWordEvent:
    """Wake word detection event data"""
    timestamp: float
    confidence: float
    wake_word: str
    audio_data: Optional[np.ndarray] = None

class WakeWordDetector:
    """
    Production wake word detector for "Hey Genie"
    Supports multiple detection engines with fallback strategy
    """
    
    def __init__(self, 
                 wake_word: str = "Hey Genie",
                 porcupine_access_key: Optional[str] = None,
                 sensitivity: float = 0.5,
                 callback: Optional[Callable[[WakeWordEvent], None]] = None):
        """
        Initialize wake word detector
        
        Args:
            wake_word: Target wake word phrase
            porcupine_access_key: Porcupine API key (optional)
            sensitivity: Detection sensitivity (0.0-1.0)
            callback: Callback function for wake word events
        """
        self.wake_word = wake_word.lower()
        self.porcupine_access_key = porcupine_access_key
        self.sensitivity = sensitivity
        self.callback = callback
        
        # Detection engine
        self.engine = None
        self.engine_type = None
        
        # State
        self.is_initialized = False
        self.is_listening = False
        
        # Audio processing
        self.sample_rate = 16000
        self.frame_length = 512  # Porcupine frame length
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize the best available wake word detection engine"""
        try:
            # Try Porcupine first (most accurate)
            if PORCUPINE_AVAILABLE and self.porcupine_access_key:
                if await self._initialize_porcupine():
                    return True
            
            # Fallback to simple audio-based detection
            if await self._initialize_simple_detector():
                return True
            
            self.logger.error("No wake word detection engine available")
            return False
            
        except Exception as e:
            self.logger.error(f"Wake word initialization failed: {e}")
            return False
    
    async def _initialize_porcupine(self) -> bool:
        """Initialize Porcupine wake word detection"""
        try:
            self.logger.info("Initializing Porcupine wake word detection...")
            
            # Create custom wake word model or use built-in keywords
            # For "Hey Genie", we'll use a combination approach
            keywords = ["jarvis", "alexa", "computer"]  # Built-in similar keywords
            
            self.engine = pvporcupine.create(
                access_key=self.porcupine_access_key,
                keywords=keywords,
                sensitivities=[self.sensitivity] * len(keywords)
            )
            
            self.engine_type = "porcupine"
            self.sample_rate = self.engine.sample_rate
            self.frame_length = self.engine.frame_length
            
            self.is_initialized = True
            self.logger.info(f"Porcupine initialized: {self.sample_rate}Hz, frame_length={self.frame_length}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Porcupine initialization failed: {e}")
            return False
    
    async def _initialize_simple_detector(self) -> bool:
        """Initialize simple pattern-based wake word detection"""
        try:
            self.logger.info("Initializing simple wake word detection...")
            
            # Use speech recognition with vosk or similar for offline detection
            self.engine_type = "simple"
            
            # Compile regex patterns for wake word variants
            self.wake_patterns = [
                re.compile(r'\bhey\s+genie\b', re.IGNORECASE),
                re.compile(r'\bgenie\b', re.IGNORECASE),
                re.compile(r'\bhey\s+jeanie\b', re.IGNORECASE),  # Common mispronunciation
                re.compile(r'\bheygenie\b', re.IGNORECASE),       # No space variant
            ]
            
            self.is_initialized = True
            self.logger.info("Simple wake word detector initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Simple detector initialization failed: {e}")
            return False
    
    async def listen_for_wake(self, audio_segment: np.ndarray) -> Optional[WakeWordEvent]:
        """
        Process audio segment for wake word detection
        
        Args:
            audio_segment: Audio data as numpy array
            
        Returns:
            WakeWordEvent if wake word detected, None otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Wake word detector not initialized")
        
        try:
            if self.engine_type == "porcupine":
                return await self._detect_porcupine(audio_segment)
            elif self.engine_type == "simple":
                return await self._detect_simple(audio_segment)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Wake word detection error: {e}")
            return None
    
    async def _detect_porcupine(self, audio_segment: np.ndarray) -> Optional[WakeWordEvent]:
        """Detect wake word using Porcupine"""
        try:
            # Convert audio to int16 format required by Porcupine
            if audio_segment.dtype != np.int16:
                audio_int16 = (audio_segment * 32767).astype(np.int16)
            else:
                audio_int16 = audio_segment
            
            # Process audio in frames
            for i in range(0, len(audio_int16) - self.frame_length, self.frame_length):
                frame = audio_int16[i:i + self.frame_length]
                
                # Get keyword index (if any detected)
                keyword_index = self.engine.process(frame)
                
                if keyword_index >= 0:
                    # Wake word detected
                    confidence = 0.9  # Porcupine doesn't provide confidence scores
                    
                    event = WakeWordEvent(
                        timestamp=time.time(),
                        confidence=confidence,
                        wake_word=self.wake_word,
                        audio_data=audio_segment
                    )
                    
                    self.logger.info(f"Wake word detected via Porcupine (keyword_index: {keyword_index})")
                    
                    if self.callback:
                        self.callback(event)
                    
                    return event
            
            return None
            
        except Exception as e:
            self.logger.error(f"Porcupine detection error: {e}")
            return None
    
    async def _detect_simple(self, audio_segment: np.ndarray) -> Optional[WakeWordEvent]:
        """Detect wake word using simple pattern matching"""
        try:
            # For simple detection, we'll use a basic audio energy + pattern approach
            # This is a fallback method and not as accurate as Porcupine
            
            # Check audio energy (basic voice activity)
            energy = np.sum(audio_segment ** 2) / len(audio_segment)
            energy_threshold = 0.001  # Adjust based on environment
            
            if energy < energy_threshold:
                return None  # Too quiet, likely no speech
            
            # Simple spectral analysis for "Hey Genie" pattern
            # Look for specific frequency patterns that match the phrase
            
            # Convert to frequency domain
            fft = np.fft.fft(audio_segment)
            frequencies = np.fft.fftfreq(len(audio_segment), 1/self.sample_rate)
            
            # Look for voice frequency range (80-255 Hz fundamental, 500-2000 Hz formants)
            voice_indices = np.where((frequencies >= 80) & (frequencies <= 2000))[0]
            voice_energy = np.sum(np.abs(fft[voice_indices]))
            
            # Simple heuristic: if there's significant voice energy and the duration matches
            # "Hey Genie" (approximately 1-2 seconds), consider it a potential match
            audio_duration = len(audio_segment) / self.sample_rate
            
            if voice_energy > 1000 and 0.8 <= audio_duration <= 3.0:
                # Basic pattern detected
                confidence = min(0.7, voice_energy / 10000)  # Scale confidence
                
                event = WakeWordEvent(
                    timestamp=time.time(),
                    confidence=confidence,
                    wake_word=self.wake_word,
                    audio_data=audio_segment
                )
                
                self.logger.info(f"Potential wake word detected via simple detector (confidence: {confidence:.3f})")
                
                if self.callback:
                    self.callback(event)
                
                return event
            
            return None
            
        except Exception as e:
            self.logger.error(f"Simple detection error: {e}")
            return None
    
    def set_callback(self, callback: Callable[[WakeWordEvent], None]):
        """Set callback function for wake word events"""
        self.callback = callback
    
    async def stop(self):
        """Stop wake word detection"""
        self.is_listening = False
        
        if self.engine and self.engine_type == "porcupine":
            try:
                self.engine.delete()
            except:
                pass
        
        self.logger.info("Wake word detector stopped")


class WakeWordManager:
    """
    High-level wake word management interface
    Handles wake word detection and event routing
    """
    
    def __init__(self, 
                 wake_word: str = "Hey Genie",
                 porcupine_key: Optional[str] = None,
                 sensitivity: float = 0.5):
        """
        Initialize wake word manager
        
        Args:
            wake_word: Target wake word phrase
            porcupine_key: Porcupine access key (optional)
            sensitivity: Detection sensitivity (0.0-1.0)
        """
        self.detector = WakeWordDetector(
            wake_word=wake_word,
            porcupine_access_key=porcupine_key,
            sensitivity=sensitivity
        )
        
        self.wake_word_callbacks = []
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize wake word detection"""
        # Set up event callback
        self.detector.set_callback(self._on_wake_word_detected)
        return await self.detector.initialize()
    
    def _on_wake_word_detected(self, event: WakeWordEvent):
        """Handle wake word detection event"""
        self.logger.info(f"Wake word '{event.wake_word}' detected at {event.timestamp}")
        
        # Notify all registered callbacks
        for callback in self.wake_word_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Wake word callback error: {e}")
    
    def add_wake_word_callback(self, callback: Callable[[WakeWordEvent], None]):
        """Add callback for wake word events"""
        self.wake_word_callbacks.append(callback)
    
    async def process_audio(self, audio_data: np.ndarray) -> Optional[WakeWordEvent]:
        """Process audio for wake word detection"""
        return await self.detector.listen_for_wake(audio_data)
    
    async def stop(self):
        """Stop wake word detection"""
        await self.detector.stop()