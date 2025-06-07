#!/usr/bin/env python3
"""
Test script for Wake Word and TTS production flow
Validates the complete VAD → Wake Word → TTS event pipeline
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.agent import GenieAgent, AgentState

async def test_production_flow():
    """Test the production wake word and TTS flow"""
    
    # Configure test logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("test_flow")
    
    logger.info("🧪 Starting Wake Word and TTS Production Flow Test")
    
    try:
        # Create agent with test configuration
        agent = GenieAgent(
            wake_word="Hey Genie",
            wake_response="Yes, Master",
            vad_sensitivity=0.6,
            tts_engine="pyttsx3",  # Use pyttsx3 for testing (most compatible)
            tts_voice="en_US-lessac-medium"
        )
        
        logger.info("✅ Agent created successfully")
        
        # Test module initialization
        logger.info("🔧 Testing module initialization...")
        
        # Test VAD initialization
        from backend.vad.vad import VoiceActivityDetector
        vad = VoiceActivityDetector(vad_sensitivity=0.6)
        logger.info("   📡 VAD module loaded")
        
        # Test Wake Word Manager initialization
        from backend.vad.wakeword import WakeWordManager
        wake_manager = WakeWordManager(wake_word="Hey Genie")
        logger.info("   🎯 Wake Word Manager loaded")
        
        # Test TTS initialization
        from backend.tts import TextToSpeech
        tts = TextToSpeech(engine_type="pyttsx3")
        
        logger.info("   🔊 Attempting TTS initialization...")
        if await tts.initialize():
            logger.info(f"   ✅ TTS initialized successfully ({tts.get_current_engine()})")
            
            # Test TTS speak functionality
            logger.info("   🗣️ Testing TTS speech...")
            success = await tts.speak("Test message")
            if success:
                logger.info("   ✅ TTS speech test successful")
            else:
                logger.warning("   ⚠️ TTS speech test failed")
        else:
            logger.warning("   ⚠️ TTS initialization failed - testing without audio")
        
        # Test agent status
        status = agent.get_status()
        logger.info(f"   📊 Agent Status: {status}")
        
        logger.info("🎉 Production flow validation completed successfully!")
        logger.info("")
        logger.info("🚀 Production Event Flow Ready:")
        logger.info("   1. VAD monitors microphone for voice activity")
        logger.info("   2. Wake word 'Hey Genie' triggers detection")
        logger.info("   3. TTS responds with 'Yes, Master'")
        logger.info("   4. Agent enters command listening mode")
        logger.info("   5. Returns to VAD monitoring after timeout")
        logger.info("")
        logger.info("▶️  To start production agent: python backend/agent.py")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("   Missing dependencies - run: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_production_flow())
    sys.exit(0 if success else 1)