import asyncio
import logging
import sounddevice as sd
from pathlib import Path
from src.voice_processing.audio_capture import MicrophoneRecorder

logging.basicConfig(level=logging.INFO)

async def test_recording_method():
    recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
    
    print("\n" + "="*40)
    print("TEST DE DÉTECTION VOCALE")
    print("Parlez, puis restez silencieux pour arrêter.")
    print("="*40)

    try:
        # Utilisation de la nouvelle méthode développée
        audio_path = recorder.record_until_silence()
        
        print(f"\n✅ Enregistrement terminé : {audio_path}")
        
        # Test de lecture pour vérifier si le début ou la fin n'est pas coupé
        import soundfile as sf
        data, fs = sf.read(audio_path)
        print("🔈 Lecture du résultat...")
        sd.play(data, fs)
        sd.wait()
        
        # Nettoyage
        audio_path.unlink()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    asyncio.run(test_recording_method())