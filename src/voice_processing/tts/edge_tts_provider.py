# src/voice_processing/tts/edge_tts_provider.py
import logging
import edge_tts
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class EdgeTTSProvider:
    """
    Fournisseur TTS ultra-léger utilisant l'API Microsoft Edge.
    Intègre le contrôle dynamique du débit (rate) pour une diction plus humaine.
    """
    def __init__(self, voice: str = "fr-FR-DeniseNeural", rate: str = "+15%") -> None:
        """
        Initialise le fournisseur.
        
        Args:
            voice: L'identifiant de la voix Microsoft (ex: 'fr-FR-DeniseNeural').
            rate: Ajustement de la vitesse sous forme de pourcentage (ex: '+20%', '-10%', '+0%').
        """
        self.voice: str = voice
        self.rate: str = rate

    async def synthesize(self, text: str, output_path: Path, reference_voice_path: Optional[Path] = None) -> Path:
        """
        Génère l'audio à partir du texte avec le débit configuré. 
        """
        logger.info("🔊 Génération vocale (Vitesse: %s) pour : '%s...'", self.rate, text[:30])
        
        # Injection du paramètre 'rate' directement dans la communication avec l'API
        communicate = edge_tts.Communicate(
            text=text, 
            voice=self.voice, 
            rate=self.rate
        )
        
        await communicate.save(str(output_path))
        
        return output_path