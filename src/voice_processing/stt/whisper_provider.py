# src/voice_processing/stt/whisper_provider.py
import logging
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from .interfaces import TranscriptionResult

# 1. LA MAGIE DU TYPAGE SANS OVERHEAD
if TYPE_CHECKING:
    # Ce bloc n'est lu QUE par ton linter (mypy/pylance).
    # À l'exécution, Python l'ignore totalement : zéro temps de chargement !
    import whisper
    from whisper.model import Whisper

logger = logging.getLogger(__name__)

class WhisperSTT:
    def __init__(self, model_name: str = "base") -> None:
        self.model_name: str = model_name
        # On utilise des guillemets pour le type hint afin d'éviter l'erreur d'import
        self._model: Optional['Whisper'] = None

    def _load_model(self) -> 'Whisper':
        if self._model is None:
            logger.info("Chargement du modèle Whisper '%s' en mémoire...", self.model_name)
            # 2. LE VRAI LAZY IMPORT
            # La librairie massive (PyTorch/Whisper) n'est chargée sur le processeur 
            # que lorsque l'utilisateur parle pour la première fois.
            import whisper
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        if not audio_path.exists():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        model = self._load_model()
        logger.info("Début de la transcription pour le fichier : %s", audio_path.name)
        
        # 3. SILENCE ET OPTIMISATION
        # fp16=False supprime le warning "FP16 is not supported on CPU" sous WSL
        options: Dict[str, Any] = {
            "fp16": False
        }
        
        if language:
            options["language"] = language

        # Whisper renvoie un dictionnaire
        raw_result: Dict[str, Any] = model.transcribe(str(audio_path), **options)
        
        # Mapping : on convertit le dict brut en notre objet standardisé
        return TranscriptionResult(
            text=raw_result.get("text", "").strip(),
            language=raw_result.get("language")
        )