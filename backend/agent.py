"""
Genie Whisper X - Main Agent Event Loop
Agent orchestrates the voice processing pipeline: voice in → action out
"""
import asyncio
import logging
from typing import Optional

# Module imports (stubs for now)
from vad import VoiceActivityDetector
from whisper import WhisperSTT
from tts import TextToSpeech
from commands import CommandEngine

class GenieAgent:
    """Main agent orchestrating voice processing pipeline"""
    
    def __init__(self):
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
        # Initialize modules (stubs)
        self.vad: Optional[VoiceActivityDetector] = None
        self.stt: Optional[WhisperSTT] = None
        self.tts: Optional[TextToSpeech] = None
        self.commands: Optional[CommandEngine] = None
        
        self.logger.info("Genie Agent initialized")
    
    async def initialize(self):
        """Initialize all agent modules"""
        try:
            self.logger.info("Initializing agent modules...")
            
            # Initialize modules (placeholder)
            # self.vad = VoiceActivityDetector()
            # self.stt = WhisperSTT()
            # self.tts = TextToSpeech()
            # self.commands = CommandEngine()
            
            self.logger.info("Agent modules initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            return False
    
    async def start(self):
        """Start the main agent event loop"""
        if not await self.initialize():
            return
            
        self.is_running = True
        self.logger.info("Genie Agent started - listening for wake word...")
        
        try:
            while self.is_running:
                # Main event loop (placeholder)
                await asyncio.sleep(0.1)
                
                # TODO: Implement pipeline:
                # 1. Listen for wake word
                # 2. Capture voice input
                # 3. Process with STT
                # 4. Parse commands
                # 5. Execute actions
                # 6. Provide TTS feedback
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Clean shutdown of agent"""
        self.is_running = False
        self.logger.info("Genie Agent shutting down...")
        
        # Cleanup modules
        # if self.vad:
        #     await self.vad.stop()
        # if self.stt:
        #     await self.stt.stop()
        # if self.tts:
        #     await self.tts.stop()
        
        self.logger.info("Genie Agent shutdown complete")

async def main():
    """Entry point for Genie Agent"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    agent = GenieAgent()
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())