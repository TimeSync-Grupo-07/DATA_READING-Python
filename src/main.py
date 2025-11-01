import os
import time
from dotenv import load_dotenv
from handlers.email_handler import fetch_new_pdfs
from handlers.pdf_handler import process_pdf
from handlers.s3_handler import upload_json_to_s3

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
S3_BUCKET = os.getenv("S3_BUCKET")

CHECK_INTERVAL = 60  # segundos

def main():
    print("📬 Iniciando listener de e-mails...")
    while True:
        try:
            pdfs = fetch_new_pdfs(IMAP_HOST, EMAIL_USER, EMAIL_PASS)

            if not pdfs:
                print("Nenhum novo e-mail encontrado.")
            else:
                for pdf in pdfs:
                    print(f"📄 Processando {pdf['filename']}...")
                    json_data = process_pdf(pdf["content"])
                    json_key = pdf["filename"].replace(".pdf", ".json")
                    upload_json_to_s3(json_data, S3_BUCKET, json_key)

        except Exception as e:
            print(f"❌ Erro no ciclo principal: {e}")

        print(f"⏳ Aguardando {CHECK_INTERVAL}s para nova verificação...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
