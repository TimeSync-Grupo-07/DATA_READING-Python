import time
import os
import json
import boto3
from src.handlers.email_handler import fetch_new_pdfs
from src.utils.pdf_to_json import pdf_to_json
import sys
import io

def log(msg):
    """Imprime mensagens com timestamp"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def main_loop():
    IMAP_HOST = os.getenv("IMAP_HOST")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    S3_BUCKET = os.getenv("S3_BUCKET")

    log("📬 Iniciando listener de e-mails...")
    log(f"🔧 Config: IMAP_HOST={IMAP_HOST}, EMAIL_USER={EMAIL_USER}, BUCKET={S3_BUCKET}")

    while True:
        try:
            log("📡 Conectando ao servidor IMAP...")
            pdfs = fetch_new_pdfs(IMAP_HOST, EMAIL_USER, EMAIL_PASS)
            log(f"📥 PDFs recebidos: {len(pdfs)}")

            if not pdfs:
                log("🕐 Nenhum novo e-mail encontrado.")
            else:
                s3 = boto3.client("s3")
                for pdf in pdfs:
                    data = pdf_to_json(pdf["content"])
                    s3_key = pdf['filename'].replace('.pdf', '.json')
                    s3.put_object(
                        Bucket=S3_BUCKET,
                        Key=s3_key,
                        Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                        ContentType="application/json"
                    )
                    log(f"✅ Enviado para S3: {s3_key}")

        except Exception as e:
            log(f"❌ Erro no ciclo principal: {e}")

        log("⏳ Aguardando 60s para nova verificação...\n")
        time.sleep(60)

if __name__ == "__main__":
    main_loop()

