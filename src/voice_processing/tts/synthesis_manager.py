# src/voice_processing/tts/synthesis_manager.py
import tempfile
import logging
from pathlib import Path
from .interfaces import TTSProvider
from .text_processor import TextCleaner # <-- Import du nouveau module

logger = logging.getLogger(__name__)

class SynthesisManager:
    def __init__(self, provider: TTSProvider, reference_voice: Path | None = None) -> None:
        self.provider: TTSProvider = provider
        self.reference_voice: Path | None = reference_voice

    async def process_text_to_audio_file(self, text: str) -> Path:
        # --- ÉTAPE DE NETTOYAGE ---
        # On nettoie le Markdown avant de l'envoyer au provider
        clean_text = TextCleaner.clean_for_speech(text)
        
        if not clean_text:
            raise ValueError("Le texte est vide après nettoyage.")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = Path(temp_file.name)
        temp_file.close()

        await self.provider.synthesize(
            text=clean_text, 
            output_path=output_path, 
            reference_voice_path=self.reference_voice
        )
        
        return output_path