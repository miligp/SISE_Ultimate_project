# src/voice_processing/stt/transcription_manager.py
from pathlib import Path
from typing import Optional
from .interfaces import STTProvider, TranscriptionResult

class TranscriptionManager:
    def __init__(self, provider: STTProvider) -> None:
        self.provider: STTProvider = provider

    def process_audio(self, audio_file_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        # Le manager se contente de déléguer et de renvoyer l'objet typé
        return self.provider.transcribe(audio_file_path, language)