import os
import re
import logging
from typing import Optional

from mistralai import Mistral

logger = logging.getLogger(__name__)

class LLMTextCleaner:
    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("MISTRAL_API_KEY")
        self.client: Optional[Mistral] = Mistral(api_key=self.api_key) if self.api_key else None
        self.model: str = "mistral-small-latest"

    def _fallback_clean(self, text: str) -> str:
        """Removes Markdown and complex URLs for direct TTS ingestion."""
        text = re.sub(r'[*_#`]', '', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 'un lien web', text)
        return text.strip()

    async def process_for_speech(self, text: str) -> str:
        if not text:
            return ""
            
        # Bypass for short UI confirmations (latency optimization)
        if len(text) < 60:
            return self._fallback_clean(text)
            
        if not self.client:
            logger.warning("MISTRAL_API_KEY missing. Fallback to regex cleaner.")
            return self._fallback_clean(text)

        system_prompt = (
            "Tu es une interface Text-To-Speech (TTS). Ta tâche est de réécrire la réponse "
            "de l'agent pour qu'elle soit fluide, naturelle et RAPIDE à écouter à la voix.\n"
            "Règles strictes :\n"
            "1. CONCISION : Élimine la verbosité. Va droit au but, synthétise les points quand il y en a plusieurs\n"
            "2. CONTEXTE OUTILS :\n"
            "   - Emails : Résume simplement les expéditeurs et le sujet en 2 mots!\n"
            "   - Documents : Résume le contenu de manière digeste. Ne lis pas les chemins de fichiers complexes.\n"
            "   - URLs : Remplace-les toutes par l'expression 'un lien'.\n"
            "3. FORMATAGE ORAL : Remplace les listes à puces par des liaisons naturelles synthétisées ('Premièrement', 'ensuite').\n"
            "4. NETTOYAGE : Aucun formatage Markdown (*, #, _, etc.). Ne justifie pas tes modifications."
        )

        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.2 
            )
            # Récupération de la réponse de Mistral
            llm_text: str = response.choices[0].message.content.strip()
            
            # 🛑 AJOUT : On force le nettoyage Regex sur la sortie du LLM quoiqu'il arrive
            return self._fallback_clean(llm_text)
            
        except Exception as e:
            logger.error("Mistral normalization failed: %s", e)
            return self._fallback_clean(text)