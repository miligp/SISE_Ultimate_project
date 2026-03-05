# src/voice_processing/tts/synthesis_manager.py
import tempfile
import logging
from pathlib import Path

from .interfaces import TTSProvider
# Import de la nouvelle classe
from .text_processor import LLMTextCleaner 

logger = logging.getLogger(__name__)

class SynthesisManager:
    """
    Chef d'orchestre du TTS : coordonne le nettoyage LLM et la synthèse vocale.
    """
    def __init__(self, provider: TTSProvider, reference_voice: Path | None = None) -> None:
        self.provider: TTSProvider = provider
        self.reference_voice: Path | None = reference_voice
        
        # Composition : Le Manager possède son propre nettoyeur
        self.cleaner: LLMTextCleaner = LLMTextCleaner()

    async def process_text_to_audio_file(self, text: str) -> Path:
        # --- ÉTAPE DE NETTOYAGE (Asynchrone via Mistral) ---
        clean_text = await self.cleaner.process_for_speech(text)
        
        if not clean_text:
            raise ValueError("Le texte est vide après le nettoyage LLM.")

        logger.debug("Texte final envoyé au moteur vocal : %s", clean_text)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = Path(temp_file.name)
        temp_file.close()

        # --- ÉTAPE DE SYNTHÈSE (Edge TTS) ---
        await self.provider.synthesize(
            text=clean_text, 
            output_path=output_path, 
            reference_voice_path=self.reference_voice
        )
        
        return output_path