# src/voice_processing/tts/synthesis_manager.py
import tempfile
import logging
from pathlib import Path
from .interfaces import TTSProvider

logger = logging.getLogger(__name__)

class SynthesisManager:
    """
    Orchestrateur qui gère la génération de fichiers audio temporaires.
    """
    def __init__(self, provider: TTSProvider, reference_voice: Path | None = None) -> None:
        # reference_voice est maintenant optionnel (None par défaut)
        self.provider: TTSProvider = provider
        self.reference_voice: Path | None = reference_voice

    async def process_text_to_audio_file(self, text: str) -> Path:
        if not text.strip():
            raise ValueError("Le texte à synthétiser est vide.")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = Path(temp_file.name)
        temp_file.close()

        # On appelle le provider (le await est nécessaire pour edge-tts qui est asynchrone)
        await self.provider.synthesize(
            text=text, 
            output_path=output_path, 
            reference_voice_path=self.reference_voice
        )
        
        return output_path