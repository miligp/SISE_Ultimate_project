import os
import re
from pathlib import Path
from typing import List, Literal, Optional

import openpyxl
from docx import Document

OUTPUT_DIR: Path = Path(os.getcwd()) / "output_docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _get_file_path(filename: str, default_ext: str = ".docx") -> Path:
    if not Path(filename).suffix:
        filename += default_ext
    return OUTPUT_DIR / filename

def list_local_documents() -> str:
    if not OUTPUT_DIR.exists():
        return "Directory does not exist."
    files = [f.name for f in OUTPUT_DIR.iterdir() if f.is_file() and f.suffix in ['.docx', '.xlsx', '.txt']]
    return f"Documents: {', '.join(files)}" if files else "No documents found."

def init_document(filename: str) -> str:
    filepath = _get_file_path(filename, ".docx")
    doc = Document()
    doc.save(filepath)
    return f"Document initialized: {filepath.name}"

def _add_markdown_paragraph(doc: Document, text: str, style: Optional[str] = None) -> None:
    if not text.strip():
        return
    p = doc.add_paragraph(style=style)
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
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
    filepath = _get_file_path(filename, ".docx")
    
    try:
        doc = Document(filepath) if filepath.exists() else Document()
    except Exception:
        return "Error: Cannot open file. Is it open in Word?"
        
    if element_type == "heading":
        clean_content = content.replace('**', '')
        doc.add_heading(clean_content, level=level)
    elif element_type == "list_item":
        _add_markdown_paragraph(doc, content, style='List Bullet')
    else:
        _add_markdown_paragraph(doc, content)
        
    try:
        doc.save(filepath)
        return f"Element appended to {filepath.name}."
    except PermissionError:
        return "Error: File is locked. Close Microsoft Word."

def replace_in_document(filename: str, old_text: str, new_text: str) -> str:
    filepath = _get_file_path(filename, ".docx")
    if not filepath.exists():
        return "Error: File not found."
        
    try:
        doc = Document(filepath)
        replaced = False
        for p in doc.paragraphs:
            if old_text in p.text:
                p.text = p.text.replace(old_text, new_text)
                replaced = True
                
        if replaced:
            doc.save(filepath)
            return f"Modification successful in {filepath.name}."
        return f"Error: Text '{old_text}' not found."
    except PermissionError:
        return "Error: File is locked."
    except Exception as e:
        return f"Unexpected error: {e}"

def _read_docx(filepath: Path) -> str:
    try:
        doc = Document(filepath)
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(lines) if lines else "Document is empty."
    except Exception as e:
        return f"Error reading docx: {e}"

def _read_txt(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading txt: {e}"

def list_excel_sheets(filename: str) -> str:
    filepath = _get_file_path(filename, ".xlsx")
    if not filepath.exists():
        return "Error: File not found."
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        sheets = wb.sheetnames
        wb.close()
        return f"Sheets in {filepath.name}: {', '.join(sheets)}"
    except Exception as e:
        return f"Error: {e}"

def read_excel_sheet(filename: str, sheet_name: Optional[str] = None, max_rows: int = 50) -> str:
    filepath = _get_file_path(filename, ".xlsx")
    if not filepath.exists():
        return "Error: File not found."
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        
        data = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= max_rows:
                data.append("... (truncated)")
                break
            if any(cell is not None for cell in row):
                data.append(" | ".join(str(cell).strip() if cell is not None else "" for cell in row))
                
        wb.close()
        return f"Sheet '{ws.title}' content:\n" + "\n".join(data) if data else f"Sheet '{ws.title}' is empty."
    except Exception as e:
        return f"Error: {e}"

def read_document_unified(filename: str, sheet_name: Optional[str] = None) -> str:
    filepath: Path = OUTPUT_DIR / filename
    if not filepath.exists():
        return f"Error: {filename} not found."
        
    ext = filepath.suffix.lower()
    if ext == ".docx":
        return _read_docx(filepath)
    elif ext == ".txt":
        return _read_txt(filepath)
    elif ext == ".xlsx":
        return read_excel_sheet(filename, sheet_name)
    return f"Error: Unsupported format {ext}."