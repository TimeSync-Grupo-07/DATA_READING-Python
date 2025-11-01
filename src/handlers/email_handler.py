import imaplib
import email
from email.header import decode_header
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def safe_decode(value):
    """Decodifica textos MIME (ex: nomes de arquivos, assunto, remetente) de forma segura em UTF-8."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            decoded += text.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded

def fetch_new_pdfs(imap_host, user, password):
    import sys
    print(f"🔗 Tentando conectar a {imap_host} como {user}", flush=True)
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(user, password)
    print("✅ Login IMAP bem-sucedido", flush=True)
    mail.select("INBOX")

    status, messages = mail.search(None, '(UNSEEN)')
    print(f"📬 E-mails não lidos encontrados: {messages}", flush=True)


    for num in messages[0].split():
        status, msg_data = mail.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])

        subject = safe_decode(msg.get("Subject"))
        from_ = safe_decode(msg.get("From"))
        print(f"📧 Novo e-mail de: {from_} | Assunto: {subject}")

        for part in msg.walk():
            if part.get_content_type() == "application/pdf":
                filename = part.get_filename()
                filename = safe_decode(filename)

                pdf_bytes = part.get_payload(decode=True)
                pdfs.append({
                    "filename": filename,
                    "content": io.BytesIO(pdf_bytes)
                })
                print(f"📎 PDF encontrado: {filename}")

        # Marca o e-mail como lido
        mail.store(num, '+FLAGS', '\\Seen')

    mail.logout()
    return pdfs
