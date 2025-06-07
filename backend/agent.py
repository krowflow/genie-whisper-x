"""
Genie Whisper X - Main Agent Event Loop
Production agent orchestrating the voice processing pipeline: VAD → Wake Word → TTS → STT → Commands
"""
import asyncio
import logging
import os
from typing import Optional
from enum import Enum

# Import production modules
from vad.vad import VoiceActivityDetector
from vad.wakeword import WakeWordManager, WakeWordEvent
from whisper import WhisperSTT
from tts import TextToSpeech
from commands import CommandEngine

class AgentState(Enum):
    """Agent operational states"""
    IDLE = "idle"
    LISTENING_VAD = "listening_vad"
    WAKE_WORD_DETECTED = "wake_word_detected"
    LISTENING_COMMAND = "listening_command"
    PROCESSING_COMMAND = "processing_command"
    SPEAKING_RESPONSE = "speaking_response"
    ERROR = "error"

class GenieAgent:
    """
    Production agent orchestrating voice processing pipeline
    Event Flow: VAD → Wake Word → TTS("Yes, Master") → Whisper → Command Processing
    """
    
    def __init__(self, 
                 wake_word: str = "Hey Genie",
                 wake_response: str = "Yes, Master",
                 vad_sensitivity: float = 0.6,
                 tts_engine: str = "piper",
                 tts_voice: str = "en_US-lessac-medium"):
        """
        Initialize Genie Agent with production configuration
        
        Args:
            wake_word: Wake word phrase to detect
            wake_response: TTS response when wake word detected
            vad_sensitivity: Voice activity detection sensitivity (0.0-1.0)
            tts_engine: TTS engine type ("piper", "edge-tts", "pyttsx3")
            tts_voice: TTS voice model name
        """
        # Configuration
        self.wake_word = wake_word
        self.wake_response = wake_response
        self.vad_sensitivity = vad_sensitivity
        self.tts_engine = tts_engine
        self.tts_voice = tts_voice
        
        # Agent state
        self.state = AgentState.IDLE
        self.is_running = False
        
        # Production modules
        self.vad: Optional[VoiceActivityDetector] = None
        self.wake_word_manager: Optional[WakeWordManager] = None
        self.stt: Optional[WhisperSTT] = None
        self.tts: Optional[TextToSpeech] = None
        self.commands: Optional[CommandEngine] = None
        
        # Event tracking
        self.wake_events_count = 0
        self.command_sessions = 0
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Genie Agent initialized - Wake: '{wake_word}' → Response: '{wake_response}'")
    
    async def initialize(self) -> bool:
        """Initialize all agent modules in production configuration"""
        try:
            self.logger.info("Initializing production agent modules...")
            
            # Initialize Voice Activity Detection
            self.vad = VoiceActivityDetector(vad_sensitivity=self.vad_sensitivity)
            if not await self.vad.initialize():
                self.logger.error("VAD initialization failed")
                return False
            self.logger.info("✅ VAD initialized")
            
            # Initialize Wake Word Detection
            porcupine_key = os.getenv('PORCUPINE_ACCESS_KEY')
            self.wake_word_manager = WakeWordManager(
                wake_word=self.wake_word,
                porcupine_key=porcupine_key,
                sensitivity=self.vad_sensitivity
            )
            
            if not await self.wake_word_manager.initialize():
                self.logger.error("Wake word manager initialization failed")
                return False
            
            # Register wake word callback
            self.wake_word_manager.add_wake_word_callback(self._on_wake_word_detected)
            self.logger.info(f"✅ Wake word detection initialized for '{self.wake_word}'")
            
            # Initialize Text-to-Speech
            self.tts = TextToSpeech(
                engine_type=self.tts_engine,
                voice_name=self.tts_voice,
                speed=1.0
            )
            
            if not await self.tts.initialize():
                self.logger.error("TTS initialization failed")
                return False
            self.logger.info(f"✅ TTS initialized ({self.tts.get_current_engine()})")
            
            # Initialize Whisper STT (placeholder for now)
            # self.stt = WhisperSTT()
            # if not await self.stt.initialize():
            #     self.logger.error("STT initialization failed")
            #     return False
            self.logger.info("✅ STT ready (placeholder)")
            
            # Initialize Command Engine (placeholder for now)
            # self.commands = CommandEngine()
            # if not await self.commands.initialize():
            #     self.logger.error("Commands initialization failed")
            #     return False
            self.logger.info("✅ Commands ready (placeholder)")
            
            self.logger.info("🚀 All agent modules initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Agent initialization failed: {e}")
            return False
    
    def _on_wake_word_detected(self, event: WakeWordEvent):
        """
        Handle wake word detection event
        Triggers immediate TTS response and state transition
        """
        self.wake_events_count += 1
        self.logger.info(f"🎯 Wake word detected #{self.wake_events_count}: '{event.wake_word}' "
                        f"(confidence: {event.confidence:.3f})")
        
        # Transition to wake word detected state
        self.state = AgentState.WAKE_WORD_DETECTED
        
        # Schedule immediate TTS response
        asyncio.create_task(self._handle_wake_response())
    
    async def _handle_wake_response(self):
        """Handle wake word response with TTS"""
        try:
            self.state = AgentState.SPEAKING_RESPONSE
            self.logger.info(f"🔊 Speaking wake response: '{self.wake_response}'")
            
            # Speak the wake response
            success = await self.tts.speak_wake_response(self.wake_response)
            
            if success:
                self.logger.info("✅ Wake response completed successfully")
                # Transition to command listening mode
                self.state = AgentState.LISTENING_COMMAND
                self.command_sessions += 1
                self.logger.info(f"👂 Now listening for commands (session #{self.command_sessions})")
                
                # Set timeout for command listening (30 seconds)
                await asyncio.sleep(30)
                
                # Return to VAD listening if no command received
                if self.state == AgentState.LISTENING_COMMAND:
                    self.logger.info("⏰ Command timeout - returning to wake word detection")
                    self.state = AgentState.LISTENING_VAD
            else:
                self.logger.error("❌ Wake response failed")
                self.state = AgentState.ERROR
                await asyncio.sleep(2)  # Brief error cooldown
                self.state = AgentState.LISTENING_VAD
                
        except Exception as e:
            self.logger.error(f"Wake response error: {e}")
            self.state = AgentState.ERROR
            await asyncio.sleep(2)
            self.state = AgentState.LISTENING_VAD
    
    async def start(self):
        """Start the main agent event loop with production pipeline"""
        if not await self.initialize():
            self.logger.error("❌ Agent initialization failed - cannot start")
            return
            
        self.is_running = True
        self.state = AgentState.LISTENING_VAD
        
        self.logger.info("🧞 Genie Agent started - Production Event Loop Active")
        self.logger.info(f"   Wake Word: '{self.wake_word}'")
        self.logger.info(f"   Response: '{self.wake_response}'")
        self.logger.info(f"   TTS Engine: {self.tts.get_current_engine()}")
        self.logger.info("   State: LISTENING_VAD → monitoring for voice activity...")
        
        try:
            # Main production event loop
            async for audio_data, is_speech in self.vad.listen_for_voice():
                if not self.is_running:
                    break
                
                # Process audio based on current state
                if self.state == AgentState.LISTENING_VAD:
                    # In VAD monitoring mode - check for wake word
                    if is_speech:
                        # Voice detected - process for wake word
                        wake_event = await self.wake_word_manager.process_audio(audio_data)
                        if wake_event:
                            # Wake word detected - callback will handle response
                            continue
                
                elif self.state == AgentState.LISTENING_COMMAND:
                    # In command listening mode - process with STT
                    if is_speech:
                        self.logger.info("🎤 Command audio detected - processing with STT...")
                        # TODO: Process with Whisper STT
                        # transcript = await self.stt.transcribe(audio_data)
                        # command_result = await self.commands.execute_command(transcript)
                        # await self.tts.speak(command_result)
                        
                        # For now, just return to VAD mode
                        self.logger.info("📝 Command processing placeholder - returning to VAD mode")
                        self.state = AgentState.LISTENING_VAD
                
                elif self.state in [AgentState.WAKE_WORD_DETECTED, AgentState.SPEAKING_RESPONSE]:
                    # Currently handling wake word response - ignore new audio
                    continue
                
                elif self.state == AgentState.ERROR:
                    # Error state - attempt recovery
                    self.logger.warning("⚠️ Agent in error state - attempting recovery...")
                    await asyncio.sleep(1)
                    self.state = AgentState.LISTENING_VAD
                
                # Brief yield for other tasks
                await asyncio.sleep(0.01)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Received shutdown signal")
        except Exception as e:
            self.logger.error(f"❌ Agent event loop error: {e}")
            self.state = AgentState.ERROR
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Clean shutdown of agent with proper cleanup"""
        self.is_running = False
        self.state = AgentState.IDLE
        
        self.logger.info("🛑 Genie Agent shutting down...")
        
        # Log session statistics
        self.logger.info(f"   Session Stats:")
        self.logger.info(f"   - Wake events: {self.wake_events_count}")
        self.logger.info(f"   - Command sessions: {self.command_sessions}")
        
        # Cleanup modules
        if self.vad:
            await self.vad.stop()
            self.logger.info("   ✅ VAD stopped")
        
        if self.wake_word_manager:
            await self.wake_word_manager.stop()
            self.logger.info("   ✅ Wake word detection stopped")
        
        if self.tts:
            await self.tts.stop()
            self.logger.info("   ✅ TTS stopped")
        
        # if self.stt:
        #     await self.stt.stop()
        #     self.logger.info("   ✅ STT stopped")
        
        # if self.commands:
        #     await self.commands.stop()
        #     self.logger.info("   ✅ Commands stopped")
        
        self.logger.info("🧞 Genie Agent shutdown complete")
    
    def get_status(self) -> dict:
        """Get current agent status"""
        return {
            "state": self.state.value,
            "is_running": self.is_running,
            "wake_events": self.wake_events_count,
            "command_sessions": self.command_sessions,
            "modules": {
                "vad": self.vad.is_active() if self.vad else False,
                "tts": self.tts.get_current_engine() if self.tts else None,
                "wake_word": self.wake_word,
                "wake_response": self.wake_response
            }
        }

async def main():
    """Entry point for Genie Agent with environment configuration"""
    # Load environment configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    wake_word = os.getenv('WAKE_WORD', 'Hey Genie')
    wake_response = os.getenv('WAKE_WORD_RESPONSE', 'Yes, Master')
    vad_sensitivity = float(os.getenv('VAD_SENSITIVITY', '0.6'))
    tts_engine = os.getenv('TTS_ENGINE', 'piper')
    tts_voice = os.getenv('TTS_VOICE', 'en_US-lessac-medium')
    
    # Create and start agent
    agent = GenieAgent(
        wake_word=wake_word,
        wake_response=wake_response,
        vad_sensitivity=vad_sensitivity,
        tts_engine=tts_engine,
        tts_voice=tts_voice
    )
    
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())