import logging
from pathlib import Path
from typing import Optional, List
from .interfaces import STTProvider, TranscriptionResult

logger = logging.getLogger(__name__)

class TranscriptionManager:
    """
    Orchestrateur STT implémentant un fallback intelligent.
    Pattern : Chain of Responsibility & Circuit Breaker.
    """
    def __init__(self, providers: List[STTProvider]) -> None:
        if not providers:
            raise ValueError("Aucun provider STT fourni.")
        self._active_providers: List[STTProvider] = list(providers)

    def process_audio(self, audio_file_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        errors: List[str] = []
        
        # On itère sur une copie pour pouvoir modifier self._active_providers en toute sécurité
        for provider in list(self._active_providers):
            provider_name = provider.__class__.__name__
            try:
                result = provider.transcribe(audio_file_path, language)
                logger.info("✅ Succès avec %s.", provider_name)
                return result
                
            except Exception as e:
                logger.error("❌ Échec de %s : %s", provider_name, e)
                logger.warning("⚠️ Retrait de %s de la liste des providers actifs.", provider_name)
                
                self._active_providers.remove(provider)
                errors.append(f"{provider_name}: {str(e)}")

        raise RuntimeError(f"Tous les providers STT ont échoué. Erreurs : {errors}")