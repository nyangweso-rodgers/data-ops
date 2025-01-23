import pandas as pd
import psycopg2

# Define the connection parameters
host = "localhost"  # Replace with your host if it's remote
port = 5432         # Default PostgreSQL port
dbname = "customers"
user = "postgres"
password = "mypassword"

try:
    # Establish the connection
    connection = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    print("Connection to the database was successful!")

    # Create a cursor to interact with the database
    cursor = connection.cursor()

    # Write your SQL query
    query = "SELECT * FROM customers LIMIT 10;"  
    data = pd.read_sql_query(query, connection)
    
    # Print the data as a DataFrame
    print("Query results:")
    print(data)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the cursor and connection
    if cursor:
        cursor.close()
    if connection:
        connection.close()
        print("Connection closed.")
