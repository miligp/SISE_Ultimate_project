"""
Agent pydantic-ai utilisant email_utils.py pour la recherche, la lecture et l'envoi d'emails.
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
from pydantic_ai import Agent

from src.agent_logic.email_utils import search_emails, send_email

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "mistral:mistral-large-latest")

def get_system_prompt() -> str:
    """Génère le prompt système en y injectant la date actuelle pour le formatage IMAP."""
    current_date = datetime.now().strftime("%d-%b-%Y")
    return (
        "Tu es un assistant personnel intelligent. Les inputs que tu reçois sont issus d'une transcription de la voix de l'utilisateur, il peut y avoir des imprécisions."
        "Tu as accès à des fonctions pour rechercher, lire et envoyer des emails. "
        "Réponds toujours en français sauf si l'utilisateur parle une autre langue. "
        "Sois concis et précis. "
        f"La date actuelle est {current_date} (format IMAP). Utilise ce format exact pour le paramètre 'since_date' si nécessaire. "
        "RÈGLE CRITIQUE : Ne déclenche JAMAIS l'outil `send_email` de ta propre initiative. "
        "Tu dois d'abord présenter le brouillon (destinataire, objet, corps) à l'utilisateur, "
        "puis attendre sa confirmation explicite avant d'exécuter l'outil."
    )

agent = Agent(
    model=LLM_MODEL,
    system_prompt=get_system_prompt(),
)

@agent.tool_plain
def fetch_emails_tool(
    sender: Optional[str] = None, 
    subject: Optional[str] = None, 
    since_date: Optional[str] = None, 
    count: int = 5
) -> list[dict[str, str]]:
    """
    Recherche et récupère des emails selon des critères stricts.
    - sender: adresse email ou nom partiel de l'expéditeur.
    - subject: mot-clé dans l'objet de l'email.
    - since_date: date de début au format 'DD-Mon-YYYY'. À utiliser UNIQUEMENT si l'utilisateur précise une notion de temps ("depuis hier", "ce matin"). Ne pas utiliser pour "le dernier email".
    - count: nombre maximum d'emails à récupérer (défaut: 5).
    """
    return search_emails(sender, subject, since_date, count)

@agent.tool_plain
def dispatch_email(to_address: str, subject: str, body: str) -> str:
    """Envoie un email après validation explicite de l'utilisateur."""
    return send_email(to_address, subject, body)

async def run_query(query: str) -> str:
    """Exécute une requête textuelle via l'agent et retourne la réponse."""
    result = await agent.run(query)
    return result.output

async def stream_query(query: str) -> AsyncGenerator[str, None]:
    """Exécute une requête en mode streaming et yield les tokens."""
    async with agent.run_stream(query) as streamed:
        async for chunk in streamed.stream_text(delta=True):
            yield chunk

if __name__ == "__main__":
    TEST_QUERIES = [
        "Est-ce que j'ai reçu un mail de Laurent depuis hier ?"
    ]

    async def main():
        print(f"Agent connecté au modèle : {LLM_MODEL}\n")
        print("=" * 60)

        for query in TEST_QUERIES:
            print(f"\n>>> {query}")
            try:
                response = await run_query(query)
                print(f"<<< {response}")
            except Exception as e:
                print(f"[ERREUR] {type(e).__name__}: {e}")
            print("-" * 60)

    asyncio.run(main())