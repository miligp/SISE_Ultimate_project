import asyncio
import logging
from pathlib import Path
from typing import Optional

from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager
from src.agent_logic.pydantic_ai_agent import run_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_voice_command(duration_sec: int = 5) -> None:
    recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
    audio_path: Optional[Path] = None
    
    try:
        audio_path = recorder.record_to_temp_file(duration_sec=duration_sec)
        
        provider = WhisperSTT(model_name="base")
        manager = TranscriptionManager(provider=provider)
        
        transcription_result = manager.process_audio(audio_path, language="fr")
        query: str = transcription_result.text.strip()
        
        if not query:
            logger.warning("No command detected.")
            return
            
        logger.info("Command recognized: %s", query)
        
        response: str = await run_query(query)
        logger.info("Agent response: %s", response)
        
    except Exception as e:
        logger.error("Error processing voice command: %s", e)
    finally:
        if audio_path and audio_path.exists():
            try:
                audio_path.unlink()
            except OSError as cleanup_error:
                logger.error("Failed to delete temporary file: %s", cleanup_error)

if __name__ == "__main__":
    asyncio.run(process_voice_command())