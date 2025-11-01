# /src/handlers/email_handler.py - CORRIGIDO
import imaplib
import email
from email.header import decode_header
import io
import sys

# Garante que o stdout use UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def safe_decode(value):
    """Decodifica textos MIME de forma segura em UTF-8."""
    if not value:
        return ""
    
    try:
        parts = decode_header(value)
        decoded = ""
        for text, enc in parts:
            if isinstance(text, bytes):
                # Usa UTF-8 como fallback se a codificação não for especificada
                encoding = enc or 'utf-8'
                try:
                    decoded += text.decode(encoding, errors='replace')
                except (UnicodeDecodeError, LookupError):
                    # Fallback para UTF-8 com substituição de caracteres inválidos
                    decoded += text.decode('utf-8', errors='replace')
            else:
                decoded += text
        return decoded
    except Exception as e:
        print(f"⚠️  Erro ao decodificar '{value}': {e}")
        return str(value) if value else ""

def fetch_new_pdfs(imap_host, user, password):
    print(f"🔗 Tentando conectar a {imap_host} como {user}", flush=True)
    
    pdfs = []  # ADICIONAR ESTA LINHA - FALTANDO NO CÓDIGO ORIGINAL!
    
    try:
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(user, password)
        print("✅ Login IMAP bem-sucedido", flush=True)
        mail.select("INBOX")

        status, messages = mail.search(None, '(UNSEEN)')
        print(f"📬 E-mails não lidos encontrados: {len(messages[0].split()) if messages[0] else 0}", flush=True)

        if not messages[0]:
            print("📭 Nenhum e-mail não lido encontrado")
            mail.logout()
            return pdfs

        for num in messages[0].split():
            try:
                status, msg_data = mail.fetch(num, '(RFC822)')
                if not msg_data or not msg_data[0]:
                    continue
                    
                msg = email.message_from_bytes(msg_data[0][1])

                subject = safe_decode(msg.get("Subject", ""))
                from_ = safe_decode(msg.get("From", ""))
                print(f"📧 Processando e-mail de: {from_} | Assunto: {subject}")

                # Processa anexos PDF
                for part in msg.walk():
                    if part.get_content_type() == "application/pdf":
                        filename = part.get_filename()
                        if filename:
                            filename = safe_decode(filename)
                            pdf_bytes = part.get_payload(decode=True)
                            
                            if pdf_bytes:
                                pdfs.append({
                                    "filename": filename,
                                    "content": io.BytesIO(pdf_bytes)
                                })
                                print(f"📎 PDF encontrado: {filename}")

                # Marca o e-mail como lido
                mail.store(num, '+FLAGS', '\\Seen')
                
            except Exception as e:
                print(f"❌ Erro ao processar e-mail {num}: {e}")
                continue

        mail.logout()
        
    except Exception as e:
        print(f"❌ Erro na conexão IMAP: {e}")
    
    return pdfs