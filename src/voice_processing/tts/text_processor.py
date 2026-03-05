# src/voice_processing/tts/text_processor.py
import os
import logging
from typing import Optional

# Import du SDK officiel
from mistralai import Mistral

logger = logging.getLogger(__name__)

class LLMTextCleaner:
    """
    Service de normalisation de texte utilisant l'API Mistral.
    Transforme le texte brut/markdown de l'agent en un script naturel prêt à être lu (TTS).
    """
    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("MISTRAL_API_KEY")
        
        # Instanciation du client Mistral si la clé est trouvée
        self.client: Optional[Mistral] = Mistral(api_key=self.api_key) if self.api_key else None
        
        # mistral-small-latest est parfait pour cette tâche rapide de réécriture
        self.model: str = "mistral-small-latest"

    async def process_for_speech(self, text: str) -> str:
        """
        Interroge l'API Mistral pour convertir le texte de l'agent en un script oral structuré.
        """
        if not text:
            return ""
            
        if not self.client:
            logger.warning("⚠️ Clé MISTRAL_API_KEY absente. Fallback d'urgence sans LLM.")
            return text.replace("*", "").replace("#", "")

        # 🧠 Prompt Engineering Avancé : Traduction Visuel -> Oral
        system_prompt = (
            "Tu es un expert en communication orale et Text-To-Speech. "
            "Ta mission est de résumer et d'adapter le texte de l'utilisateur pour qu'il soit lu à voix haute. "
            "1. CONCISION : Sois direct et va à l'essentiel. Fais des phrases courtes. "
            "2. STRUCTURE ORALE : Si le texte d'origine contient des listes ou des idées complexes, "
            "organise-les logiquement avec des mots de liaison clairs (ex: 'Premièrement', 'Ensuite', 'Pour résumer') "
            "au lieu d'utiliser des énumérations hachées. "
            "3. NETTOYAGE : Ne génère AUCUN symbole Markdown ou ponctuation anormale. "
            "RÈGLE ABSOLUE : Commence obligatoirement ta réponse par la phrase exacte : 'ça va aller vite'."
        )

        try:
            logger.info("🔄 Normalisation LLM (Structure orale) via Mistral Small...")
            
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                # On enlève max_tokens pour éviter les phrases coupées.
                # On garde une température basse (0.3) pour que le LLM reste très factuel et structuré.
                temperature=0.3
            )
            
            clean_text: str = response.choices[0].message.content.strip()
            return clean_text
            
        except Exception as e:
            logger.error("❌ Échec de la normalisation Mistral : %s", e)
            return text.replace("*", "").replace("#", "")