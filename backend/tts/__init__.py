"""
Text-to-Speech Module - Production TTS with Piper Engine
Configurable TTS with fallback engines for compatibility
"""
import asyncio
import logging
import os
from typing import Optional, Dict, Any
from .piper_tts import PiperTTS

# Fallback TTS engines
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

class TextToSpeech:
    """
    Production text-to-speech processor with multiple engine support
    Primary: Piper TTS (local, high-quality)
    Fallbacks: Edge-TTS, pyttsx3
    """
    
    def __init__(self, 
                 engine_type: str = "piper",
                 voice_name: str = "en_US-lessac-medium",
                 speed: float = 1.0):
        """
        Initialize TTS processor
        
        Args:
            engine_type: TTS engine ("piper", "edge-tts", "pyttsx3")
            voice_name: Voice model name
            speed: Speech rate (0.5-2.0)
        """
        self.engine_type = engine_type
        self.voice_name = voice_name
        self.speed = speed
        
        # TTS engines
        self.piper_engine = None
        self.pyttsx3_engine = None
        self.current_engine = None
        
        # State
        self.is_initialized = False
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize TTS engine with fallback strategy"""
        try:
            self.logger.info(f"Initializing TTS engine: {self.engine_type}")
            
            # Try primary engine first
            if self.engine_type == "piper":
                if await self._initialize_piper():
                    return True
            elif self.engine_type == "edge-tts":
                if await self._initialize_edge_tts():
                    return True
            elif self.engine_type == "pyttsx3":
                if await self._initialize_pyttsx3():
                    return True
            
            # Fallback strategy
            self.logger.warning(f"Primary TTS engine '{self.engine_type}' failed, trying fallbacks...")
            
            # Try Piper first (best quality)
            if self.engine_type != "piper" and await self._initialize_piper():
                return True
            
            # Try pyttsx3 (most compatible)
            if self.engine_type != "pyttsx3" and await self._initialize_pyttsx3():
                return True
            
            # Try Edge-TTS (requires internet)
            if self.engine_type != "edge-tts" and await self._initialize_edge_tts():
                return True
            
            self.logger.error("No TTS engine available")
            return False
            
        except Exception as e:
            self.logger.error(f"TTS initialization failed: {e}")
            return False
    
    async def _initialize_piper(self) -> bool:
        """Initialize Piper TTS engine"""
        try:
            self.piper_engine = PiperTTS(
                voice_name=self.voice_name,
                speed=self.speed
            )
            
            if await self.piper_engine.initialize():
                self.current_engine = "piper"
                self.is_initialized = True
                self.logger.info("Piper TTS engine initialized")
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Piper TTS initialization failed: {e}")
            return False
    
    async def _initialize_edge_tts(self) -> bool:
        """Initialize Edge-TTS engine"""
        try:
            if not EDGE_TTS_AVAILABLE:
                self.logger.warning("Edge-TTS not available")
                return False
            
            # Test Edge-TTS connection
            communicate = edge_tts.Communicate("test", "en-US-AriaNeural")
            # Try to generate a small test to verify connection
            test_audio = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    test_audio += chunk["data"]
                    break  # Just test connection
            
            if test_audio:
                self.current_engine = "edge-tts"
                self.is_initialized = True
                self.logger.info("Edge-TTS engine initialized")
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Edge-TTS initialization failed: {e}")
            return False
    
    async def _initialize_pyttsx3(self) -> bool:
        """Initialize pyttsx3 engine"""
        try:
            if not PYTTSX3_AVAILABLE:
                self.logger.warning("pyttsx3 not available")
                return False
            
            self.pyttsx3_engine = pyttsx3.init()
            
            # Configure voice and speed
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                # Try to find a suitable voice
                for voice in voices:
                    if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                        self.pyttsx3_engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate
            rate = self.pyttsx3_engine.getProperty('rate')
            self.pyttsx3_engine.setProperty('rate', int(rate * self.speed))
            
            self.current_engine = "pyttsx3"
            self.is_initialized = True
            self.logger.info("pyttsx3 engine initialized")
            return True
            
        except Exception as e:
            self.logger.warning(f"pyttsx3 initialization failed: {e}")
            return False
    
    async def speak(self, text: str) -> bool:
        """
        Convert text to speech and play
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("TTS not initialized")
        
        try:
            self.logger.info(f"Speaking with {self.current_engine}: '{text[:50]}...'")
            
            if self.current_engine == "piper":
                return await self.piper_engine.speak_and_play(text)
            
            elif self.current_engine == "edge-tts":
                return await self._speak_edge_tts(text)
            
            elif self.current_engine == "pyttsx3":
                return await self._speak_pyttsx3(text)
            
            else:
                self.logger.error(f"Unknown TTS engine: {self.current_engine}")
                return False
                
        except Exception as e:
            self.logger.error(f"TTS speak error: {e}")
            return False
    
    async def _speak_edge_tts(self, text: str) -> bool:
        """Speak using Edge-TTS"""
        try:
            import tempfile
            
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            await communicate.save(temp_path)
            
            # Play audio file
            success = await self.piper_engine._play_audio_file(temp_path) if self.piper_engine else False
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return success
            
        except Exception as e:
            self.logger.error(f"Edge-TTS speak error: {e}")
            return False
    
    async def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3"""
        try:
            # pyttsx3 is synchronous, run in executor
            loop = asyncio.get_event_loop()
            
            def _speak_sync():
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
            
            await loop.run_in_executor(None, _speak_sync)
            return True
            
        except Exception as e:
            self.logger.error(f"pyttsx3 speak error: {e}")
            return False
    
    async def speak_wake_response(self, response_text: str = "Yes, Master") -> bool:
        """
        Speak wake word response
        
        Args:
            response_text: Response to speak when wake word detected
            
        Returns:
            True if successful
        """
        return await self.speak(response_text)
    
    def get_current_engine(self) -> str:
        """Get currently active TTS engine"""
        return self.current_engine if self.is_initialized else None
    
    def get_available_engines(self) -> Dict[str, bool]:
        """Get status of available TTS engines"""
        return {
            "piper": self.piper_engine is not None,
            "edge-tts": EDGE_TTS_AVAILABLE,
            "pyttsx3": PYTTSX3_AVAILABLE
        }
    
    async def stop(self):
        """Stop TTS and clean up resources"""
        if self.piper_engine:
            await self.piper_engine.stop()
        
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.stop()
            except:
                pass
        
        self.is_initialized = False
        self.logger.info("TTS engine stopped")