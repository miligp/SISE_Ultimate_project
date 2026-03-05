import os
import re
from pathlib import Path
from typing import List, Literal

from docx import Document

OUTPUT_DIR: Path = Path(os.getcwd()) / "output_docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _get_doc_path(filename: str) -> Path:
    if not filename.endswith(".docx"):
        filename += ".docx"
    return OUTPUT_DIR / filename

def init_document(filename: str) -> str:
    doc = Document()
    doc.save(_get_doc_path(filename))
    return f"Document {filename} initialisé."

def _add_markdown_paragraph(doc: Document, text: str, style: str | None = None) -> None:
    """Analyse un texte avec du gras Markdown (**texte**) et l'ajoute au document."""
    p = doc.add_paragraph(style=style)
    # Découpe le texte autour des balises **
    parts = re.split(r'(\*\*.*?\*\*)', text)
    
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            # On enlève les étoiles et on met en gras
            run = p.add_run(part[2:-2])
            run.bold = True
        else:
            p.add_run(part)

def append_to_document(
    filename: str, 
    content: str, 
    element_type: Literal["paragraph", "heading", "list_item"] = "paragraph",
    level: int = 1
) -> str:
    filepath: Path = _get_doc_path(filename)
    
    if not filepath.exists():
        doc = Document()
    else:
        doc = Document(filepath)
        
    if element_type == "heading":
        # On nettoie les éventuelles étoiles générées par erreur dans les titres
        clean_content = content.replace('**', '')
        doc.add_heading(clean_content, level=level)
    elif element_type == "list_item":
        _add_markdown_paragraph(doc, content, style='List Bullet')
    else:
        _add_markdown_paragraph(doc, content)
        
    doc.save(filepath)
    return f"Élément ({element_type}) ajouté à {filename}."

def read_document(filename: str) -> str:
    filepath: Path = _get_doc_path(filename)
    if not filepath.exists():
        return "Erreur : Le fichier n'existe pas."
        
    doc = Document(filepath)
    lines: List[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    
    if not lines:
        return "Le document est vide."
    return "\n".join(lines)