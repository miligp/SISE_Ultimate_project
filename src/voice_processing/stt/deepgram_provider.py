# src/voice_processing/stt/deepgram_provider.py
import os
import httpx
import logging
from pathlib import Path
from typing import Optional
from .interfaces import STTProvider, TranscriptionResult

logger = logging.getLogger(__name__)

class DeepgramSTTProvider:
    """
    Implémentation STT via l'API REST de Deepgram (sans SDK pour éviter les bugs d'import).
    Intègre une sécurité FinOps pour bloquer les boucles infinies.
    """
    def __init__(self, max_requests_per_session: int = 100) -> None:
        self.api_key: Optional[str] = os.getenv("DEEPGRAM_API_KEY")
        self.url: str = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
        
        # --- Variables de sécurité FinOps ---
        self.max_requests = max_requests_per_session
        self.request_count = 0

    def transcribe(self, audio_path: Path, language: Optional[str] = "fr") -> TranscriptionResult:
        if not self.api_key:
            raise ValueError("Clé API Deepgram non configurée.")
            
        # 🚨 VÉRIFICATION DU QUOTA LOCAL
        if self.request_count >= self.max_requests:
            raise PermissionError(f"Sécurité FinOps : Quota de {self.max_requests} requêtes atteint. Coupure de Deepgram.")

        if not audio_path.exists():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }

        # Concaténation des paramètres d'URL
        request_url = f"{self.url}&language={language}" if language else self.url

        logger.info(f"⚡ Deepgram STT API REST (Requête {self.request_count + 1}/{self.max_requests})...")
        
        # Le bloc 'with' gère proprement l'ouverture et la fermeture du fichier audio
        with open(audio_path, "rb") as f:
            response = httpx.post(request_url, headers=headers, content=f.read(), timeout=15.0)
            
        # Lève une exception si l'API renvoie une erreur (401, 400, etc.)
        response.raise_for_status()
        
        # Succès de la requête
        self.request_count += 1
        data = response.json()
        
        # Navigation sécurisée dans le JSON renvoyé par Deepgram
        try:
            transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        except (KeyError, IndexError):
            transcript = ""
            logger.warning("Deepgram n'a détecté aucune parole dans l'audio.")
        
        return TranscriptionResult(text=transcript, language=language)