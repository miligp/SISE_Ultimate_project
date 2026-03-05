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

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "mistral:mistral-large-latest")

def get_system_prompt() -> str:
    current_date = datetime.now().strftime("%d-%b-%Y")
    return (
        "Tu es un assistant personnel intelligent contrôlé à la voix. "
        "L'utilisateur peut être malvoyant : sois descriptif sur les actions effectuées et n'hésite pas à relire les modifications. "
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