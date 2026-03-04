"""
Agent pydantic-ai lié au serveur MCP Google Workspace.

L'agent ingère dynamiquement tous les outils exposés par le MCP au démarrage
(Gmail, Drive, Calendar, Docs, Sheets…) et les rend disponibles au LLM.

Usage autonome (test) :
    python -m src.agent_logic.pydantic_ai_agent
"""

import asyncio
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from pydantic_ai import Agent

from src.agent_logic.mcp_connection import get_mcp_server

load_dotenv()

# Modèle LLM : mistral-large-latest par défaut, configurable via .env
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:mistral-large-latest")

# Prompt système : donne le contexte Google Workspace à l'agent
SYSTEM_PROMPT = (
    "Tu es un assistant personnel intelligent connecté à Google Workspace. "
    "Tu peux lire et envoyer des emails Gmail, consulter et créer des événements "
    "Google Calendar, lire et modifier des fichiers Drive, Docs et Sheets. "
    "Réponds toujours en français sauf si l'utilisateur parle une autre langue. "
    "Sois concis et précis dans tes réponses."
)


def create_agent() -> Agent:
    """
    Crée et retourne l'agent pydantic-ai avec le serveur MCP attaché.

    Les outils MCP sont injectés dynamiquement à l'entrée du context manager
    agent.run_mcp_servers(). Aucune déclaration manuelle d'outils n'est requise.
    """
    mcp_server = get_mcp_server()
    return Agent(
        model=LLM_MODEL,
        mcp_servers=[mcp_server],
        system_prompt=SYSTEM_PROMPT,
    )


async def run_query(query: str) -> str:
    """
    Exécute une requête textuelle via l'agent et retourne la réponse.

    Le serveur MCP doit être démarré avant d'appeler cette fonction.
    Les outils sont découverts automatiquement à chaque appel.

    Args:
        query: La requête en langage naturel (ex: "Lis mes derniers mails").

    Returns:
        La réponse textuelle de l'agent.
    """
    agent = create_agent()
    async with agent.run_mcp_servers():
        result = await agent.run(query)
    return result.output


async def stream_query(query: str) -> AsyncGenerator[str, None]:
    """
    Exécute une requête en mode streaming et yield les tokens au fur et à mesure.

    Args:
        query: La requête en langage naturel.

    Yields:
        Les morceaux de texte générés par l'agent.
    """
    agent = create_agent()
    async with agent.run_mcp_servers():
        async with agent.run_stream(query) as streamed:
            async for chunk in streamed.stream_text(delta=True):
                yield chunk


# ─── Test autonome ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TEST_QUERIES = [
        "Lis le derniers mail et donne-moi un résumé."
    ]

    async def main():
        print(f"Agent connecté au modèle : {LLM_MODEL}")
        print("Serveur MCP attendu sur : http://localhost:8000/mcp\n")
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
