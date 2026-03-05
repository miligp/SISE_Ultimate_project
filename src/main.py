# src/main.py
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Imports de l'Agent et des messages
from pydantic_ai.messages import ModelMessage
from src.agent_logic.pydantic_ai_agent import agent 

# Imports Voice Processing (STT)
from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager

# Imports Voice Processing (TTS)
from src.voice_processing.tts.edge_tts_provider import EdgeTTSProvider
from src.voice_processing.tts.synthesis_manager import SynthesisManager
from src.voice_processing.audio_playback import AudioSpeaker

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def voice_chat_loop() -> None:
    """
    Boucle principale d'interaction vocale en continu.
    Flux : Écoute -> Transcription -> Agent -> Synthèse Vocale -> Lecture.
    """
    # 1. Initialisation des composants (Injection de dépendances)
    # --- Composants d'Entrée (Micro -> Texte) ---
    recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
    stt_provider = WhisperSTT(model_name="small")
    stt_manager = TranscriptionManager(provider=stt_provider)

    # --- Composants de Sortie (Texte -> HP) ---
    tts_provider = EdgeTTSProvider(voice="fr-FR-DeniseNeural")
    tts_manager = SynthesisManager(provider=tts_provider)
    speaker = AudioSpeaker()

    message_history: List[ModelMessage] = []

    print("\n" + "="*50)
    print("   COPILOTE VOCAL INTERACTIF INITIALISÉ")
    print("   Mode : Écoute active (détection de silence)")
    print("   Quitter : Ctrl+C")
    print("="*50)

    while True:
        input_audio_path: Optional[Path] = None
        output_audio_path: Optional[Path] = None

        try:
            # --- PHASE 1 : ÉCOUTE ACTIVE ---
            print("\n🎤 Écoute en cours (parlez maintenant)...")
            # Cette méthode doit gérer la détection de silence en interne
            input_audio_path = recorder.record_until_silence()
            
            # --- PHASE 2 : SPEECH-TO-TEXT ---
            transcription_result = stt_manager.process_audio(input_audio_path, language="fr")
            query: str = transcription_result.text.strip()
            
            # Filtrage des bruits de fond ou entrées trop courtes
            if not query or len(query) < 2:
                continue
                
            print(f"👤 Vous : {query}")
            
            # --- PHASE 3 : RÉFLEXION DE L'AGENT ---
            print("🤖 Réflexion de l'agent...")
            result = await agent.run(query, message_history=message_history)
            
            # Mise à jour de la mémoire de l'agent
            message_history.extend(result.new_messages())
            agent_response = result.output
            print(f"🤖 Agent : {agent_response}")

            # --- PHASE 4 : TEXT-TO-SPEECH (Rendre compte) ---
            print("🔊 Synthèse vocale...")
            output_audio_path = await tts_manager.process_text_to_audio_file(agent_response)
            
            # --- PHASE 5 : DIFFUSION AUDIO ---
            # Lecture bloquante pour que l'agent finisse de parler avant de réécouter
            speaker.play_file(output_audio_path)

        except KeyboardInterrupt:
            print("\n\nArrêt du copilote sollicité. Nettoyage et fermeture...")
            break
        except Exception as e:
            logger.error(f"Erreur critique dans la boucle vocale : {e}")
        finally:
            # --- NETTOYAGE RIGOUREUX DES RESSOURCES ---
            if input_audio_path and input_audio_path.exists():
                input_audio_path.unlink()
            if output_audio_path and output_audio_path.exists():
                output_audio_path.unlink()

    print("Au revoir !")
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(voice_chat_loop())
    except KeyboardInterrupt:
        pass