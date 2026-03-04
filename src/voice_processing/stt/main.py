# main.py
import logging
from pathlib import Path
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager

logging.basicConfig(level=logging.INFO)

def main() -> None:
    # 1. Résolution propre du chemin (basée sur l'image de ton arborescence)
    base_dir: Path = Path(__file__).parent
    audio_file: Path = base_dir / "src" / "voice_processing" / "professor_voice.mp3"

    # 2. Instanciation du fournisseur (la technologie concrète)
    whisper_provider = WhisperSTT(model_name="small") # "base", "small", "medium", etc.

    # 3. Injection du fournisseur dans le manager (le métier)
    manager = TranscriptionManager(provider=whisper_provider)

    # 4. Exécution
    try:
        transcript: str = manager.process_audio(audio_file)
        print("\n--- RÉSULTAT DE LA TRANSCRIPTION ---")
        print(transcript)
    except Exception as e:
        logging.error("Une erreur est survenue : %s", e)

if __name__ == "__main__":
    main()