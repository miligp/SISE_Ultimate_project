"""
Agent pydantic-ai utilisant email_utils.py pour la lecture des emails.
"""

import asyncio
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from pydantic_ai import Agent

from src.agent_logic.email_utils import get_latest_emails, send_email


load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "mistral:mistral-large-latest")

SYSTEM_PROMPT: str = (
    "Tu es un assistant personnel intelligent. "
    "Tu as accès à des fonctions pour lire et envoyer des emails. "
    "Réponds toujours en français sauf si l'utilisateur parle une autre langue. "
    "Sois concis et précis dans tes réponses. "
    "RÈGLE CRITIQUE : Ne déclenche JAMAIS l'outil `send_email` de ta propre initiative. "
    "Tu dois d'abord présenter le brouillon (destinataire, objet, corps) à l'utilisateur, "
    "puis attendre explicitement sa confirmation dans le tour de parole suivant avant d'exécuter l'outil."
)

agent = Agent(
    model=LLM_MODEL,
    system_prompt=SYSTEM_PROMPT,
)

@agent.tool_plain
def fetch_emails(count: int = 5) -> list[dict[str, str]]:
    """Récupère les derniers emails de la boîte de réception."""
    return get_latest_emails(count)

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
        "Récupère mes 3 derniers emails et fais-en un résumé."
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