import os
import pymysql
from pymysql import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================
DB_CONFIGS = {
    "host": "localhost",
    "port": 3306,
    "user": os.getenv("LOCAL_MYSQL_DB_USER"),
    "password": os.getenv("LOCAL_MYSQL_DB_PASSWORD", ""),
    "database": os.getenv("LOCAL_MYSQL_DB_NAME"),
}


def get_mysql_db_client():
    """Return database configuration"""
    return DB_CONFIGS


def establish_connection_mysql_db():
    """Establish and return MySQL database connection"""
    try:
        connection = pymysql.connect(
            host=DB_CONFIGS["host"],
            port=DB_CONFIGS["port"],
            user=DB_CONFIGS["user"],
            password=DB_CONFIGS["password"],
            database=DB_CONFIGS["database"],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print(f"✓ Successfully connected to database: {DB_CONFIGS['database']}")
        return connection
    except Error as e:
        print(f"✗ Error connecting to MySQL database: {e}")
        return None


def get_all_tables(connection):
    """Retrieve all table names from the database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            return tables
    except Error as e:
        print(f"✗ Error retrieving tables: {e}")
        return []


def delete_all_tables(connection, database_name):
    """Delete all tables in the database after confirmation"""
    tables = get_all_tables(connection)
    
    if not tables:
        print(f"No tables found in database '{database_name}'")
        return
    
    print(f"\n{'='*70}")
    print(f"⚠️  WARNING: YOU ARE ABOUT TO DELETE ALL TABLES IN DATABASE '{database_name}'")
    print(f"{'='*70}")
    print(f"\nTables to be deleted ({len(tables)}):")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table}")
    
    print(f"\n{'='*70}")
    confirmation = input(f"Type 'YES' to proceed with deletion: ").strip()
    
    if confirmation != "YES":
        print("\n✗ Operation cancelled. No tables were deleted.")
        return
    
    print("\n🗑️  Proceeding with table deletion...\n")
    
    try:
        with connection.cursor() as cursor:
            # Disable foreign key checks to avoid constraint issues
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            deleted_count = 0
            failed_tables = []
            
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                    print(f"  ✓ Deleted table: {table}")
                    deleted_count += 1
                except Error as e:
                    print(f"  ✗ Failed to delete table '{table}': {e}")
                    failed_tables.append(table)
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            connection.commit()
            
            print(f"\n{'='*70}")
            print(f"✓ Deletion complete: {deleted_count}/{len(tables)} tables deleted")
            
            if failed_tables:
                print(f"✗ Failed to delete {len(failed_tables)} table(s): {', '.join(failed_tables)}")
            print(f"{'='*70}")
            
    except Error as e:
        print(f"\n✗ Error during table deletion: {e}")
        connection.rollback()


def main():
    """Main function to execute the table deletion process"""
    config = get_mysql_db_client()
    database_name = config.get("database")
    
    if not database_name:
        print("✗ Error: Database name not configured in environment variables")
        return
    
    connection = establish_connection_mysql_db()
    
    if connection:
        try:
            delete_all_tables(connection, database_name)
        finally:
            connection.close()
            print("\n✓ Database connection closed")
    else:
        print("✗ Failed to establish database connection")


if __name__ == "__main__":
    main()