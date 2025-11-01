# /src/main.py - CORRIGIDO
import time
import os
import json
import boto3
from botocore.exceptions import ClientError  # 👈 ADICIONE ESTE IMPORT
from src.handlers.email_handler import fetch_new_pdfs
from src.utils.pdf_to_json import pdf_to_json
import traceback
import re
import unicodedata
from datetime import datetime

def log(msg):
    """Imprime mensagens com timestamp"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def test_s3_permissions(bucket):
    """Testa as permissões S3 antes de tentar fazer upload"""
    try:
        s3 = boto3.client("s3")
        
        # Testa listagem do bucket
        s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        log("✅ Permissão de listagem: OK")
        
        # Testa upload (objeto pequeno de teste)
        test_key = "test-permission.txt"
        s3.put_object(
            Bucket=bucket,
            Key=test_key,
            Body=b"test",
            ContentType="text/plain"
        )
        log("✅ Permissão de upload: OK")
        
        # Limpa o teste
        s3.delete_object(Bucket=bucket, Key=test_key)
        log("✅ Permissão de delete: OK")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        log(f"❌ Falha na permissão ({error_code}): {error_message}")
        return False
    except Exception as e:
        log(f"❌ Erro inesperado no teste: {e}")
        return False

def upload_to_s3(data, bucket, key):
    """Faz upload para S3 com tratamento de erro melhorado"""
    try:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json"
        )
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        log(f"❌ Erro AWS S3 ({error_code}): {error_message}")
        return False
    except Exception as e:
        log(f"❌ Erro inesperado no S3: {e}")
        return False

def main_loop():
    IMAP_HOST = os.getenv("IMAP_HOST")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    S3_BUCKET = os.getenv("S3_BUCKET")
    
    log("📬 Iniciando listener de e-mails...")
    log(f"🔧 Config: IMAP_HOST={IMAP_HOST}, EMAIL_USER={EMAIL_USER}, BUCKET={S3_BUCKET}")

    # Testa permissões S3 primeiro
    log("🔐 Testando permissões S3...")
    if not test_s3_permissions(S3_BUCKET):
        log("🚫 Permissões S3 insuficientes. Verifique a política IAM.")
        log("💡 O fluxo IMAP funcionará, mas os uploads S3 falharão.")
        # Não retorne aqui - deixe o processo continuar para testar o IMAP

    while True:
        try:
            log("📡 Conectando ao servidor IMAP...")
            pdfs = fetch_new_pdfs(IMAP_HOST, EMAIL_USER, EMAIL_PASS)
            log(f"📥 PDFs recebidos: {len(pdfs)}")

            if not pdfs:
                log("🕐 Nenhum novo e-mail encontrado.")
            else:
                for pdf in pdfs:
                    log(f"🔄 Processando PDF: {pdf['filename']}")
                    
                    # Converte PDF para JSON
                    data = pdf_to_json(pdf["content"])
                    log(f"📄 PDF convertido: {len(data.get('lines', []))} linhas extraídas")
                    
                    # EXTRAI O NOME DO COLABORADOR PARA O NOME DO ARQUIVO
                    employee_name = extract_employee_name_for_filename(data)
                    current_date = time.strftime("%Y-%m-%d")
                    
                    # Define chave S3 com o novo padrão: Nome_Colaborador_Data_envio_email.json
                    s3_key = f"{employee_name}_{current_date}.json"
                    log(f"📤 Tentando upload para S3: {s3_key}")
                    
                    # Faz upload
                    if upload_to_s3(data, S3_BUCKET, s3_key):
                        log(f"✅ Upload bem-sucedido: {s3_key}")
                    else:
                        log(f"❌ Falha no upload: {s3_key}")

        except Exception as e:
            log(f"❌ Erro no ciclo principal: {e}")
            import traceback
            log(f"🔍 Traceback: {traceback.format_exc()}")

        log("⏳ Aguardando 60s para nova verificação...\n")
        time.sleep(60)

def extract_employee_name_for_filename(data):
    """
    Extrai e formata o nome do colaborador para usar no nome do arquivo.
    Remove acentos, espaços e caracteres especiais.
    """
    try:
        # Tenta pegar o nome da estrutura processada
        employee_name = data.get('header_info', {}).get('employee', {}).get('name', '')
        
        if not employee_name:
            # Fallback: procura nas linhas brutas
            for line in data.get('raw_lines', []):
                if 'Colaborador(a):' in line:
                    # Exemplo: "Colaborador(a): Giovanna AAvila (Matrícula: 509880)"
                    match = re.search(r'Colaborador\(a\):\s*([^(]+)', line)
                    if match:
                        employee_name = match.group(1).strip()
                        break
        
        # Limpa e formata o nome para o arquivo
        if employee_name:
            # Remove acentos e caracteres especiais
            import unicodedata
            employee_name = unicodedata.normalize('NFKD', employee_name)
            employee_name = ''.join(c for c in employee_name if not unicodedata.combining(c))
            
            # Substitui espaços por underscores e remove outros caracteres especiais
            employee_name = re.sub(r'[^\w\s-]', '', employee_name)
            employee_name = re.sub(r'[-\s]+', '_', employee_name)
            
            return employee_name.lower()
        else:
            return "colaborador_desconhecido"
            
    except Exception as e:
        log(f"⚠️ Erro ao extrair nome do colaborador: {e}")
        return "colaborador_desconhecido"

if __name__ == "__main__":
    main_loop()
