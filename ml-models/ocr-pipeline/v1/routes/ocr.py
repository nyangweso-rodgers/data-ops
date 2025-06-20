from flask import Blueprint, request, jsonify
from services.s3_service import download_file_from_s3, list_files_in_folder
from services.textract_service import extract_text_from_file
from services.db_service import save_to_db
from werkzeug.utils import secure_filename
from config.settings import S3_BUCKET, SUPPORTED_EXTENSIONS
import logging
import os
import json
import psycopg2
from config.settings import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

logger = logging.getLogger(__name__)
logger.info("Loading routes/ocr.py module")

try:
    ocr_bp = Blueprint('ocr', __name__, url_prefix='/ocr')
    logger.info("Blueprint 'ocr' created successfully")
except Exception as e:
    logger.error("Failed to create Blueprint 'ocr': %s", str(e))
    raise

def check_duplicate(file_key):
    logger.info(f"Checking duplicate for s3://{S3_BUCKET}/{file_key}")
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM extracted_text_v2 WHERE file_name = %s", (file_key,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"Error checking duplicate for s3://{S3_BUCKET}/{file_key}: {e}")
        raise

@ocr_bp.route('/process-file', methods=['POST'])
def process_file():
    logger.info("Registering /process-file route")
    try:
        data = request.get_json()
        if not data or 'file_key' not in data:
            logger.error("Missing file_key in request payload")
            return jsonify({'error': 'Missing file_key'}), 400

        file_key = data['file_key'].strip()
        logger.info(f"Received request to process file: s3://{S3_BUCKET}/{file_key}")

        is_duplicate = check_duplicate(file_key)
        if is_duplicate:
            logger.warning(f"Duplicate file detected: s3://{S3_BUCKET}/{file_key}")
            # Update database with duplicate flag
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE extracted_text_v2 SET duplicate_receipt = TRUE WHERE file_name = %s",
                (file_key,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'status': 'skipped', 'file_key': file_key, 'reason': 'duplicate'}), 200

        basename = os.path.basename(file_key)
        has_extension = any(basename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)
        has_any_extension = '.' in basename

        logger.info(f"File extension check for s3://{S3_BUCKET}/{file_key} - has supported extension: {has_extension}, has any extension: {has_any_extension}")

        if has_any_extension and not has_extension:
            return jsonify({'error': f'Unsupported file type. Supported extensions: {SUPPORTED_EXTENSIONS}'}), 400

        os.makedirs('/tmp', exist_ok=True)

        filename = os.path.basename(file_key)
        temp_file = f"/tmp/{secure_filename(filename)}"
        
        # Remove URL encoding, pass raw file_key to S3
        download_file_from_s3(S3_BUCKET, file_key, temp_file)

        extracted_json = extract_text_from_file(temp_file)
        extracted_data = json.loads(extracted_json)

        has_prohibited_items = extracted_data.get('has_prohibited_items', False)

        record_id = save_to_db(file_key, extracted_json, has_prohibited_items)

        if os.path.exists(temp_file):
            os.remove(temp_file)

        logger.info(f"Successfully processed file: s3://{S3_BUCKET}/{file_key}, record ID: {record_id}")
        return jsonify({
            'status': 'success',
            'file_key': file_key,
            'extracted_data': extracted_data,
            'record_id': record_id
        }), 200

    except Exception as e:
        logger.error(f"Error processing file s3://{S3_BUCKET}/{file_key if 'file_key' in locals() else 'unknown'}: {e}")
        if '404' in str(e):  # Handle S3 404 specifically
            return jsonify({'error': 'File not found in S3', 'file_key': file_key if 'file_key' in locals() else None}), 404
        return jsonify({'error': str(e)}), 500

@ocr_bp.route('/process-all-files', methods=['POST'])
def process_all_files():
    logger.info("Registering /process-all-files route")
    try:
        logger.info("Received request to process all files in dev/employee-documents/")
        prefix = 'dev/employee-documents/'
        files = list_files_in_folder(S3_BUCKET, prefix)

        if not files:
            logger.info("No supported files found in dev/employee-documents/")
            return jsonify({'status': 'success', 'message': 'No supported files found in dev/employee-documents/'}), 200

        results = []
        for file_key in files:
            try:
                logger.info(f"Processing file: s3://{S3_BUCKET}/{file_key}")

                os.makedirs('/tmp', exist_ok=True)

                filename = os.path.basename(file_key)
                temp_file = f"/tmp/{secure_filename(filename)}"
                
                # Remove URL encoding, pass raw file_key to S3
                download_file_from_s3(S3_BUCKET, file_key, temp_file)

                extracted_json = extract_text_from_file(temp_file)
                extracted_data = json.loads(extracted_json)

                has_prohibited_items = extracted_data.get('has_prohibited_items', False)

                record_id = save_to_db(file_key, extracted_json, has_prohibited_items)

                results.append({
                    'file_key': file_key,
                    'record_id': record_id,
                    'status': 'success'
                })

                if os.path.exists(temp_file):
                    os.remove(temp_file)
                logger.info(f"Successfully processed file: s3://{S3_BUCKET}/{file_key}, record ID: {record_id}")
            except Exception as e:
                logger.error(f"Error processing s3://{S3_BUCKET}/{file_key}: {e}")
                results.append({
                    'file_key': file_key,
                    'record_id': None,
                    'status': 'failed',
                    'error': str(e)
                })

        logger.info(f"Completed processing {len(files)} files: {sum(1 for r in results if r['status'] == 'success')} successful, {sum(1 for r in results if r['status'] == 'failed')} failed")
        return jsonify({
            'status': 'success',
            'processed_files': results,
            'total_files': len(files),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'failed')
        }), 200

    except Exception as e:
        logger.error(f"Error processing all files: {e}")
        return jsonify({'error': str(e)}), 500

@ocr_bp.route('/health', methods=['GET'])
def health_check():
    logger.info("Serving /health route")
    return jsonify({'status': 'healthy'}), 200

logger.info("Finished loading routes/ocr.py module")