import boto3
import json
import logging
import requests
from config.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, SQS_QUEUE_URL, SQS_DLQ_URL

logger = logging.getLogger(__name__)

class SQSService:
    def __init__(self):
        try:
            self.sqs_client = boto3.client(
                'sqs',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            self.queue_url = SQS_QUEUE_URL
            self.dlq_url = SQS_DLQ_URL
            logger.info("Successfully connected to AWS SQS")
        except Exception as e:
            logger.error(f"Failed to connect to AWS SQS: {e}")
            raise

    def move_to_dlq(self, message):
        if self.dlq_url:
            self.sqs_client.send_message(
                QueueUrl=self.dlq_url,
                MessageBody=message['Body']
            )
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            logger.info(f"Moved message to DLQ: {self.dlq_url}")
        else:
            logger.warning("No DLQ configured, message will not be moved: deleting from source queue")
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )

    def process_message(self, message, retry_count=0, max_retries=2):
        try:
            body = json.loads(message['Body'])
            file_key = None
            
            # Handle S3 event format
            if 'Records' in body and isinstance(body['Records'], list):
                for record in body['Records']:
                    if 's3' in record and 'object' in record['s3']:
                        file_key = record['s3']['object']['key']
                        break
            
            # Fallback to direct file_key if present
            if not file_key:
                file_key = body.get('file_key')
            
            if not file_key:
                raise ValueError("No file_key in SQS message")
            
            logger.info(f"Extracted file_key from SQS message: {file_key}")
            logger.info(f"Processing SQS message for file: s3://cash-release/{file_key} (Retry {retry_count}/{max_retries})")
            
            response = requests.post(
                'http://localhost:5001/ocr/process-file',
                json={'file_key': file_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'skipped':
                    logger.info(f"File s3://cash-release/{file_key} skipped as duplicate")
                    self.sqs_client.delete_message(
                        QueueUrl=self.queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    logger.info("Message deleted from queue")
                else:
                    logger.info(f"Successfully processed file: s3://cash-release/{file_key}")
                    self.sqs_client.delete_message(
                        QueueUrl=self.queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    logger.info("Message deleted from queue")
            elif response.status_code == 404:
                if retry_count < max_retries:
                    logger.warning(f"File not found s3://cash-release/{file_key}, retrying ({retry_count + 1}/{max_retries})")
                    return
                else:
                    logger.error(f"File not found after {max_retries} retries: s3://cash-release/{file_key}")
                    self.move_to_dlq(message)
            else:
                try:
                    error_detail = response.json().get('error', response.text)
                except ValueError:
                    error_detail = response.text
                logger.error(f"Failed to process file s3://cash-release/{file_key}: {error_detail}")
                self.move_to_dlq(message)
        
        except Exception as e:
            logger.error(f"Error processing SQS message: {e}")
            if retry_count < max_retries:
                return
            self.move_to_dlq(message)

    def start_sqs_polling(self):
        logger.info(f"Starting SQS polling for queue: {self.queue_url}")
        while True:
            try:
                response = self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20
                )
                
                messages = response.get('Messages', [])
                if not messages:
                    logger.debug("No messages in queue, continuing to poll")
                    continue
                
                for message in messages:
                    self.process_message(message)
            
            except Exception as e:
                logger.error(f"Error polling SQS queue: {e}")
                continue