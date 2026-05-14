import os
import psycopg2
import json

# Configure logging
import logging
from rich.logging import RichHandler

from flask.cli import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RichHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

POSTGRES_DB_CONFIG = {
    "host": os.getenv("LOCAL_POSTGRES_DAGSTER_DB_HOST"),
    "database": os.getenv("LOCAL_POSTGRES_DAGSTER_DB_NAME"),
    "username": os.getenv("LOCAL_POSTGRES_DAGSTER_DB_USER"),
    "password": os.getenv("LOCAL_POSTGRES_DAGSTER_DB_PASSWORD"),
    "schema": "dagster",
    "port": 5432,
}

POSTGRES_DB_TABLES = ["kvs"]


def establish_connection_to_postgres(config):
    """Establish connection to PostgreSQL database"""
    try:
        connection = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["username"],
            password=config["password"],
            database=config["database"],
            connect_timeout=10,
            options="-c statement_timeout=30000",
        )

        # Set the search_path to use the specified schema
        schema = config.get("schema", "public")
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema}")

        logger.info(
            f"✓ Connected to PostgreSQL: {config['database']} (schema: {schema})"
        )
        return connection
    except Exception as e:
        logger.error(f"✗ Failed to connect to PostgreSQL {config['database']}: {e}")
        return None


def select_postgres_db_tables(connection, table_name, schema="public"):
    """
    Select and display table data in a clean format

    Args:
        connection: PostgreSQL connection object
        table_name: Name of the table to query
        schema: Schema name (default: public)
    """
    if not connection:
        logger.error("No database connection provided")
        return

    query = f"SELECT * FROM {schema}.{table_name} ORDER BY key;"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

            logger.info(f"\nTable: {schema}.{table_name}")
            logger.info(f"Total rows: {len(rows)}\n")

            # Print header
            print(f"{'id':<10} {'key':<60} {'value'}")
            print("-" * 150)

            # Print rows
            for row in rows:
                row_dict = dict(zip(column_names, row))
                id_val = row_dict.get("id", "")
                key_val = row_dict.get("key", "")
                value_val = row_dict.get("value", "")

                # Format value if it's JSON
                if isinstance(value_val, (dict, str)):
                    try:
                        if isinstance(value_val, str):
                            value_dict = json.loads(value_val)
                        else:
                            value_dict = value_val

                        # Extract version and last_value for display
                        version = value_dict.get("version", "")
                        last_value = value_dict.get("last_value", "")
                        value_display = (
                            f'{{"version": "{version}", "last_value": "{last_value}"}}'
                        )
                    except:
                        value_display = str(value_val)[:100]
                else:
                    value_display = str(value_val)[:100]

                print(f"{id_val:<10} {key_val:<60} {value_display}")

    except Exception as e:
        logger.error(f"Error querying table {table_name}: {e}")


def delete_record_by_id(connection, record_id, schema="public"):
    """
    Delete a record from kvs table by ID

    Args:
        connection: PostgreSQL connection object
        record_id: ID of the record to delete
        schema: Schema name (default: public)

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        with connection.cursor() as cursor:
            # First, get the record to show what will be deleted
            cursor.execute(
                f"SELECT id, key FROM {schema}.kvs WHERE id = %s", (record_id,)
            )
            record = cursor.fetchone()

            if not record:
                logger.error(f"❌ No record found with ID: {record_id}")
                return False

            # Show what will be deleted
            print("\n" + "=" * 80)
            print(f"⚠️  ABOUT TO DELETE:")
            print(f"   ID:  {record[0]}")
            print(f"   Key: {record[1]}")
            print("=" * 80)

            # Final confirmation
            confirm = input("\n🔴 Type 'DELETE' to confirm deletion: ").strip()

            if confirm == "DELETE":
                cursor.execute(f"DELETE FROM {schema}.kvs WHERE id = %s", (record_id,))
                connection.commit()
                logger.info(f"✅ Successfully deleted record ID: {record_id}")
                logger.info(f"   This will trigger a FULL SYNC for: {record[1]}")
                return True
            else:
                logger.info("❌ Deletion cancelled (confirmation not matched)")
                return False

    except Exception as e:
        logger.error(f"❌ Error deleting record: {e}")
        connection.rollback()
        return False


def main():
    """Main function to run the script"""
    logger.info("Starting PostgreSQL table query script")

    # Establish connection
    connection = establish_connection_to_postgres(POSTGRES_DB_CONFIG)

    if connection:
        try:
            schema = POSTGRES_DB_CONFIG.get("schema", "public")

            # Query the kvs table
            select_postgres_db_tables(connection, "kvs", schema)

            # Ask if user wants to delete
            print("\n" + "=" * 80)
            delete_prompt = (
                input("\n🗑️  Do you need to DELETE a record? (yes/no): ")
                .strip()
                .lower()
            )

            if delete_prompt in ["yes", "y"]:
                record_id = input("\n📝 Enter the ID to delete: ").strip()

                try:
                    record_id = int(record_id)
                    delete_record_by_id(connection, record_id, schema)
                except ValueError:
                    logger.error("❌ Invalid ID. Please enter a valid number.")
            else:
                logger.info("No deletion requested.")

        except Exception as e:
            logger.error(f"Error during table query: {e}")
        finally:
            connection.close()
            logger.info("\nDatabase connection closed")
    else:
        logger.error("Failed to establish database connection")


if __name__ == "__main__":
    main()
