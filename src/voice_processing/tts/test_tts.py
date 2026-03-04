# src/voice_processing/tts/test_tts.py
import logging
import asyncio
from pathlib import Path
from src.voice_processing.tts.edge_tts_provider import EdgeTTSProvider
from src.voice_processing.tts.synthesis_manager import SynthesisManager
from src.voice_processing.audio_playback import AudioSpeaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def test_vocal() -> None:
    print("=== TEST TTS LÉGER (EDGE-TTS) ===")
    
    # 1. On instancie sans voix de référence (None)
    provider = EdgeTTSProvider(voice="fr-FR-DeniseNeural")
    manager = SynthesisManager(provider=provider, reference_voice=None)
    speaker = AudioSpeaker()
    
    texte = "Je suis quelqu'un qui aime les crocs, mais pas n'importe lesquelles"
    audio_path: Path | None = None

    try:
        # 2. Génération
        audio_path = await manager.process_text_to_audio_file(text=texte)
        
        # 3. Lecture
        speaker.play_file(audio_path)
        
    finally:
        if audio_path and audio_path.exists():
            audio_path.unlink()
            logging.info("Nettoyage effectué.")

if __name__ == "__main__":
    asyncio.run(test_vocal())