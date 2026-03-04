# src/voice_processing/stt/interfaces.py
from typing import Protocol, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TranscriptionResult:
    """
    Objet de transfert de données (DTO) standardisant la sortie de n'importe quel modèle STT.
    Cela évite de se reposer sur de simples dictionnaires non structurés.
    """
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    # On pourrait ajouter plus tard : segments: List[Dict[str, Any]] = field(default_factory=list)

class STTProvider(Protocol):
    """
    Interface définissant le contrat strict pour tout fournisseur de Speech-to-Text.
    """
    # On ajoute des paramètres optionnels fréquents en IA (ex: forcer la langue)
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        ...