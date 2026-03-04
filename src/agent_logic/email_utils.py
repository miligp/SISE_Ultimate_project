import imaplib
import email
from email.header import decode_header
from email.message import Message
from typing import List, Dict, Optional
import os
import smtplib
from email.message import EmailMessage

def send_email(to_address: str, subject: str, body: str) -> str:
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

    try:
        with smtplib.SMTP_SSL(server, port) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return f"Email successfully sent to {to_address}."
    except Exception as e:
        return f"Failed to send email: {e}"

def _get_email_body(msg: Message, max_length: int = 2000) -> str:
    body: str = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type: str = part.get_content_type()
            disposition: str = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in disposition:
                try:
                    charset: str = part.get_content_charset() or "utf-8"
                    payload: Optional[bytes] = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(charset, errors="replace")
                except Exception:
                    continue
    else:
        if msg.get_content_type() == "text/plain":
            try:
                charset: str = msg.get_content_charset() or "utf-8"
                payload: Optional[bytes] = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors="replace")
            except Exception:
                pass
                
    return body.strip()[:max_length]

def get_latest_emails(count: int = 5) -> List[Dict[str, str]]:
    user: Optional[str] = os.getenv("EMAIL_USER")
    password: Optional[str] = os.getenv("EMAIL_PASSWORD")
    server: str = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")

    if not user or not password:
        return [{"error": "Missing email credentials in environment variables."}]

    emails: List[Dict[str, str]] = []
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")

        _, data = mail.search(None, "ALL")
        if not data or not data[0]:
            return []
            
        mail_ids: List[str] = data[0].split()
        
        for m_id in mail_ids[-count:]:
            _, msg_data = mail.fetch(m_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg: Message = email.message_from_bytes(response_part[1])
                    
                    subject_header = msg.get("Subject", "")
                    subject: str = ""
                    if subject_header:
                        decoded_parts = decode_header(subject_header)
                        decoded_subject, encoding = decoded_parts[0]
                        if isinstance(decoded_subject, bytes):
                            subject = decoded_subject.decode(encoding or "utf-8", errors="replace")
                        else:
                            subject = str(decoded_subject)
                    
                    emails.append({
                        "from": str(msg.get("From", "")),
                        "subject": subject,
                        "date": str(msg.get("Date", "")),
                        "body": _get_email_body(msg)
                    })
        mail.logout()
    except Exception as e:
        return [{"error": str(e)}]
        
    return emails[::-1]