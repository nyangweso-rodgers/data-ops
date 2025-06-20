# services/s3_service.py
import boto3
from config.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, SUPPORTED_EXTENSIONS
import logging

logger = logging.getLogger(__name__)

# Initialize S3 client and verify connection
try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    # Test S3 connection by listing buckets
    s3_client.list_buckets()
    logger.info("Successfully connected to AWS S3")
except Exception as e:
    logger.error(f"Failed to connect to AWS S3: {e}")
    raise

def download_file_from_s3(bucket, file_key, temp_file):
    try:
        s3_client.download_file(bucket, file_key, temp_file)
        logger.info(f"Successfully downloaded {file_key} from bucket {bucket} to {temp_file}")
    except Exception as e:
        logger.error(f"Error downloading file {file_key} from S3 bucket {bucket}: {e}")
        raise

def list_files_in_folder(bucket, prefix):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files = [
            obj['Key'] for obj in response.get('Contents', [])
            if any(obj['Key'].lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)
        ]
        
        # Handle pagination
        while response.get('IsTruncated', False):
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                ContinuationToken=response['NextContinuationToken']
            )
            files.extend([
                obj['Key'] for obj in response.get('Contents', [])
                if any(obj['Key'].lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)
            ])
        
        logger.info(f"Successfully listed {len(files)} supported files in {bucket}/{prefix}")
        return files
    except Exception as e:
        logger.error(f"Error listing files in {bucket}/{prefix}: {e}")
        raise