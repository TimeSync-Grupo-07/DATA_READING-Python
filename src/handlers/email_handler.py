import imaplib
import email
from email.header import decode_header
import io

def fetch_new_pdfs(imap_host, user, password):
    """Lê novos e-mails (não lidos), extrai anexos PDF e marca como lido."""
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(user, password)
    mail.select("INBOX")

    status, messages = mail.search(None, '(UNSEEN)')
    pdfs = []

    for num in messages[0].split():
        status, msg_data = mail.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        
        for part in msg.walk():
            if part.get_content_type() == "application/pdf":
                filename = part.get_filename()
                if filename:
                    decoded_name, enc = decode_header(filename)[0]
                    if isinstance(decoded_name, bytes):
                        filename = decoded_name.decode(enc or "utf-8")

                    pdf_bytes = part.get_payload(decode=True)
                    pdfs.append({
                        "filename": filename,
                        "content": io.BytesIO(pdf_bytes)
                    })

        # Marca como lido
        mail.store(num, '+FLAGS', '\\Seen')

    mail.logout()
    return pdfs
