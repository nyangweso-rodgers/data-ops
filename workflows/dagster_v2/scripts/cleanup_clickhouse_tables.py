#!/usr/bin/env python3
"""
Local ClickHouse Cleanup Test Script

This script tests the deduplication logic locally before integrating into Dagster.
It connects to ClickHouse, analyzes partitions, and can perform cleanup.

Usage:
    # Dry run (safe - just reports, no changes)
    python test_cleanup_locally.py --database sales-service --table leads_v2 --dry-run
    
    # Actual cleanup (use with caution!)
    python test_cleanup_locally.py --database sales-service --table leads_v2
    
    # Cleanup specific partition only
    python test_cleanup_locally.py --database sales-service --table leads_v2 --partition 202412
    
    # Adjust thresholds
    python test_cleanup_locally.py --database sales-service --table leads_v2 --min-duplicates 50 --min-pct 0.5
"""

import clickhouse_connect
import os
from dotenv import load_dotenv
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

# Load environment variables
load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """ClickHouse connection configuration"""
    
    def __init__(self):
        self.host = os.getenv("SC_CH_DB_HOST")
        self.port = int(os.getenv("SC_CH_DB_PORT", "8443"))
        self.username = os.getenv("SC_CH_DB_USER")
        self.password = os.getenv("SC_CH_DB_PASSWORD", "")
        self.secure = True
        self.verify = True
    
    def get_client(self):
        """Create ClickHouse client"""
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            secure=self.secure,
            verify=self.verify,
        )


# ============================================================================
# PARTITION ANALYSIS
# ============================================================================
def get_partitions_in_window(
    client,
    database: str,
    table: str,
    partition_column: str,
    partition_format: str,
    window_days: Optional[int]  # ← Now accepts None
) -> List[str]:
    """Get list of partitions within cleanup window"""
    
    # Query existing partitions
    query = f"""
        SELECT DISTINCT partition
        FROM system.parts
        WHERE database = %(database)s 
          AND table = %(table)s
          AND active = 1
        ORDER BY partition DESC
    """
    
    result = client.query(
        query,
        parameters={"database": database, "table": table}
    )
    
    all_partitions = [row[0] for row in result.result_rows]
    
    # If window_days is None, return ALL partitions
    if window_days is None:
        print(f"\n🔍 Analyzing ALL partitions (no date filter)...")
        print(f"   ✅ Found {len(all_partitions)} total partitions")
        return all_partitions
    
    # Otherwise, filter by date window
    print(f"\n🔍 Identifying partitions in last {window_days} days...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=window_days)
    
    print(f"   Date range: {start_date.date()} to {end_date.date()}")
    
    # Filter partitions within window
    partitions_in_window = []
    for partition in all_partitions:
        try:
            # Parse partition based on format
            if partition_format == "toYYYYMM":
                # Format: 202412
                if len(partition) == 6:
                    partition_date = datetime.strptime(partition, "%Y%m")
                else:
                    continue
            elif partition_format == "toYYYYMMDD":
                # Format: 20241230
                if len(partition) == 8:
                    partition_date = datetime.strptime(partition, "%Y%m%d")
                else:
                    continue
            else:
                # Unknown format, include all
                partitions_in_window.append(partition)
                continue
            
            # Check if in window
            if start_date <= partition_date <= end_date:
                partitions_in_window.append(partition)
                
        except ValueError:
            print(f"   ⚠️  Could not parse partition '{partition}'")
            continue
    
    print(f"   ✅ Found {len(partitions_in_window)} partitions in window (out of {len(all_partitions)} total)")
    return partitions_in_window


def get_partition_duplicate_stats(
    client,
    database: str,
    table: str,
    partition: str,
    partition_format: str,
    partition_column: str
) -> Dict[str, Any]:
    """Get duplicate statistics for a partition"""
    
    # Query for row counts and duplicates from the actual table
    row_query = f"""
        SELECT
            count() as total_rows,
            uniqExact(leadId) as unique_ids,
            count() - uniqExact(leadId) as duplicate_count,
            round((count() - uniqExact(leadId)) * 100.0 / count(), 2) as duplicate_pct
        FROM `{database}`.`{table}`
        WHERE {partition_format}({partition_column}) = %(partition)s
    """
    
    row_result = client.query(row_query, parameters={"partition": partition})
    
    # Query for bytes from system.parts
    size_query = f"""
        SELECT sum(bytes_on_disk) as bytes_on_disk
        FROM system.parts
        WHERE database = %(database)s
          AND table = %(table)s
          AND partition = %(partition)s
          AND active = 1
    """
    
    size_result = client.query(
        size_query, 
        parameters={"database": database, "table": table, "partition": partition}
    )
    
    if row_result.result_rows:
        row = row_result.result_rows[0]
        bytes_on_disk = size_result.result_rows[0][0] if size_result.result_rows else 0
        
        return {
            "partition": partition,
            "total_rows": row[0],
            "unique_ids": row[1],
            "duplicate_count": row[2],
            "duplicate_pct": round(row[3], 2),
            "bytes_on_disk": bytes_on_disk or 0,
        }
    
    return {
        "partition": partition,
        "total_rows": 0,
        "unique_ids": 0,
        "duplicate_count": 0,
        "duplicate_pct": 0.0,
        "bytes_on_disk": 0,
    }


def should_clean_partition(
    stats: Dict[str, Any],
    min_duplicate_threshold: int,
    duplicate_threshold_pct: float
) -> bool:
    """Determine if partition should be cleaned"""
    
    duplicate_count = stats["duplicate_count"]
    duplicate_pct = stats["duplicate_pct"]
    
    # Skip if below thresholds
    if duplicate_count < min_duplicate_threshold:
        return False
    
    if duplicate_pct < duplicate_threshold_pct:
        return False
    
    return True


# ============================================================================
# CLEANUP OPERATIONS
# ============================================================================
def deduplicate_partition(
    client,
    database: str,
    table: str,
    partition: str,
    stats: Dict[str, Any],
    partition_format: str,
    partition_column: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Deduplicate a partition using atomic replacement"""
    
    if dry_run:
        print(f"   🔍 [DRY RUN] Would deduplicate partition {partition} ({stats['duplicate_count']} duplicates)")
        return {
            "partition": partition,
            "action": "dry_run",
            "duplicates_removed": stats["duplicate_count"],
            "bytes_saved": 0,
        }
    
    print(f"   🧹 Deduplicating partition {partition}...")
    
    start_time = time.time()
    temp_table = f"{table}_temp_{partition}_{int(start_time)}"
    
    try:
        # Step 1: Create temp table with deduplicated data
        print(f"      → Creating temp table {temp_table}")
        
        create_temp_query = f"""
            CREATE TABLE `{database}`.`{temp_table}`
            ENGINE = MergeTree()
            ORDER BY (leadId, updatedAt)
            AS
            SELECT *
            FROM `{database}`.`{table}`
            WHERE {partition_format}({partition_column}) = %(partition)s
              AND (leadId, updatedAt) IN (
                  SELECT leadId, max(updatedAt) as updatedAt
                  FROM `{database}`.`{table}`
                  WHERE {partition_format}({partition_column}) = %(partition)s
                  GROUP BY leadId
              )
        """
        
        client.command(create_temp_query, parameters={"partition": partition})
        
        # Step 2: Get deduplicated row count
        count_query = f"SELECT count() FROM `{database}`.`{temp_table}`"
        count_result = client.query(count_query)
        deduplicated_rows = count_result.result_rows[0][0]
        
        print(f"      → Temp table created: {deduplicated_rows} rows (removed {stats['total_rows'] - deduplicated_rows} duplicates)")
        
        # Step 3: Drop old partition
        print(f"      → Dropping old partition {partition}")
        drop_query = f"ALTER TABLE `{database}`.`{table}` DROP PARTITION %(partition)s"
        client.command(drop_query, parameters={"partition": partition})
        
        # Step 4: Insert deduplicated data back
        print(f"      → Inserting deduplicated data")
        insert_query = f"""
            INSERT INTO `{database}`.`{table}`
            SELECT * FROM `{database}`.`{temp_table}`
        """
        client.command(insert_query)
        
        # Step 5: Drop temp table
        print(f"      → Dropping temp table")
        drop_temp_query = f"DROP TABLE `{database}`.`{temp_table}`"
        client.command(drop_temp_query)
        
        duration = time.time() - start_time
        duplicates_removed = stats['total_rows'] - deduplicated_rows
        
        print(f"   ✅ Partition {partition} deduplicated in {duration:.2f}s ({duplicates_removed} duplicates removed)")
        
        return {
            "partition": partition,
            "action": "deduplicated",
            "duplicates_removed": duplicates_removed,
            "duration_seconds": duration,
            "rows_before": stats['total_rows'],
            "rows_after": deduplicated_rows,
        }
        
    except Exception as e:
        print(f"   ❌ Failed to deduplicate partition {partition}: {e}")
        
        # Try to cleanup temp table if it exists
        try:
            client.command(f"DROP TABLE IF EXISTS `{database}`.`{temp_table}`")
        except Exception:
            pass
        
        return {
            "partition": partition,
            "action": "failed",
            "error": str(e),
            "duplicates_removed": 0,
        }


# ============================================================================
# MAIN CLEANUP LOGIC
# ============================================================================
def run_cleanup(
    database: str,
    table: str,
    partition_column: str = "createdAt",
    partition_format: str = "toYYYYMM",
    cleanup_window_days: Optional[int] = None,  # ← None = all partitions
    min_duplicate_threshold: int = 1,  # ← Default to 1
    duplicate_threshold_pct: float = 0.0,  # ← Default to 0.0
    specific_partition: Optional[str] = None,
    dry_run: bool = True
):
    """Main cleanup function"""
    
    start_time = time.time()
    
    print("=" * 80)
    print("🧹 CLICKHOUSE CLEANUP TEST")
    print("=" * 80)
    print(f"\n📊 Target: {database}.{table}")
    
    if cleanup_window_days is None:
        print(f"📅 Window: ALL PARTITIONS (complete historical cleanup)")
    else:
        print(f"📅 Window: Last {cleanup_window_days} days")
    
    print(f"🎯 Thresholds: Min {min_duplicate_threshold} duplicates OR {duplicate_threshold_pct}%")
    print(f"🔧 Mode: {'DRY RUN (no changes)' if dry_run else 'ACTIVE (will modify data!)'}")
    
    if specific_partition:
        print(f"📌 Specific partition: {specific_partition}")
    
    print("=" * 80)
    
    try:
        # Connect to ClickHouse
        config = Config()
        client = config.get_client()
        
        # Step 1: Get partitions
        if specific_partition:
            partitions = [specific_partition]
            print(f"\n✅ Using specific partition: {specific_partition}")
        else:
            partitions = get_partitions_in_window(
                client,
                database,
                table,
                partition_column,
                partition_format,
                cleanup_window_days
            )
        
        if not partitions:
            print("\nℹ️  No partitions found in cleanup window")
            return
        
        # Step 2: Analyze each partition
        print(f"\n📊 STEP 2: Analyzing {len(partitions)} partition(s)...\n")
        
        partition_stats = []
        for partition in partitions:
            stats = get_partition_duplicate_stats(
                client,
                database,
                table,
                partition,
                partition_format,
                partition_column
            )
            partition_stats.append(stats)
            
            print(f"   Partition {partition}: {stats['total_rows']:,} rows, {stats['duplicate_count']:,} duplicates ({stats['duplicate_pct']}%)")
        
        # Step 3: Identify partitions to clean
        print(f"\n🎯 STEP 3: Identifying partitions needing cleanup...\n")
        
        partitions_to_clean = [
            stats for stats in partition_stats
            if should_clean_partition(stats, min_duplicate_threshold, duplicate_threshold_pct)
        ]
        
        partitions_skipped = [
            stats for stats in partition_stats
            if not should_clean_partition(stats, min_duplicate_threshold, duplicate_threshold_pct)
        ]
        
        print(f"   → {len(partitions_to_clean)} partition(s) need cleanup")
        print(f"   → {len(partitions_skipped)} partition(s) skipped (below threshold)")
        
        if partitions_to_clean:
            print("\n📋 Partitions to clean:")
            for stats in partitions_to_clean:
                print(f"   • {stats['partition']}: {stats['duplicate_count']:,} duplicates ({stats['duplicate_pct']}%) - {stats['total_rows']:,} rows")
        
        if not partitions_to_clean:
            print("\n✅ No partitions need cleanup - all below threshold")
            duration = time.time() - start_time
            print(f"\n⏱️  Completed in {duration:.2f}s")
            return
        
        # Step 4: Clean partitions
        print(f"\n🧹 STEP 4: Cleaning {len(partitions_to_clean)} partition(s)...\n")
        
        cleanup_results = []
        total_duplicates_removed = 0
        
        for stats in partitions_to_clean:
            result = deduplicate_partition(
                client,
                database,
                table,
                stats['partition'],
                stats,
                partition_format,
                partition_column,
                dry_run
            )
            cleanup_results.append(result)
            total_duplicates_removed += result.get('duplicates_removed', 0)
        
        # Summary
        duration = time.time() - start_time
        total_rows_before = sum(s['total_rows'] for s in partitions_to_clean)
        total_rows_after = total_rows_before - total_duplicates_removed
        
        print("\n" + "=" * 80)
        print("🎉 CLEANUP COMPLETE")
        print("=" * 80)
        print(f"\n📊 Results:")
        print(f"   Partitions checked: {len(partitions)}")
        print(f"   Partitions cleaned: {len(partitions_to_clean)}")
        print(f"   Partitions skipped: {len(partitions_skipped)}")
        print(f"   Duplicates removed: {total_duplicates_removed:,}")
        print(f"   Rows before: {total_rows_before:,}")
        print(f"   Rows after: {total_rows_after:,}")
        if total_rows_before > 0:
            reduction_pct = (total_duplicates_removed / total_rows_before) * 100
            print(f"   Reduction: {reduction_pct:.1f}%")
        print(f"   Duration: {duration:.2f}s")
        
        if dry_run:
            print("\n⚠️  This was a DRY RUN - no actual changes were made")
            print("   Run without --dry-run to perform actual cleanup")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# CLI
# ============================================================================
def main():
    """Main CLI function"""
    
    parser = argparse.ArgumentParser(
        description='Test ClickHouse cleanup locally',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (safe - just reports)
  %(prog)s --database sales-service --table leads_v2 --dry-run
  
  # Actual cleanup
  %(prog)s --database sales-service --table leads_v2
  
  # Cleanup specific partition
  %(prog)s --database sales-service --table leads_v2 --partition 202412
  
  # Adjust thresholds
  %(prog)s --database sales-service --table leads_v2 --min-duplicates 50 --min-pct 0.5 --dry-run
        """
    )
    
    parser.add_argument(
        '-d', '--database',
        required=True,
        help='Database name'
    )
    parser.add_argument(
        '-t', '--table',
        required=True,
        help='Table name'
    )
    parser.add_argument(
        '--partition-column',
        default='createdAt',
        help='Column used for partitioning (default: createdAt)'
    )
    parser.add_argument(
        '--partition-format',
        default='toYYYYMM',
        choices=['toYYYYMM', 'toYYYYMMDD'],
        help='Partition format (default: toYYYYMM)'
    )
    parser.add_argument(
        '--window-days',
        type=int,
        default=None,  # ← Changed: None = all partitions
        help='Cleanup window in days (default: None = all partitions, use number to limit)'
    )
    parser.add_argument(
        '--min-duplicates',
        type=int,
        default=1,  # ← Changed: clean any partition with duplicates
        help='Minimum duplicates to trigger cleanup (default: 1)'
    )
    parser.add_argument(
        '--min-pct',
        type=float,
        default=0.0,  # ← Changed: clean even 0.1% duplicates
        help='Minimum duplicate percentage to trigger cleanup (default: 0.0)'
    )
    parser.add_argument(
        '--partition',
        help='Cleanup specific partition only (e.g., 202412)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - only report, do not make changes (recommended for first run)'
    )
    
    args = parser.parse_args()
    
    # Run cleanup
    run_cleanup(
        database=args.database,
        table=args.table,
        partition_column=args.partition_column,
        partition_format=args.partition_format,
        cleanup_window_days=args.window_days,
        min_duplicate_threshold=args.min_duplicates,
        duplicate_threshold_pct=args.min_pct,
        specific_partition=args.partition,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()