"""
Piper TTS Implementation - Production Text-to-Speech Engine
Local, high-quality neural TTS with configurable voices
"""
import asyncio
import subprocess
import tempfile
import os
import logging
import numpy as np
from typing import Optional, Dict, List
from pathlib import Path
import json
import wave

class PiperTTS:
    """
    Production Piper TTS engine for local text-to-speech synthesis
    Supports multiple voices and configurations
    """
    
    def __init__(self, 
                 voice_name: str = "en_US-lessac-medium",
                 models_dir: str = "models/piper",
                 sample_rate: int = 22050,
                 speed: float = 1.0):
        """
        Initialize Piper TTS engine
        
        Args:
            voice_name: Voice model name (e.g., "en_US-lessac-medium")
            models_dir: Directory containing Piper voice models
            sample_rate: Output audio sample rate
            speed: Speech rate multiplier (0.5-2.0)
        """
        self.voice_name = voice_name
        self.models_dir = Path(models_dir)
        self.sample_rate = sample_rate
        self.speed = speed
        
        # Model files
        self.model_path = None
        self.config_path = None
        
        # Piper executable
        self.piper_executable = self._find_piper_executable()
        
        # State
        self.is_initialized = False
        
        self.logger = logging.getLogger(__name__)
    
    def _find_piper_executable(self) -> Optional[str]:
        """Find Piper executable in system or local installation"""
        # Check common installation paths
        possible_paths = [
            "piper",  # System PATH
            "./bin/piper",  # Local installation
            "./piper/piper",  # Downloaded binary
            "/usr/local/bin/piper",  # Linux system install
            "C:/Program Files/Piper/piper.exe",  # Windows install
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.logger.info(f"Found Piper executable: {path}")
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None
    
    async def initialize(self) -> bool:
        """Initialize Piper TTS with voice model"""
        try:
            self.logger.info(f"Initializing Piper TTS with voice: {self.voice_name}")
            
            # Check if Piper executable exists
            if not self.piper_executable:
                self.logger.error("Piper executable not found. Install Piper TTS first.")
                return False
            
            # Ensure models directory exists
            self.models_dir.mkdir(parents=True, exist_ok=True)
            
            # Check for voice model files
            self.model_path = self.models_dir / f"{self.voice_name}.onnx"
            self.config_path = self.models_dir / f"{self.voice_name}.onnx.json"
            
            # Download voice model if not present
            if not self.model_path.exists() or not self.config_path.exists():
                if not await self._download_voice_model():
                    return False
            
            # Validate model files
            if not await self._validate_model():
                return False
            
            self.is_initialized = True
            self.logger.info(f"Piper TTS initialized successfully with {self.voice_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Piper TTS initialization failed: {e}")
            return False
    
    async def _download_voice_model(self) -> bool:
        """Download Piper voice model if not available locally"""
        try:
            self.logger.info(f"Downloading Piper voice model: {self.voice_name}")
            
            # Piper voice download URLs (Hugging Face)
            base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
            
            # Determine language and model paths
            lang_code = self.voice_name.split('-')[0]  # e.g., "en_US"
            
            model_url = f"{base_url}/{lang_code}/{self.voice_name}.onnx"
            config_url = f"{base_url}/{lang_code}/{self.voice_name}.onnx.json"
            
            # Download model file
            if not await self._download_file(model_url, self.model_path):
                return False
            
            # Download config file
            if not await self._download_file(config_url, self.config_path):
                return False
            
            self.logger.info(f"Voice model {self.voice_name} downloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Voice model download failed: {e}")
            return False
    
    async def _download_file(self, url: str, dest_path: Path) -> bool:
        """Download file from URL to destination"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(dest_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        return True
                    else:
                        self.logger.error(f"Download failed: {url} -> HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"File download error: {e}")
            return False
    
    async def _validate_model(self) -> bool:
        """Validate that model files are correct and accessible"""
        try:
            # Check file existence
            if not self.model_path.exists():
                self.logger.error(f"Model file not found: {self.model_path}")
                return False
            
            if not self.config_path.exists():
                self.logger.error(f"Config file not found: {self.config_path}")
                return False
            
            # Validate config JSON
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Basic config validation
            required_keys = ['audio', 'inference', 'phoneme_type']
            for key in required_keys:
                if key not in config:
                    self.logger.error(f"Invalid config: missing '{key}'")
                    return False
            
            self.logger.debug(f"Model validation passed: {self.voice_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Model validation failed: {e}")
            return False
    
    async def speak(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech using Piper TTS
        
        Args:
            text: Text to synthesize
            output_file: Optional output WAV file path
            
        Returns:
            Path to generated audio file or None on error
        """
        if not self.is_initialized:
            raise RuntimeError("Piper TTS not initialized")
        
        try:
            # Create temporary output file if not specified
            if output_file is None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                output_file = temp_file.name
                temp_file.close()
            
            # Build Piper command
            cmd = [
                self.piper_executable,
                "--model", str(self.model_path),
                "--config", str(self.config_path),
                "--output-file", output_file
            ]
            
            # Add speed parameter if supported
            if self.speed != 1.0:
                cmd.extend(["--length-scale", str(1.0 / self.speed)])
            
            self.logger.debug(f"Running Piper command: {' '.join(cmd)}")
            
            # Run Piper TTS
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send text to Piper stdin
            stdout, stderr = await process.communicate(input=text.encode('utf-8'))
            
            if process.returncode == 0:
                self.logger.debug(f"TTS synthesis completed: {output_file}")
                return output_file
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                self.logger.error(f"Piper TTS failed: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"TTS synthesis error: {e}")
            return None
    
    async def speak_and_play(self, text: str) -> bool:
        """
        Synthesize text and immediately play audio
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate audio file
            audio_file = await self.speak(text)
            if not audio_file:
                return False
            
            # Play audio file
            success = await self._play_audio_file(audio_file)
            
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass
            
            return success
            
        except Exception as e:
            self.logger.error(f"Speak and play error: {e}")
            return False
    
    async def _play_audio_file(self, audio_file: str) -> bool:
        """Play audio file using system audio player"""
        try:
            # Try different audio players based on platform
            players = []
            
            # Windows
            if os.name == 'nt':
                players = ['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_file}").PlaySync()']
            
            # Linux/macOS
            else:
                for player in ['aplay', 'paplay', 'afplay', 'sox']:
                    try:
                        subprocess.run(['which', player], check=True, capture_output=True)
                        if player == 'sox':
                            players = ['play', audio_file]
                        else:
                            players = [player, audio_file]
                        break
                    except subprocess.CalledProcessError:
                        continue
            
            if not players:
                self.logger.error("No audio player found")
                return False
            
            # Play audio
            process = await asyncio.create_subprocess_exec(
                *players,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            return process.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
            return False
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voice models"""
        voices = []
        if self.models_dir.exists():
            for model_file in self.models_dir.glob("*.onnx"):
                voice_name = model_file.stem
                if voice_name.endswith('.onnx'):
                    voice_name = voice_name[:-5]  # Remove .onnx extension
                voices.append(voice_name)
        return voices
    
    async def stop(self):
        """Stop TTS engine"""
        self.is_initialized = False
        self.logger.info("Piper TTS stopped")