# src/voice_processing/tts/text_processor.py
import re
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    """
    Classe utilitaire pour nettoyer le texte avant la synthèse vocale.
    Supprime les artefacts Markdown et normalise la ponctuation.
    """
    @staticmethod
    def clean_for_speech(text: str) -> str:
        """
        Transforme un texte Markdown en texte brut lisible par une IA vocale.
        """
        if not text:
            return ""

        # 1. Supprimer les blocs de code (```code```)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # 2. Supprimer le gras et l'italique (**text**, __text__, *text*, _text_)
        text = re.sub(r'\*\*|__|\*|_', '', text)
        
        # 3. Supprimer les titres (### Titre)
        text = re.sub(r'#+\s+', '', text)
        
        # 4. Gérer les liens Markdown [texte](url) -> on ne garde que le texte
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        
        # 5. Supprimer les listes à puces ( - ou * en début de ligne)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # 6. Nettoyage des espaces doubles et sauts de ligne excessifs
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text