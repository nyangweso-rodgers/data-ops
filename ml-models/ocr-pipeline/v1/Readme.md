# OCR Pipeline

# Deployment

# S3 Event Notifications + SQS + Flask Service

- A queue-based approach that:
  1. S3 sends notifications to an SQS queue when files are uploaded
  2. Flask service polls the SQS queue for new messages
  3. Process files as messages are received

# Workflow

- The SQS service polls `test-ocr-queue` queue, and extracts `file_key` (e.g., `dev-rodgers/test-receipt-1+-copy.jpg`) from the message.
- It sends a `POST` request to `http://localhost:5001/ocr/process-file` (Flask endpoint).
- The Flask app calls `download_file_from_s3` in `s3_service.py` with the `file_key`
