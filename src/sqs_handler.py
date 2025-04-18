import boto3
import json
import redis
from botocore.exceptions import ClientError
from time import sleep
from contextlib import contextmanager
from config import Config

class SQSConsumer:
    def __init__(self, config, pdf_processor, s3_uploader):
        self.sqs = boto3.client(
            'sqs',
            aws_access_key_id=config.aws_access_key,
            aws_secret_access_key=config.aws_secret_key,
            region_name=config.aws_region
        )
        self.queue_url = config.sqs_queue_url
        self.pdf_processor = pdf_processor
        self.s3_uploader = s3_uploader
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=0
        )
        self.instance_id = config.instance_id
        
    def process_messages(self):
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=30  # Tempo para evitar que outra instância pegue a mesma mensagem
            )
            
            if 'Messages' in response:
                for message in response['Messages']:
                    with self._distributed_lock(message['MessageId']):
                        self._process_message(message)
                        self._delete_message(message)
                    
        except ClientError as e:
            print(f"[Instance {self.instance_id}] SQS Client Error: {str(e)}")
            raise
            
    @contextmanager
    def _distributed_lock(self, message_id):
        """Implementa um bloqueio distribuído usando Redis"""
        lock_key = f"lock:{message_id}"
        
        # Tenta adquirir o bloqueio (expira após 60 segundos automaticamente)
        acquired = self.redis.set(lock_key, self.instance_id, nx=True, ex=60)
        
        if acquired:
            try:
                yield
            finally:
                # Libera o bloqueio
                if self.redis.get(lock_key) == self.instance_id.encode():
                    self.redis.delete(lock_key)
        else:
            print(f"[Instance {self.instance_id}] Lock already acquired by another instance for message {message_id}")
            raise Exception("Could not acquire lock")
            
    # ... (restante do código permanece igual)