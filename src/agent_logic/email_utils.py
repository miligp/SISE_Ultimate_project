import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
import os

def get_latest_emails(count: int = 5) -> List[Dict[str, str]]:
    """Fetch the latest emails from the inbox using IMAP."""
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")

    emails = []
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")

        # Search for all emails
        _, data = mail.search(None, "ALL")
        mail_ids = data[0].split()
        
        # Get the last N ids
        for m_id in mail_ids[-count:]:
            _, msg_data = mail.fetch(m_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")
                    
                    emails.append({
                        "from": msg.get("From"),
                        "subject": subject,
                        "date": msg.get("Date")
                    })
        mail.logout()
    except Exception as e:
        return [{"error": str(e)}]
        
    return emails[::-1] # Newest first