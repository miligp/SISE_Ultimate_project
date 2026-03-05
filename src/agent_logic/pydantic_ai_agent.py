"""
Agent pydantic-ai utilisant email_utils.py pour la recherche, la lecture et l'envoi d'emails.
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Optional, Literal

from dotenv import load_dotenv
from pydantic_ai import Agent

from src.agent_logic.email_utils import search_emails, send_email
from src.agent_logic.doc_utils import init_document, append_to_document, read_document

from src.agent_logic.music_utils import global_player

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "mistral:mistral-large-latest")

def get_system_prompt() -> str:
    current_date = datetime.now().strftime("%d-%b-%Y")
    return (
        "Tu es un assistant personnel intelligent contrôlé à la voix. "
        "L'utilisateur peut être malvoyant : sois descriptif sur les actions effectuées et n'hésite pas à relire les modifications. "
        "Tu es également un DJ personnel : tu peux chercher de la musique, la lancer, la mettre en pause, la reprendre ou l'arrêter complètement. "
        "Pour la rédaction de documents (.docx) : procède étape par étape. Demande d'abord le titre, puis l'en-tête, puis paragraphe par paragraphe. "
        "Ne génère jamais un document entier sans valider chaque section avec l'utilisateur. "
        "Réponds toujours en français, sois concis et précis. "
        f"Date actuelle : {current_date} (format IMAP). "
        "RÈGLE CRITIQUE (Email) : Présente toujours le brouillon et attends une confirmation explicite avant d'utiliser `dispatch_email`."
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

@agent.tool_plain
def init_doc_tool(filename: str) -> str:
    """Crée un nouveau document Word vide ou écrase un document existant."""
    return init_document(filename)

@agent.tool_plain
def append_doc_tool(
    filename: str, 
    content: str, 
    element_type: Literal["paragraph", "heading"] = "paragraph",
    level: int = 1
) -> str:
    """
    Ajoute un bloc de texte à la fin du document Word.
    - element_type: "heading" pour un titre, "paragraph" pour du texte normal.
    - level: niveau du titre (1 à 9), ignoré si element_type est "paragraph".
    """
    return append_to_document(filename, content, element_type, level)

@agent.tool_plain
def read_doc_tool(filename: str) -> str:
    """Lit l'intégralité du contenu actuel du document Word."""
    return read_document(filename)

@agent.tool_plain
def play_music_tool(query: str) -> str:
    """
    Recherche une musique sur YouTube et la joue immédiatement sur les enceintes.
    - query: Le nom de l'artiste, le titre de la chanson, ou le style musical.
    """
    return global_player.play(query)

@agent.tool_plain
def stop_music_tool() -> str:
    """
    Arrête la musique actuellement en cours de lecture sur l'ordinateur.
    À utiliser si l'utilisateur dit "stop la musique", "coupe le son", "silence", etc.
    """
    return global_player.stop()

@agent.tool_plain
def pause_music_tool() -> str:
    """
    Met en pause la musique actuellement en cours de lecture.
    À utiliser quand l'utilisateur dit "pause", "mets sur pause", "arrête un instant", etc.
    """
    return global_player.pause()

@agent.tool_plain
def resume_music_tool() -> str:
    """
    Reprend la lecture de la musique qui était en pause.
    À utiliser quand l'utilisateur dit "remets la musique", "reprends", "play", etc.
    """
    return global_player.resume()

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