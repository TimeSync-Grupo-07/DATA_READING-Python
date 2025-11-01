import boto3
import json
import io

def upload_json_to_s3(data, bucket, key):
    """Faz upload do JSON gerado para o bucket S3."""
    s3 = boto3.client("s3")
    body = io.BytesIO(json.dumps(data, indent=2).encode("utf-8"))

    s3.upload_fileobj(
        Fileobj=body,
        Bucket=bucket,
        Key=f"processed/{key}",
        ExtraArgs={"ContentType": "application/json"}
    )
    print(f"✅ Enviado para S3: processed/{key}")
