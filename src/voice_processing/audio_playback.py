# src/voice_processing/audio_playback.py
import logging
import sounddevice as sd
import soundfile as sf
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioSpeaker:
    """
    Classe responsable de la diffusion d'un fichier audio 
    via les haut-parleurs du système (Encapsulation matérielle).
    """
    def play_file(self, audio_path: Path) -> None:
        """Lit un fichier audio de manière synchrone (bloque jusqu'à la fin de la lecture)."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Impossible de lire le fichier, chemin introuvable : {audio_path}")

        logger.info("🔊 Lecture audio en cours : %s", audio_path.name)
        # On extrait les données et le sample rate du fichier généré par l'IA
        data, fs = sf.read(str(audio_path))
        
        # Diffusion matérielle
        sd.play(data, fs)
        sd.wait() # On attend que la phrase soit finie avant de rendre la main
        logger.info("🔈 Lecture terminée.")