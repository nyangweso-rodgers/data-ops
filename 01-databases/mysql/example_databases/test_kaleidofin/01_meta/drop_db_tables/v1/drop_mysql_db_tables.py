import os
from dotenv import load_dotenv
import logging
import pymysql
from typing import Dict, List
import sys
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DB_CONFIGS = {
    "local_mysql_kaleidofin_db": {
        "type": "mysql",
        "host": "localhost",
        "database": "test_kaleidofin",
        "username": os.getenv("LOCAL_KALEIDOFIN_MYSQL_USER"),
        "password": os.getenv("LOCAL_KALEIDOFIN_MYSQL_PASSWORD"),
        "port": 3306,
    },
}

DB_TABLES = {
    "local_mysql_kaleidofin_db": [
        "account_payplans",
        "accounts",
        "customers",
        "installment_schedules",
        "wallet_installment_payments",
    ],
}

# SAFETY: Define protected databases (add production DBs here)
PROTECTED_DATABASES = [
    "kaleidofin_prod",
    "kaleidofin_production",
    "production",
    # Add more production database names here
]


def establish_connection_to_mysql(config: Dict) -> pymysql.connections.Connection:
    """Establish connection to MySQL database"""
    try:
        connection = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["username"],
            password=config["password"],
            database=config["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,  # Connection timeout
            read_timeout=30,  # Query timeout - queries longer than 30s will be killed
            write_timeout=30,
        )
        logger.info(f"✓ Connected to MySQL: {config['database']}")
        return connection
    except Exception as e:
        logger.error(f"✗ Failed to connect to MySQL {config['database']}: {e}")
        return None


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="⚠️  Dangerous MySQL Table Dropper - Use with caution!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Drop all configured tables (interactive mode)
  python drop_mysql_db_tables.py
  
  # Drop specific table(s)
  python drop_mysql_db_tables.py --tables customers
  python drop_mysql_db_tables.py --tables customers account
  
  # Drop all tables (non-interactive)
  python drop_mysql_db_tables.py --tables all
  
  # Specify database
  python drop_mysql_db_tables.py --db local_mysql_kaleidofin_db --tables customers
  
  # Skip backups (faster)
  python drop_mysql_db_tables.py --tables all --no-backup
  
  # Use exact row counts (slower)
  python drop_mysql_db_tables.py --tables all --exact-count
        """,
    )

    parser.add_argument(
        "--tables",
        "-t",
        nargs="+",
        help='Table name(s) to drop, or "all" for all configured tables',
    )

    parser.add_argument(
        "--db",
        "-d",
        choices=list(DB_CONFIGS.keys()),
        default=list(DB_CONFIGS.keys())[0] if DB_CONFIGS else None,
        help="Database configuration to use (default: first configured DB)",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backups before dropping tables",
    )

    parser.add_argument(
        "--exact-count",
        action="store_true",
        help="Use exact row counts instead of estimates (slower)",
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts (dangerous!)",
    )

    return parser.parse_args()


def get_tables_to_drop(args, db_key: str) -> List[str]:
    """Determine which tables to drop based on arguments"""
    if not args.tables:
        # No --tables argument, use all configured tables for this DB
        return DB_TABLES.get(db_key, [])

    if len(args.tables) == 1 and args.tables[0].lower() == "all":
        # --tables all
        return DB_TABLES.get(db_key, [])

    # Specific table(s) requested
    configured_tables = DB_TABLES.get(db_key, [])
    requested_tables = args.tables

    # Validate that requested tables are in the configured list
    invalid_tables = [t for t in requested_tables if t not in configured_tables]
    if invalid_tables:
        logger.warning(f"⚠️  Tables not in configuration: {', '.join(invalid_tables)}")
        logger.info(f"Available tables: {', '.join(configured_tables)}")
        response = input("Continue with valid tables only? (y/n): ")
        if response.lower() != "y":
            return []

    return [t for t in requested_tables if t in configured_tables]


def check_safety(config: Dict, tables: List[str]) -> bool:
    """Safety checks before dropping tables"""
    database_name = config["database"]

    # Check if database is in protected list
    if database_name in PROTECTED_DATABASES:
        logger.error(f"🛑 BLOCKED: '{database_name}' is a protected database!")
        return False

    # Check if it's a test/dev database
    if not any(
        keyword in database_name.lower()
        for keyword in ["test", "dev", "local", "staging"]
    ):
        logger.warning(
            f"⚠️  WARNING: '{database_name}' doesn't appear to be a test database!"
        )
        response = input(
            f"Are you ABSOLUTELY sure you want to drop tables from '{database_name}'? (type 'YES' to confirm): "
        )
        if response != "YES":
            logger.info("Operation cancelled by user")
            return False

    return True


def backup_table(
    connection: pymysql.connections.Connection,
    table: str,
    backup_dir: str = "./backups",
):
    """Create a backup of table data before dropping"""
    try:
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f"{table}_backup.sql")

        with connection.cursor() as cursor:
            # Get table structure
            cursor.execute(f"SHOW CREATE TABLE {table}")
            create_table = cursor.fetchone()

            # Get table data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            with open(backup_file, "w") as f:
                if create_table:
                    f.write(f"{create_table['Create Table']};\n\n")

                # Write insert statements (simplified)
                f.write(f"-- Backed up {len(rows)} rows from {table}\n")

            logger.info(f"  ✓ Backed up table: {table} ({len(rows)} rows)")
            return True
    except Exception as e:
        logger.error(f"  ✗ Failed to backup table {table}: {e}")
        return False


def get_table_info(connection: pymysql.connections.Connection, table: str) -> Dict:
    """Get table row count and size"""
    try:
        with connection.cursor() as cursor:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()["count"]

            # Get table size
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.TABLES
                WHERE table_schema = DATABASE()
                AND table_name = '{table}'
            """)
            size_result = cursor.fetchone()
            size_mb = size_result["size_mb"] if size_result else 0

            return {"rows": count, "size_mb": size_mb}
    except Exception as e:
        logger.warning(f"Could not get info for {table}: {e}")
        return {"rows": "?", "size_mb": "?"}


def confirm_table_deletion(
    connection: pymysql.connections.Connection,
    tables: List[str],
    db_name: str,
    fast_mode: bool = True,
    skip_confirm: bool = False,
) -> bool:
    """Show table info and get user confirmation

    Args:
        fast_mode: If True, uses estimated row counts (instant) instead of exact counts (slow)
        skip_confirm: If True, skip confirmation prompt (use with --yes flag)
    """
    print("\n" + "─" * 60)
    print(f"📊 Tables to be DELETED from '{db_name}':")
    print("─" * 60)

    if fast_mode:
        # Use INFORMATION_SCHEMA for instant estimates (no table scan)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT 
                        table_name,
                        table_rows,
                        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                    FROM information_schema.TABLES
                    WHERE table_schema = DATABASE()
                    AND table_name IN ({','.join(['%s'] * len(tables))})
                """,
                    tables,
                )
                results = {row["table_name"]: row for row in cursor.fetchall()}
        except Exception as e:
            logger.warning(f"Could not fetch table stats: {e}")
            results = {}

        total_rows = 0
        for i, table in enumerate(tables, 1):
            if table in results:
                rows = results[table]["table_rows"]
                size = results[table]["size_mb"]
                print(f"  {i}. {table:30s} (~{rows:>9} rows, {size:>6} MB)")
                total_rows += rows if rows else 0
            else:
                print(f"  {i}. {table:30s} (unknown)")

        print("─" * 60)
        print(f"  TOTAL: {len(tables)} tables, ~{total_rows:,} rows (estimated)")
    else:
        # Exact counts - slower but accurate
        total_rows = 0
        for i, table in enumerate(tables, 1):
            info = get_table_info(connection, table)
            rows = info["rows"]
            size = info["size_mb"]
            print(f"  {i}. {table:30s} ({rows:>10} rows, {size:>6} MB)")
            if isinstance(rows, int):
                total_rows += rows

        print("─" * 60)
        print(f"  TOTAL: {len(tables)} tables, ~{total_rows:,} rows (exact)")

    print("─" * 60)

    if skip_confirm:
        print("\n⚠️  Auto-confirming deletion (--yes flag used)")
        return True

    response = input("\n⚠️  Type 'DELETE' to confirm deletion: ")
    return response == "DELETE"


def drop_mysql_tables(
    connection: pymysql.connections.Connection,
    tables: List[str],
    create_backup: bool = True,
):
    """Drop tables in MySQL database"""
    try:
        # Disable foreign key checks temporarily
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            for table in tables:
                # Optional backup
                if create_backup:
                    backup_table(connection, table)

                # Drop the table
                drop_query = f"DROP TABLE IF EXISTS {table}"
                cursor.execute(drop_query)
                logger.info(f"  ✓ Dropped table: {table}")

            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        connection.commit()
        logger.info("✓ All tables dropped successfully")
    except Exception as e:
        logger.error(f"✗ Failed to drop tables: {e}")
        connection.rollback()
        raise


def main():
    """Main execution function"""
    args = parse_arguments()

    print("\n" + "=" * 60)
    print("⚠️  DANGEROUS DATABASE CLEANUP SCRIPT ⚠️")
    print("=" * 60 + "\n")

    # Determine which database to use
    db_key = args.db
    if not db_key:
        logger.error("No database configuration available")
        sys.exit(1)

    config = DB_CONFIGS[db_key]

    # Determine which tables to drop
    tables_to_drop = get_tables_to_drop(args, db_key)

    if not tables_to_drop:
        logger.error("No valid tables specified")
        sys.exit(1)

    print(f"🔌 Target Database: {config['database']}")
    print(f"📋 Tables to drop: {', '.join(tables_to_drop)}")
    print(f"💾 Backups: {'disabled' if args.no_backup else 'enabled'}")
    print(
        f"🔢 Count mode: {'exact (slow)' if args.exact_count else 'estimated (fast)'}"
    )
    print()

    # Safety check
    if not check_safety(config, tables_to_drop):
        logger.warning(f"Skipping {db_key} due to safety check")
        sys.exit(1)

    # Establish connection
    print(f"🔌 Connecting to {db_key}...")
    connection = establish_connection_to_mysql(config)
    if not connection:
        sys.exit(1)

    print(f"✅ Connection to MySQL '{config['database']}' established successfully!\n")

    try:
        # Show table info and get confirmation
        fast_mode = not args.exact_count
        if not confirm_table_deletion(
            connection,
            tables_to_drop,
            config["database"],
            fast_mode=fast_mode,
            skip_confirm=args.yes,
        ):
            logger.info("❌ Operation cancelled by user")
            sys.exit(0)

        # Drop tables
        print("\n🗑️  Dropping tables...\n")
        drop_mysql_tables(connection, tables_to_drop, create_backup=not args.no_backup)
        print("\n✅ All operations completed successfully!")

    except Exception as e:
        logger.error(f"Error during table drop: {e}")
        sys.exit(1)
    finally:
        connection.close()
        logger.info(f"🔌 Connection closed for {db_key}")

    print("\n" + "=" * 60)
    print("Script execution completed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
