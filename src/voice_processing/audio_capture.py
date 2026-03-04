# src/voice_processing/audio_capture.py
import logging
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path

logger = logging.getLogger(__name__)

class MicrophoneRecorder:
    """
    Classe responsable de la capture du flux audio du microphone.
    Elle encapsule la complexité matérielle (sounddevice).
    """
    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate: int = sample_rate
        self.channels: int = channels
        
        # --- Paramètres VAD (Voice Activity Detection) ---
        # Si la barre visuelle montre un bruit de fond à 0.005, mettez le threshold à 0.015
        self.threshold: float = 0.025
        self.silence_duration: float = 1  # Secondes de silence avant coupure

    def record_to_temp_file(self, duration_sec: int = 5) -> Path:
        """Enregistrement à durée fixe (Legacy)."""
        logger.info("🎤 Enregistrement en cours pour %d secondes...", duration_sec)
        
        recording: np.ndarray = sd.rec(
            int(duration_sec * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32'
        )
        sd.wait() 
        logger.info("✅ Enregistrement terminé.")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = Path(temp_file.name)
        sf.write(file=str(temp_path), data=recording, samplerate=self.sample_rate)
        
        return temp_path

    def record_until_silence(self) -> Path:
        """Enregistre dynamiquement jusqu'à détection d'un silence prolongé."""
        logger.info("🎤 Écoute active... Parlez maintenant.")
        print("\n--- Calibration VAD ---")
        
        recording = []
        pre_buffer = []  # Pour ne pas couper le tout premier son
        silent_chunks = 0
        chunk_size = int(self.sample_rate * 0.1)  # Blocs de 100ms
        has_started = False
        
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='float32') as stream:
            while True:
                data, overflowed = stream.read(chunk_size)
                
                # Calcul du volume RMS
                volume = float(np.sqrt(np.mean(data**2)))
                
                # Affichage de la jauge visuelle pour régler le threshold
                bar_length = min(int(volume * 1000), 40)
                bar = "█" * bar_length
                status = "🗣️ ENREGISTREMENT" if has_started else "⏳ ATTENTE"
                print(f"\rVol: {volume:.4f} |{bar:<40}| (Seuil: {self.threshold}) [{status}]", end="", flush=True)

                if not has_started:
                    # On stocke en permanence les 5 derniers blocs (0.5s) au cas où on parle soudainement
                    pre_buffer.append(data)
                    if len(pre_buffer) > 5:
                        pre_buffer.pop(0)

                    # Détection du début de parole
                    if volume >= self.threshold:
                        has_started = True
                        recording.extend(pre_buffer)  # On garde le buffer précédant le mot
                else:
                    recording.append(data)
                    
                    # Détection du silence
                    if volume < self.threshold:
                        silent_chunks += 1
                    else:
                        silent_chunks = 0  # Réinitialise si on reparle
                    
                    # Arrêt si le silence dure plus longtemps que la limite
                    if silent_chunks > (self.silence_duration / 0.1):
                        print()  # Nouvelle ligne propre après la jauge
                        break

        logger.info("✅ Silence détecté, fin de l'enregistrement.")
        full_audio = np.concatenate(recording, axis=0)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = Path(temp_file.name)
        sf.write(file=str(temp_path), data=full_audio, samplerate=self.sample_rate)
        
        return temp_path