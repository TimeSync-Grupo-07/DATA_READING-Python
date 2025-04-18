import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        # AWS Configuration
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # SQS Configuration
        self.sqs_queue_url = os.getenv('SQS_QUEUE_URL')
        
        # S3 Configuration
        self.s3_bucket_name = os.getenv('S3_BUCKET_NAME')
        
        # Redis Configuration
        self.redis_host = os.getenv('REDIS_HOST', 'redis')
        self.redis_port = os.getenv('REDIS_PORT', '6379')
        
        # Instance ID
        self.instance_id = os.getenv('INSTANCE_ID', '0')