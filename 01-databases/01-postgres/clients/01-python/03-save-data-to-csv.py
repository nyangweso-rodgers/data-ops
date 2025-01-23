import csv
import psycopg2

# Connection parameters
host = "localhost"
port = 5432
dbname = "customers"
user = "postgres"
password = "mypassword"

try:
    # Establish connection
    connection = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    print("Connection to the database was successful!")

    # Create a cursor and execute the query
    cursor = connection.cursor()
    query = "SELECT * FROM customers LIMIT 10;"
    cursor.execute(query)

    # Fetch results
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]

    # Write to CSV
    with open("customers.csv", "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(colnames)  # Write header
        csvwriter.writerows(rows)     # Write data

    print("Results have been written to 'customers.csv'.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    if cursor:
        cursor.close()
    if connection:
        connection.close()
        print("Connection closed.")
