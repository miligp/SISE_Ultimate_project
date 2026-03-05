import os
import logging
from pathlib import Path
from typing import Optional
from groq import Groq
from .interfaces import STTProvider, TranscriptionResult

logger = logging.getLogger(__name__)

class GroqSTTProvider:
    """
    Implémentation du STT utilisant Groq pour accéder à Whisper Large V3.
    Pattern : Strategy.
    """
    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("GROQ_API_KEY")
        self.client: Optional[Groq] = Groq(api_key=self.api_key) if self.api_key else None

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        if not self.client:
            raise ValueError("Clé API Groq non configurée.")

        logger.info("Envoi de l'audio à Groq...")
        
        with open(audio_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(audio_path.name, file.read()),
                model="whisper-large-v3",
                language=language,
                response_format="json"
            )
            
        return TranscriptionResult(text=transcription.text, language=language)