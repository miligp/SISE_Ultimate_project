"""
Agent pydantic-ai utilisant email_utils.py pour la recherche, la lecture et l'envoi d'emails.
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Optional, Literal, List, Dict

from dotenv import load_dotenv
from pydantic_ai import Agent

from src.agent_logic.email_utils import search_emails, send_email, delete_email
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

from src.agent_logic.doc_utils import OUTPUT_DIR


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
    limit: int = 5,
    is_unread: bool = False
) -> List[Dict[str, str]]:
    """
    Fetches emails from the inbox based on specific criteria.
    - sender: Email address or partial name of the sender.
    - subject: Keyword in the email subject.
    - since_date: Start date in 'DD-Mon-YYYY' format.
    - limit: Maximum number of emails to retrieve (default: 5).
    - is_unread: Boolean (True) if the user explicitly asks for "new" or "unread" messages.
    """
    return search_emails(sender, subject, since_date, limit, is_unread)

@agent.tool_plain
def send_email_tool(to_address: str, subject: str, body: str, attachment_filename: Optional[str] = None) -> str:
    """
    Envoie un email avec la possibilité d'ajouter une pièce jointe locale.
    - to_address: L'adresse email du destinataire.
    - subject: Le sujet de l'email.
    - body: Le contenu textuel du message.
    - attachment_filename: Le nom exact du fichier à joindre (ex: 'data.xlsx' ou 'report.docx'). Optionnel.
    """
    attachment_path: Optional[str] = None
    if attachment_filename:
        attachment_path = str(OUTPUT_DIR / attachment_filename)
        
    return send_email(to_address, subject, body, attachment_path)

@agent.tool_plain
def delete_email_tool(mail_id: str) -> str:
    """
    Supprime définitivement un email de la boîte de réception.
    - mail_id: L'identifiant unique de l'email (il doit obligatoirement être récupéré au préalable via fetch_emails_tool).
    RÈGLE DE SÉCURITÉ : Ne supprime jamais un email sans avoir lu son contenu à l'utilisateur et obtenu sa confirmation explicite.
    """
    return delete_email(mail_id)

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