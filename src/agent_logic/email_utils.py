import imaplib
import email
from email.header import decode_header
from email.message import Message
from typing import List, Dict, Optional
import os
import smtplib
from email.message import EmailMessage
import re
import mimetypes
from pathlib import Path

def send_email(to_address: str, subject: str, body: str, attachment_path: Optional[str] = None) -> str:
    user: str | None = os.getenv("EMAIL_USER")
    password: str | None = os.getenv("EMAIL_PASSWORD")
    server: str = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    port: int = int(os.getenv("EMAIL_SMTP_PORT", "465"))

    if not user or not password:
        return "Error: Missing credentials."

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_address

    if attachment_path:
        path = Path(attachment_path)
        if not path.exists() or not path.is_file():
            return f"Error: Attachment file not found at {attachment_path}."
        
        ctype, encoding = mimetypes.guess_type(str(path))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=path.name)

    try:
        with smtplib.SMTP_SSL(server, port) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return f"Email successfully sent to {to_address}."
    except Exception as e:
        return f"Failed to send email: {e}"

def _get_email_body(msg: Message, max_length: int = 2000) -> str:
    body_plain: str = ""
    body_html: str = ""
    
    for part in msg.walk():
        content_type: str = part.get_content_type()
        disposition: str = str(part.get("Content-Disposition"))
        
        if "attachment" in disposition:
            continue
            
        try:
            charset: str = part.get_content_charset() or "utf-8"
            payload: Optional[bytes] = part.get_payload(decode=True)
            if payload:
                decoded_text = payload.decode(charset, errors="replace")
                if content_type == "text/plain":
                    body_plain += decoded_text
                elif content_type == "text/html":
                    body_html += decoded_text
        except Exception:
            continue

    # Priorité au texte brut, sinon nettoyage basique du HTML
    final_body = body_plain if body_plain else re.sub(r'<[^>]+>', ' ', body_html)
    
    # Nettoyage des espaces multiples
    final_body = re.sub(r'\s+', ' ', final_body)
            
    return final_body.strip()[:max_length]

def search_emails(
    sender: Optional[str] = None, 
    subject: Optional[str] = None, 
    since_date: Optional[str] = None, 
    limit: int = 5,
    is_unread: bool = False
) -> List[Dict[str, str]]:
    user: Optional[str] = os.getenv("EMAIL_USER")
    password: Optional[str] = os.getenv("EMAIL_PASSWORD")
    server: str = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")

    if not user or not password:
        return [{"error": "Missing email credentials."}]

    emails: List[Dict[str, str]] = []
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        
        search_criteria: List[str] = []
        if is_unread:
            search_criteria.append("UNSEEN")
            
        if sender:
            search_criteria.append(f'(FROM "{sender}")')
        if subject:
            search_criteria.append(f'(SUBJECT "{subject}")')
        if since_date:
            search_criteria.append(f'(SINCE "{since_date}")')
            
        query: str = " ".join(search_criteria) if search_criteria else "ALL"
        
        status, data = mail.search(None, query)
        if status != "OK" or not data or not data[0]:
            return []
            
        mail_ids: List[str] = data[0].split()
        emails: List[Dict[str, str]] = []
        
        for m_id_bytes in mail_ids[-limit:]:
            m_id: str = m_id_bytes.decode('utf-8')
            _, msg_data = mail.fetch(m_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg: Message = email.message_from_bytes(response_part[1])
                    
                    subject_header = msg.get("Subject", "")
                    decoded_subject: str = ""
                    if subject_header:
                        decoded_parts = decode_header(subject_header)
                        raw_subject, encoding = decoded_parts[0]
                        if isinstance(raw_subject, bytes):
                            decoded_subject = raw_subject.decode(encoding or "utf-8", errors="replace")
                        else:
                            decoded_subject = str(raw_subject)
                    
                    emails.append({
                        "id": m_id, # AJOUT DE L'ID IMAP
                        "from": str(msg.get("From", "")),
                        "subject": decoded_subject,
                        "date": str(msg.get("Date", "")),
                        "body": _get_email_body(msg)
                    })
        mail.logout()
    except Exception as e:
        return [{"error": str(e)}]
        
    return emails[::-1]

def delete_email(mail_id: str) -> str:
    """
    Supprime définitivement un email via son identifiant IMAP.
    """
    user: str | None = os.getenv("EMAIL_USER")
    password: str | None = os.getenv("EMAIL_PASSWORD")
    server: str = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")

    if not user or not password:
        return "Error: Missing credentials."

    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        
        # Le protocole IMAP marque d'abord le message comme supprimé (\Deleted)
        mail.store(mail_id, '+FLAGS', '\\Deleted')
        # Puis expunge nettoie définitivement la boîte des messages marqués
        mail.expunge()
        mail.logout()
        
        return f"Succès : l'email avec l'ID {mail_id} a été supprimé définitivement."
    except Exception as e:
        return f"Erreur lors de la suppression de l'email : {e}"