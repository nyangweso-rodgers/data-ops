from dagster import job, op, Out
import mysql.connector
from sqlalchemy import create_engine
import os

# Op to fetch data from MySQL
@op(out=Out(list))
def fetch_from_mysql(context):
    # Get MySQL connection details from environment variables
    mysql_host = os.getenv("MYSQL_HOST", "mysql-db")
    mysql_user = os.getenv("MYSQL_USER", "mysql_user")
    mysql_password = os.getenv("MYSQL_PASSWORD", "mysql_password")
    mysql_db = os.getenv("MYSQL_DB", "source_db")

    # Connect to MySQL
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_db
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, created_at FROM users")
        data = cursor.fetchall()
        context.log.info(f"Fetched {len(data)} rows from MySQL")
        cursor.close()
        conn.close()
        return data
    except Exception as e:
        context.log.error(f"Error fetching from MySQL: {e}")
        raise

# Op to load data into PostgreSQL
@op
def load_to_postgres(context, data):
    # Get PostgreSQL connection details from environment variables
    pg_user = os.getenv("PG_DAGSTER_USER", "dagster")
    pg_password = os.getenv("PG_DAGSTER_PASSWORD", "mypassword")
    pg_host = os.getenv("PG_DAGSTER_HOST", "postgres-db")
    pg_port = os.getenv("PG_DAGSTER_PORT", "5432")
    pg_db = os.getenv("PG_DAGSTER_DB", "dagster")

    # Create SQLAlchemy engine
    connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    engine = create_engine(connection_string)

    # Load data into PostgreSQL
    try:
        with engine.connect() as conn:
            # Truncate table for simplicity (modify as needed)
            conn.execute("TRUNCATE TABLE users")
            for row in data:
                conn.execute(
                    """
                    INSERT INTO users (id, username, email, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (row["id"], row["username"], row["email"], row["created_at"])
                )
            conn.commit()
            context.log.info(f"Loaded {len(data)} rows into PostgreSQL")
    except Exception as e:
        context.log.error(f"Error loading to PostgreSQL: {e}")
        raise

# Define the job
@job
def mysql_to_postgres():
    data = fetch_from_mysql()
    load_to_postgres(data)

if __name__ == "__main__":
    mysql_to_postgres.execute_in_process()