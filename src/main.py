import time
from sqs_handler import SQSConsumer
from pdf_processor import PDFProcessor
from s3_uploader import S3Uploader
from config import Config

def main():
    config = Config()
    s3_uploader = S3Uploader(config)
    pdf_processor = PDFProcessor()
    sqs_consumer = SQSConsumer(config, pdf_processor, s3_uploader)

    print("Starting PDF processing service...")
    while True:
        try:
            sqs_consumer.process_messages()
            time.sleep(10)  # Sleep for 10 seconds between polling
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            time.sleep(30)  # Wait before retrying after an error

if __name__ == "__main__":
    main()