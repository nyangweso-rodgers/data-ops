import psycopg2
from config.settings import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
import logging

logger = logging.getLogger(__name__)

def save_to_db(file_key, extracted_text, has_prohibited_items):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO extracted_text_v2 (file_name, extracted_text, has_prohibited_items, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (file_key, extracted_text, has_prohibited_items)
        )
        record_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        return record_id
    except Exception as e:
        logger.error(f"Error saving to database for {file_key}: {e}")
        raise