import os

# AWS configurations
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')  # Fixed S3 bucket name
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
SQS_DLQ_URL = os.getenv('SQS_DLQ_URL')  # Dead Letter Queue URL

# Database configurations
DB_NAME = os.getenv('ep_stage_db')
DB_USER = os.getenv('ep_stage_db_user')
DB_PASSWORD = os.getenv('ep_stage_db_password')
DB_HOST = os.getenv('ep_stage_db_host')
DB_PORT = os.getenv('ep_stage_db_port', '5432')

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.png', '.pdf', '.jpeg', '.jpg'}