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

    def record_to_temp_file(self, duration_sec: int = 5) -> Path:
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