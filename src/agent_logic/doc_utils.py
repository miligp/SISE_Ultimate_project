import os
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

def append_to_document(
    filename: str, 
    content: str, 
    element_type: Literal["paragraph", "heading"] = "paragraph",
    level: int = 1
) -> str:
    filepath: Path = _get_doc_path(filename)
    
    if not filepath.exists():
        doc = Document()
    else:
        doc = Document(filepath)
        
    if element_type == "heading":
        doc.add_heading(content, level=level)
    else:
        doc.add_paragraph(content)
        
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