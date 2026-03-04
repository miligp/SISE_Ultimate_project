# src/voice_processing/stt/whisper_provider.py
import logging
import whisper
from whisper.model import Whisper
from pathlib import Path
from typing import Optional, Dict, Any
from .interfaces import TranscriptionResult

logger = logging.getLogger(__name__)

class WhisperSTT:
    def __init__(self, model_name: str = "base") -> None:
        self.model_name: str = model_name
        self._model: Optional[Whisper] = None

    def _load_model(self) -> whisper.Whisper:
        if self._model is None:
            logger.info("Chargement du modèle Whisper '%s' en mémoire...", self.model_name)
            self._model = whisper.load_model(self.model_name)
        return self._model

    # On respecte la nouvelle signature de l'interface !
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        if not audio_path.exists():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        model = self._load_model()
        logger.info("Début de la transcription pour le fichier : %s", audio_path.name)
        
        options: Dict[str, Any] = {}
        if language:
            options["language"] = language

        # Whisper renvoie un dictionnaire
        raw_result: Dict[str, Any] = model.transcribe(str(audio_path), **options)
        
        # Mapping : on convertit le dict brut en notre objet standardisé
        return TranscriptionResult(
            text=raw_result.get("text", "").strip(),
            language=raw_result.get("language")
        )