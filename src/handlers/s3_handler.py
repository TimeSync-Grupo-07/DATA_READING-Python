import boto3
import json
import io
from datetime import datetime

def upload_json_to_s3(data, bucket, key, folder="processed"):
    """
    Faz upload do JSON gerado para uma pasta específica dentro do bucket S3.

    Parâmetros:
    - data: dict → dados a enviar
    - bucket: str → nome do bucket S3
    - key: str → nome do arquivo (ex: "ponto_2025_11.json")
    - folder: str → pasta dentro do bucket (ex: "jsons/erro" ou "processed")
    """
    s3 = boto3.client("s3")

    # Serializa o JSON
    body = io.BytesIO(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    # Monta o caminho completo no S3
    folder = folder.strip("/apontamentos/")

    s3_key = f"{folder}/{key}"

    try:
        s3.upload_fileobj(
            Fileobj=body,
            Bucket=bucket,
            Key=s3_key,
            ExtraArgs={"ContentType": "application/json"}
        )
        print(f"✅ JSON enviado para S3 em: s3://{bucket}/{s3_key}")

    except Exception as e:
        print(f"❌ Erro ao enviar para S3: {e}")
