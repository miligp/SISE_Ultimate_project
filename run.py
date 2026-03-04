# run.py
import os
import logging
from pathlib import Path
from typing import Optional

from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager
from src.voice_processing.stt.interfaces import TranscriptionResult
from src.voice_processing.stt.exporter import AgentPayloadExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main() -> None:
    print("=== INITIALISATION DU SYSTEME VOCAL ===")
    
    # 1. Configuration dynamique du chemin d'export (Le secret d'un code portable)
    # On lit la variable d'environnement. Si elle n'existe pas, on met un dossier par défaut.
    default_dir = str(Path(__file__).parent / "stt_outputs")
    export_path_str: str = os.getenv("AGENT_INPUT_DIR", default_dir)
    
    # On convertit la chaîne en objet Path propre
    shared_agent_folder: Path = Path(export_path_str)
    
    logging.info("Dossier cible pour l'Agent IA : %s", shared_agent_folder.absolute())
    
    # 2. Instanciation des composants
    recorder = MicrophoneRecorder(sample_rate=16000)
    provider = WhisperSTT(model_name="base")
    manager = TranscriptionManager(provider=provider)
    exporter = AgentPayloadExporter(export_dir=shared_agent_folder)
    
    audio_path: Optional[Path] = None

    try:
        input("\n[Action Requise] Appuyez sur ENTRÉE et parlez pendant 5 secondes...")
        audio_path = recorder.record_to_temp_file(duration_sec=5)
        
        logging.info("Analyse de la voix par l'IA en cours...")
        resultat: TranscriptionResult = manager.process_audio(audio_path, language="fr")
        
        print(f"\n🗣️ Vous avez dit : '{resultat.text}'\n")

        # 3. Génération du Payload dans le dossier paramétré
        exporter.export(resultat)

    except Exception as e:
        logging.error("Une erreur inattendue s'est produite : %s", e)
        
    finally:
        if audio_path and audio_path.exists():
            audio_path.unlink()

if __name__ == "__main__":
    main()