import os
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any
from config import settings

def fetch_recent_application_threads(user_email: str, app_password: str, query: str = '(OR SUBJECT "application" SUBJECT "interview")') -> List[Dict]:
    """Fetches recent email threads using IMAP and App Passwords."""
    if not user_email or not app_password:
        return []
        
    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user_email, app_password)
        mail.select("inbox")
        
        # Search for messages
        # IMAP search strings can be tricky, using basic SUBJECT search
        status, messages = mail.search(None, query)
        if status != 'OK':
            return []
            
        thread_data = []
        # Get the IDs of the last 10 messages
        msg_ids = messages[0].split()[-10:]
        
        for msg_id in reversed(msg_ids):
            status, data = mail.fetch(msg_id, "(RFC822)")
            if status != 'OK':
                continue
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Decode subject
            subject, encoding = decode_header(msg.get("Subject", "No Subject"))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")
                
            # Snippet logic (simple)
            snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        snippet = part.get_payload(decode=True).decode()[:200]
                        break
            else:
                snippet = msg.get_payload(decode=True).decode()[:200]

            thread_data.append({
                "id": msg_id.decode(),
                "subject": subject,
                "snippet": snippet,
                "date": msg.get("Date")
            })
            
        mail.logout()
        return thread_data
    except Exception as e:
        print(f"IMAP Error: {e}")
        return []

def draft_follow_up_email(*args, **kwargs):
    """IMAP doesn't easily support Gmail-style drafts via API, will implement SMTP if needed."""
    print("IMAP Draft-creation not implemented. Use SMTP for sending.")
    return None
