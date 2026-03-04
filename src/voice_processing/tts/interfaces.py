# src/voice_processing/tts/interfaces.py
from typing import Protocol
from pathlib import Path

class TTSProvider(Protocol):
    """
    Contrat strict pour tout moteur de Text-To-Speech.
    Il doit prendre du texte, optionnellement une voix de référence, 
    et retourner le chemin vers le fichier audio généré.
    """
    def synthesize(self, text: str, output_path: Path, reference_voice_path: Path | None = None) -> Path:
        ...