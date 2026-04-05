#scripts/verify_clickhouse_tables.py
"""
Verify ClickHouse table configurations

This script checks your ClickHouse tables and shows their optimization settings.
Use this to verify that your asset definitions created the tables correctly.

Usage:
    python dagster_pipeline/scripts/verify_clickhouse_tables.py # Use default config (analytics database, all tables)
    python dagster_pipeline/scripts/verify_clickhouse_tables.py --database analytics # Override database only
    python dagster_pipeline/scripts/verify_clickhouse_tables.py --database analytics --table leads # Override both database and table
"""

import clickhouse_connect
import os
from dotenv import load_dotenv
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Load environment variables
load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================
CH_CONFIGS = {
    "host": os.getenv("SC_CH_DB_HOST"),
    "port": int(os.getenv("SC_CH_DB_PORT", "8443")),
    "username": os.getenv("SC_CH_DB_USER"),
    "password": os.getenv("SC_CH_DB_PASSWORD", ""),
    "database": "test",  # Default database to check
    "table_name": None,  # Default: None means check all tables
    #"secure": os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true"
}


def get_client():
    """Get ClickHouse client using CH_CONFIGS"""
    return clickhouse_connect.get_client(
        host=CH_CONFIGS["host"],
        port=CH_CONFIGS["port"],
        username=CH_CONFIGS["username"],
        password=CH_CONFIGS["password"],
    )


def get_tables_to_check(client, database_name: str, table_name: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Get list of tables to check based on database and optional table name.
    
    Args:
        client: ClickHouse client
        database_name: Name of the database
        table_name: Optional specific table name. If None, returns all tables in database.
    
    Returns:
        List of (database, table) tuples
    """
    if table_name:
        # Return only the specified table
        return [(database_name, table_name)]
    else:
        # Get all tables in the database
        query = f"""
            SELECT name 
            FROM system.tables 
            WHERE database = '{database_name}' 
            AND engine LIKE '%MergeTree%'
            ORDER BY name
        """
        result = client.query(query)
        return [(database_name, row[0]) for row in result.result_rows]


def get_table_info(client, database: str, table: str) -> Dict[str, Any]:
    """Get comprehensive table information"""
    
    # Get CREATE TABLE statement
    create_query = f"SHOW CREATE TABLE `{database}`.`{table}`"
    create_result = client.query(create_query)
    create_statement = create_result.result_rows[0][0] if create_result.result_rows else ""
    
    # Get partition info
    partition_query = f"""
        SELECT 
            partition,
            count() as parts,
            sum(rows) as rows,
            formatReadableSize(sum(bytes_on_disk)) as size
        FROM system.parts
        WHERE database = '{database}' AND table = '{table}' AND active
        GROUP BY partition
        ORDER BY partition DESC
        LIMIT 10
    """
    partition_result = client.query(partition_query)
    
    # Get table stats
    stats_query = f"""
        SELECT 
            sum(rows) as total_rows,
            formatReadableSize(sum(bytes_on_disk)) as total_size,
            count() as total_parts,
            formatReadableSize(sum(data_compressed_bytes)) as compressed_size
        FROM system.parts
        WHERE database = '{database}' AND table = '{table}' AND active
    """
    stats_result = client.query(stats_query)
    
    # Get engine info
    engine_query = f"""
        SELECT 
            engine,
            partition_key,
            sorting_key,
            primary_key,
            sampling_key
        FROM system.tables
        WHERE database = '{database}' AND name = '{table}'
    """
    engine_result = client.query(engine_query)
    
    return {
        "create_statement": create_statement,
        "partitions": partition_result.result_rows,
        "stats": stats_result.result_rows[0] if stats_result.result_rows else None,
        "engine_info": engine_result.result_rows[0] if engine_result.result_rows else None
    }


def print_table_analysis(database: str, table: str, info: Dict[str, Any]):
    """Print formatted table analysis"""
    
    print("\n" + "=" * 80)
    print(f"TABLE: {database}.{table}")
    print("=" * 80)
    
    # Engine info
    if info["engine_info"]:
        engine, partition_key, sorting_key, primary_key, sampling_key = info["engine_info"]
        
        print("\n🔧 ENGINE CONFIGURATION:")
        print(f"  Engine: {engine}")
        print(f"  ORDER BY: {sorting_key}")
        print(f"  PRIMARY KEY: {primary_key or '(default)'}")
        print(f"  PARTITION BY: {partition_key or '(none)'}")
        if sampling_key:
            print(f"  SAMPLE BY: {sampling_key}")
    
    # Statistics
    if info["stats"]:
        total_rows, total_size, total_parts, compressed_size = info["stats"]
        
        print("\n📊 TABLE STATISTICS:")
        print(f"  Total rows: {total_rows:,}")
        print(f"  Total size: {total_size}")
        print(f"  Compressed: {compressed_size}")
        print(f"  Total parts: {total_parts}")
        
        if total_rows > 0 and total_parts > 0:
            rows_per_part = total_rows / total_parts
            print(f"  Rows per part: {rows_per_part:,.0f}")
    
    # Partitions
    if info["partitions"]:
        print("\n📁 PARTITIONS (latest 10):")
        for partition, parts, rows, size in info["partitions"]:
            print(f"  {partition}: {rows:,} rows, {parts} parts, {size}")
    else:
        print("\n📁 PARTITIONS: No partitions (single partition table)")
    
    # Optimization recommendations
    print("\n💡 OPTIMIZATION ANALYSIS:")
    
    if info["stats"]:
        total_rows = info["stats"][0]
        total_parts = info["stats"][2]
        
        # Check part count
        if total_parts > 100:
            print(f"  ⚠️  High part count ({total_parts}) - consider running OPTIMIZE TABLE")
        elif total_parts < 10 and total_rows > 1000000:
            print(f"  ℹ️  Low part count ({total_parts}) - normal for new tables")
        else:
            print(f"  ✅ Part count ({total_parts}) is healthy")
        
        # Check partitioning
        if not info["engine_info"][1]:  # No partition key
            if total_rows > 10000000:
                print(f"  ⚠️  Large table ({total_rows:,} rows) without partitioning")
                print(f"      Consider adding PARTITION BY for better performance")
            else:
                print(f"  ✅ No partitioning needed for current size")
        else:
            print(f"  ✅ Partitioned table - good for large datasets")
    
    # Check engine
    if info["engine_info"]:
        engine = info["engine_info"][0]
        if "Replacing" in engine:
            print(f"  ✅ Using ReplacingMergeTree - automatic deduplication")
            print(f"      Remember to use FINAL in queries for deduplicated results")
        elif "Summing" in engine:
            print(f"  ✅ Using SummingMergeTree - automatic aggregation")
        elif engine == "MergeTree":
            print(f"  ✅ Using MergeTree - standard sorted storage")
    
    print("\n" + "=" * 80)


def main():
    """Main verification function"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Verify ClickHouse table configurations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --database analytics
  %(prog)s --database analytics --table leads
  %(prog)s -d test -t amt_accounts_test
  
  Or run with default config (no arguments needed):
  %(prog)s
        """
    )
    parser.add_argument(
        '-d', '--database',
        help=f'Database name to check (default: {CH_CONFIGS["database"]})'
    )
    parser.add_argument(
        '-t', '--table',
        help='Specific table name (optional). If not provided, checks all tables in database.'
    )
    
    args = parser.parse_args()
    
    # Use command-line args if provided, otherwise use CH_CONFIGS
    database = args.database if args.database else CH_CONFIGS["database"]
    table = args.table if args.table else CH_CONFIGS["table_name"]
    
    print("=" * 80)
    print("CLICKHOUSE TABLE VERIFICATION")
    print("=" * 80)
    print(f"\nDatabase: {database}")
    if table:
        print(f"Table: {table}")
    else:
        print("Checking all tables in database...")
    
    try:
        client = get_client()
        
        # Get tables to check based on arguments or config
        tables_to_check = get_tables_to_check(client, database, table)
        
        if not tables_to_check:
            print(f"\n❌ No tables found in database '{database}'")
            if table:
                print(f"   Table '{table}' does not exist or is not a MergeTree table")
            return
        
        print(f"\nFound {len(tables_to_check)} table(s) to check\n")
        
        for database, table in tables_to_check:
            try:
                info = get_table_info(client, database, table)
                print_table_analysis(database, table, info)
            except Exception as e:
                print(f"\n❌ Error checking {database}.{table}: {e}")
        
        print("\n✅ Verification complete!")
        
    except Exception as e:
        print(f"\n❌ Failed to connect to ClickHouse: {e}")
        print("\nMake sure to set environment variables:")
        print("  SC_CH_DB_HOST")
        print("  SC_CH_DB_PORT")
        print("  SC_CH_DB_USER")
        print("  SC_CH_DB_PASSWORD")


if __name__ == "__main__":
    main()