# src/main.py
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_ai.messages import ModelMessage

# Imports de l'architecture SOLID
from src.agent_logic.pydantic_ai_agent import agent 
from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.deepgram_provider import DeepgramSTTProvider
from src.voice_processing.stt.groq_provider import GroqSTTProvider
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager
from src.voice_processing.tts.edge_tts_provider import EdgeTTSProvider
from src.voice_processing.tts.synthesis_manager import SynthesisManager
from src.voice_processing.audio_playback import AudioSpeaker

project_root = Path(__file__).parent.parent
load_dotenv(dotenv_path=project_root / ".env")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def voice_chat_loop() -> None:
    # 1. Initialisation des composants
    recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
    
    stt_providers = [
        DeepgramSTTProvider(),
        GroqSTTProvider(),
        WhisperSTT(model_name="small")
    ]
    stt_manager = TranscriptionManager(providers=stt_providers)
    
    tts_provider = EdgeTTSProvider(voice="fr-FR-DeniseNeural")
    tts_manager = SynthesisManager(provider=tts_provider)
    speaker = AudioSpeaker()

    message_history: List[ModelMessage] = []

    print("\n" + "═"*50)
    print(" 🎙️  COPILOTE VOCAL - MODE VAD (Voice Activity Detection)")
    print(" 💡  Parlez naturellement. L'IA répondra après un silence.")
    print(" 🚪  Appuyez sur Ctrl+C pour quitter le programme.")
    print("═"*50)

    while True:
        input_audio_path: Optional[Path] = None
        output_audio_path: Optional[Path] = None

        try:
            # --- PHASE 1 : ÉCOUTE ACTIVE (Gérée par ton script VAD) ---
            # asyncio.to_thread permet de ne pas bloquer l'Event Loop asynchrone 
            # pendant que le micro tourne dans sa boucle while True synchrone.
            input_audio_path = await asyncio.to_thread(recorder.record_until_silence)
            
            # --- PHASE 2 : TRANSCRIPTION STT ---
            print("⏳ [TRAITEMENT] Transcription en cours...")
            transcription_result = stt_manager.process_audio(input_audio_path, language="fr")
            query: str = transcription_result.text.strip()
            
            if not query or len(query) < 2:
                print("🟡 [INFO] Aucun mot distinct capté (bruit de fond ignoré).")
                continue
                
            print(f"👤 Vous : {query}")

            # --- PHASE 3 : RÉFLEXION IA ---
            print("🧠 [RÉFLEXION] L'agent analyse votre demande...")
            result = await agent.run(query, message_history=message_history)
            
            message_history.extend(result.new_messages())
            agent_response = result.output
            print(f"🤖 Agent : {agent_response}")

            # --- PHASE 4 : SYNTHÈSE VOCALE TTS ---
            print("🔊 [PAROLE] Génération de la réponse...")
            output_audio_path = await tts_manager.process_text_to_audio_file(agent_response)
            
            # Lecture bloquante pour que le micro ne se déclenche pas sur la voix de l'IA
            speaker.play_file(output_audio_path)

        except KeyboardInterrupt:
            print("\n\n🛑 [SYSTÈME] Arrêt manuel sollicité via Ctrl+C. Extinction...")
            break
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            print("🔴 [ERREUR] Le système a rencontré un problème. Reprise du cycle...")
        finally:
            # --- NETTOYAGE ---
            if input_audio_path and input_audio_path.exists():
                input_audio_path.unlink()
            if output_audio_path and output_audio_path.exists():
                output_audio_path.unlink()

    print("\n👋 Programme terminé avec succès.")
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(voice_chat_loop())
    except KeyboardInterrupt:
        pass