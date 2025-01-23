import psycopg2
from psycopg2 import sql

def connect_to_postgres_db(host, database, user, password, port=5432):
    try:
        # # Establish the connection
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        print("Successfully connected to the database!")
        
        # Create a cursor to execute queries
        cursor = connection.cursor()
        
        # Example query
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("PostgreSQL version:", db_version)
        
        # Close the cursor and connection
        cursor.close()
        connection.close()
        print("Connection closed.")
        
    except Exception as e:
        print("Error while connecting to PostgreSQL:", e)
        
# Connection details
if __name__ == "__main__":
    # Replace these with your database details
    POSTGRES_HOST = "localhost"  # or the IP of your Docker container / remote server
    POSTGRES_DB = "customers"
    POSTGRES_USER = "postgres"
    POSTGRES_PASSWORD = "<password>"
    POSTGRES_PORT = 5432

connect_to_postgres_db(POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_PORT)