"""
Agent pydantic-ai utilisant email_utils.py pour la recherche, la lecture et l'envoi d'emails.
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Optional, Literal, List

from dotenv import load_dotenv
from pydantic_ai import Agent

from src.agent_logic.email_utils import search_emails, send_email
from src.agent_logic.doc_utils import (
    init_document, 
    append_to_document, 
    replace_in_document, 
    list_local_documents, 
    read_document_unified,
    write_to_excel,
    refresh_excel_file
)

from src.agent_logic.music_utils import global_player

from src.agent_logic.router_utils import (
    fetch_weather, 
    fetch_news, 
    fetch_places, 
    web_search,
    fetch_route
)

from typing import Literal # Ajoute cet import si ce n'est pas déjà fait

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "mistral:mistral-large-latest")

def get_system_prompt() -> str:
    current_date = datetime.now().strftime("%d-%b-%Y")
    return (
        "Tu es un assistant personnel intelligent contrôlé à la voix. "
        "L'utilisateur peut être malvoyant : sois descriptif sur les actions effectuées et n'hésite pas à relire les modifications. "
        "Tu es connecté à Internet : utilise tes outils pour chercher la météo, l'actualité, des lieux ou faire des recherches web si l'utilisateur pose une question d'actualité ou de culture générale. "
        "Tu es également un DJ personnel : tu peux chercher de la musique, la lancer, la mettre en pause, la reprendre ou l'arrêter complètement. "
        "Pour la rédaction de documents (.docx, .xlsx) : procède étape par étape. Demande ce dont tu as besoin pour guider l'utilisateur dans la création/lecture du document. "
        "Garde en mémoire le nom du fichier sur lequel tu travailles pour ne pas avoir à le redemander à chaque fois. "
        "Ne génère jamais un document entier sans valider chaque section avec l'utilisateur. "
        "Réponds toujours en français, sois concis et précis. "
        f"Date actuelle : {current_date} (format IMAP). "
        "RÈGLE CRITIQUE (Email) : Présente toujours le brouillon et attends une confirmation explicite avant d'utiliser `dispatch_email`."
    )

agent = Agent(
    model=LLM_MODEL,
    system_prompt=get_system_prompt(),
)

# --- OUTILS EMAILS ---

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

# --- OUTILS BUREAUTIQUE ---

@agent.tool_plain
def list_documents_tool() -> str:
    """
    Liste les documents (.docx, .xlsx, .txt) actuellement disponibles dans le répertoire de travail local.
    À utiliser quand l'utilisateur demande quels fichiers sont présents, ou avant de lire/modifier un fichier dont on n'est pas sûr du nom exact.
    """
    return list_local_documents()

@agent.tool_plain
def read_document_tool(filename: str, sheet_name: Optional[str] = None) -> str:
    """
    Lit le contenu d'un document (.docx, .txt, .xlsx).
    - filename: Nom exact du fichier (avec extension).
    - sheet_name: Optionnel, uniquement pour cibler un onglet précis dans un classeur Excel (.xlsx).
    """
    return read_document_unified(filename, sheet_name)

@agent.tool_plain
def init_doc_tool(filename: str) -> str:
    """Crée un nouveau document Word (.docx) vide ou écrase un document existant."""
    return init_document(filename)

@agent.tool_plain
def append_doc_tool(
    filename: str, 
    content: str, 
    element_type: Literal["paragraph", "heading", "list_item"] = "paragraph",
    level: int = 1
) -> str:
    """
    Ajoute un bloc de texte à la fin du document Word (.docx).
    - element_type: "heading" (titre), "paragraph" (texte normal), ou "list_item" (puce de liste).
    - level: niveau du titre (1 à 9), ignoré sinon.
    NOTE: Tu peux utiliser **texte** dans le `content` pour mettre des mots en gras.
    """
    return append_to_document(filename, content, element_type, level)

@agent.tool_plain
def edit_doc_tool(filename: str, old_text: str, new_text: str) -> str:
    """
    Modifie un document Word existant en remplaçant un passage exact par un autre.
    - old_text: L'extrait de texte exact à chercher (ne met pas tout le paragraphe, juste la phrase à changer).
    - new_text: Le nouveau texte qui remplacera l'ancien.
    """
    return replace_in_document(filename, old_text, new_text)

@agent.tool_plain
def write_excel_tool(filename: str, sheet_name: str, data: list[list[str]], start_row: int = 1, start_col: int = 1) -> str:
    """
    Crée un fichier Excel (.xlsx) ou modifie un existant en y écrivant des données.
    - data: Une liste de lignes (ex: [["Nom", "Age"], ["Alice", "30"]]).
    RÈGLE CRITIQUE : 
    Les formules DOIVENT être en anglais (ex: =RANDBETWEEN(0, 10), =AVERAGE(A1:A20)).
    """
    return write_to_excel(filename, sheet_name, data, start_row, start_col)

@agent.tool_plain
def refresh_excel_tool(filename: str) -> str:
    """
    Actualise un classeur Excel pour forcer le calcul de toutes ses formules.
    À utiliser IMPÉRATIVEMENT quand tu lis un fichier et que tu trouves des cellules contenant la mention "[Formule non évaluée]".
    """
    return refresh_excel_file(filename)

# --- EXECUTION ---

async def run_query(query: str) -> str:
    """Exécute une requête textuelle via l'agent et retourne la réponse."""
    result = await agent.run(query)
    return result.output

async def stream_query(query: str) -> AsyncGenerator[str, None]:
    """Exécute une requête en mode streaming et yield les tokens."""
    async with agent.run_stream(query) as streamed:
        async for chunk in streamed.stream_text(delta=True):
            yield chunk

# ---  MUSIQUE --- #

@agent.tool_plain
def search_music_tool(query: str) -> str:
    """
    Recherche une musique sur YouTube et renvoie une liste de 3 propositions.
    À utiliser TOUJOURS en premier quand l'utilisateur demande une musique. 
    Tu dois lire les propositions à l'utilisateur et attendre qu'il en choisisse une avant de la jouer.
    """
    return global_player.search(query)

@agent.tool_plain
def play_music_tool(url: str) -> str:
    """
    Lance la lecture d'une musique.
    - url: L'URL exacte de la musique, choisie par l'utilisateur suite à la recherche.
    """
    return global_player.play(url)

# (Vous pouvez garder pause_music_tool, resume_music_tool et stop_music_tool tels quels)

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

# ---  METEO --- #

@agent.tool_plain
async def get_weather_tool(city: str) -> dict:
    """
    Fournit la météo actuelle pour une ville donnée.
    À utiliser dès que l'utilisateur demande le temps qu'il fait.
    - city: Nom de la ville (ex: "Lyon", "Paris").
    """
    return await fetch_weather(city)

# ---  ACTUALITES --- #

@agent.tool_plain
async def get_news_tool(topic: str) -> dict:
    """
    Fournit les gros titres de l'actualité sur un sujet donné.
    - topic: Sujet de la recherche (ex: "technologie", "politique", "sport").
    """
    return await fetch_news(topic)

# ---  POINTS D'INTERETS --- #

@agent.tool_plain
async def find_places_tool(category: str, location: str) -> dict:
    """
    Recherche des points d'intérêts (restaurants, stations-service, musées, etc.).
    - category: Le type de lieu recherché (ex: "restaurant italien", "pharmacie").
    - location: La ville ou le quartier cible.
    """
    return await fetch_places(category, location)

@agent.tool_plain
async def web_search_tool(query: str) -> dict:
    """
    Effectue une recherche sur internet (DuckDuckGo).
    À utiliser pour répondre à une question de culture générale, vérifier un fait, 
    ou si l'information n'est pas couverte par les autres outils.
    - query: La question courte et précise à poser au moteur de recherche.
    """
    return await web_search(query)

# ---  GPS --- #

@agent.tool_plain
async def get_route_tool(origin: str, destination: str, mode: Literal["driving", "cycling", "walking"] = "cycling") -> dict:
    """
    Calcule le temps de trajet routier exact et la distance entre deux adresses ou lieux.
    À utiliser dès que l'utilisateur demande "combien de temps", "quelle distance", ou "itinéraire".
    - origin: Adresse ou lieu de départ.
    - destination: Adresse ou lieu d'arrivée.
    - mode: Le moyen de transport ("driving" pour la voiture, "cycling" pour le vélo, "walking" pour à pied).
    """
    return await fetch_route(origin, destination, mode)


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