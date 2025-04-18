import boto3
from io import StringIO
from botocore.exceptions import ClientError

class S3Uploader:
    def __init__(self, config):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=config.aws_access_key,
            aws_secret_access_key=config.aws_secret_key,
            region_name=config.aws_region
        )
        self.bucket_name = config.s3_bucket_name
        
    def upload_csv(self, key, csv_data):
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=csv_data,
                ContentType='text/csv'
            )
            print(f"Successfully uploaded CSV to s3://{self.bucket_name}/{key}")
        except ClientError as e:
            print(f"S3 Upload Error: {str(e)}")
            raise