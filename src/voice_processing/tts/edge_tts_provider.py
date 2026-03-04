# src/voice_processing/tts/edge_tts_provider.py
import logging
import edge_tts
from pathlib import Path

logger = logging.getLogger(__name__)

class EdgeTTSProvider:
    """
    Fournisseur TTS ultra-léger utilisant l'API Microsoft Edge.
    Pas besoin de modèle local, pas besoin de voix de référence.
    """
    def __init__(self, voice: str = "fr-FR-DeniseNeural") -> None:
        """
        Initialise le fournisseur avec une voix par défaut.
        Options populaires : 'fr-FR-DeniseNeural' (Femme), 'fr-FR-HenriNeural' (Homme).
        """
        self.voice: str = voice

    async def synthesize(self, text: str, output_path: Path, reference_voice_path: Path | None = None) -> Path:
        """
        Génère l'audio à partir du texte. 
        Note : reference_voice_path est ignoré ici car nous n'utilisons plus de clonage.
        """
        logger.info("Génération de la voix (Edge-TTS) pour : '%s...'", text[:30])
        
        # Création de l'objet de communication avec Microsoft
        communicate = edge_tts.Communicate(text, self.voice)
        
        # Sauvegarde du flux audio vers le fichier
        await communicate.save(str(output_path))
        
        return output_path