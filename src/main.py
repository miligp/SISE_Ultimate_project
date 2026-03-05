# src/main.py
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Chargement de l'environnement (pour les clés API Deepgram/Groq)
from dotenv import load_dotenv

# Imports de l'Agent et des messages
from pydantic_ai.messages import ModelMessage
from src.agent_logic.pydantic_ai_agent import agent 

# Imports Voice Processing (STT) avec le nouveau Fallback Intelligent
from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.deepgram_provider import DeepgramSTTProvider
from src.voice_processing.stt.groq_provider import GroqSTTProvider
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager

# Imports Voice Processing (TTS)
from src.voice_processing.tts.edge_tts_provider import EdgeTTSProvider
from src.voice_processing.tts.synthesis_manager import SynthesisManager
from src.voice_processing.audio_playback import AudioSpeaker

# 1. Résolution du chemin racine et chargement des clés API (.env)
project_root = Path(__file__).parent.parent
load_dotenv(dotenv_path=project_root / ".env")

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def voice_chat_loop() -> None:
    """
    Boucle principale d'interaction vocale en continu.
    Flux : Écoute -> Transcription (Fallback STT) -> Agent -> Synthèse Vocale -> Lecture.
    """
    # 2. Initialisation des composants (Injection de dépendances)
    
    # --- Composants d'Entrée (Micro -> Texte) ---
    recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
    
    # 🌟 Le coeur de la nouvelle architecture STT : La chaîne de priorité
    stt_providers = [
        DeepgramSTTProvider(),            # Priorité 1 : Ultra rapide (API)
        GroqSTTProvider(),                # Priorité 2 : Whisper V3 (API)
        WhisperSTT(model_name="small")    # Priorité 3 : Fallback Local (Offline)
    ]
    # On injecte la liste de providers au lieu d'un seul
    stt_manager = TranscriptionManager(providers=stt_providers)

    # --- Composants de Sortie (Texte -> HP) ---
    tts_provider = EdgeTTSProvider(voice="fr-FR-DeniseNeural")
    tts_manager = SynthesisManager(provider=tts_provider)
    speaker = AudioSpeaker()

    message_history: List[ModelMessage] = []

    print("\n" + "="*50)
    print("   COPILOTE VOCAL INTERACTIF INITIALISÉ")
    print("   Mode : Écoute active avec STT Haute Disponibilité")
    print("   Quitter : Ctrl+C")
    print("="*50)

    while True:
        input_audio_path: Optional[Path] = None
        output_audio_path: Optional[Path] = None

        try:
            # --- PHASE 1 : ÉCOUTE ACTIVE ---
            print("\n🎤 Écoute en cours (parlez maintenant)...")
            input_audio_path = recorder.record_until_silence()
            
            # --- PHASE 2 : SPEECH-TO-TEXT (Intelligent) ---
            # Le manager va tester Deepgram, puis Groq, puis Whisper de manière transparente
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