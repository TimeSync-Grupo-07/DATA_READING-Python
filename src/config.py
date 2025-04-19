import os
import boto3
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_session_token = os.getenv('AWS_SESSION_TOKEN')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        self.sqs_queue_url = os.getenv('SQS_QUEUE_URL')
        if not self.sqs_queue_url:
            raise ValueError("SQS_QUEUE_URL não definido no .env!")
        
        self.s3_bucket_name = os.getenv('S3_BUCKET_NAME')
        if not self.s3_bucket_name:
            raise ValueError("S3_BUCKET_NAME não definido no .env!")
        
        self.redis_host = os.getenv('REDIS_HOST', 'redis')
        self.redis_port = os.getenv('REDIS_PORT', '6379')
        
        self.instance_id = os.getenv('INSTANCE_ID', '0')
    
    def get_boto3_client(self, service_name):
        """Retorna um cliente boto3 configurado para local ou AWS."""
        if self.aws_access_key and self.aws_secret_key:  
            return boto3.client(
                service_name,
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                aws_session_token=self.aws_session_token 
            )
        else:
            return boto3.client(service_name, region_name=self.aws_region)