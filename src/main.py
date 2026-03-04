import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from pydantic_ai.messages import ModelMessage
from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager
from src.agent_logic.pydantic_ai_agent import agent 

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def voice_chat_loop() -> None:
    message_history: List[ModelMessage] = []
    recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
    provider = WhisperSTT(model_name="base")
    manager = TranscriptionManager(provider=provider)

    print("\n" + "="*50)
    print("  COPILOTE VOCAL INITIALISÉ")
    print("  Appuyez sur Ctrl+C pour quitter")
    print("="*50)

    while True:
        audio_path: Optional[Path] = None
        try:
            print("\n🎤 Écoute en cours...")
            audio_path = recorder.record_until_silence()
            
            transcription_result = manager.process_audio(audio_path, language="fr")
            query: str = transcription_result.text.strip()
            
            if not query or len(query) < 2:
                continue
                
            print(f"🗣️  Vous : {query}")
            
            print("🤖 Réflexion...")
            result = await agent.run(query, message_history=message_history)
            
            message_history.extend(result.new_messages())
            
            print(f"\n<<< {result.output}")
            
            # Pause bloquante avant de relancer l'écoute
            input("\n[Appuyez sur 'Entrée' pour continuer...]")

        except KeyboardInterrupt:
            print("\n\nArrêt du copilote. Au revoir !")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Erreur dans la boucle : {e}")
        finally:
            if audio_path and audio_path.exists():
                audio_path.unlink()

if __name__ == "__main__":
    try:
        asyncio.run(voice_chat_loop())
    except KeyboardInterrupt:
        pass