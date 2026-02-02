"""
CIV Regional Data Migration - Production Version

Migrates regional data from source to target MySQL database with support for:
- Initial migration (one-time setup)
- Daily sync via TRUNCATE + INSERT (fast, no duplicates)
- Auto-detection of schema changes with recreation
- Legacy data handling (zero dates, permissive SQL mode)
- Data validation and integrity checks

USAGE:
======

1. INITIAL MIGRATION (First Run):
   {
       "parent_id_value": 2,
       "recreate_tables": false,
       "truncate_before_load": false
   }

2. DAILY SYNC (Automated):
   {
       "parent_id_value": 2,
       "truncate_before_load": true  # ← Clears data, keeps structure
   }

SCHEMA CHANGES:
===============
When source schema changes (columns added/removed), the migrator automatically
detects this during daily sync and recreates affected tables. No manual
intervention needed!

TO SWITCH DATABASES: Change SOURCE_RESOURCE and TARGET_RESOURCE below!
"""

from dagster import (
    asset,
    AssetExecutionContext,
    Output,
    MetadataValue,
    Config,
)
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
import time
import pymysql
from pymysql.cursors import DictCursor

from dagster_pipeline.utils.logging_config import get_logger

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION - CHANGE THESE TO SWITCH DATABASES
# ════════════════════════════════════════════════════════════════════════════

# Database resources (defined in your registry.py)
SOURCE_RESOURCE = "sc_mysql_amtdb_replica_resource"  # Where to READ from
TARGET_RESOURCE = "grdata_mysql_db_resource"         # Where to WRITE to (PRODUCTION)
#TARGET_RESOURCE = "local_mysql_db_resource"          # Where to WRITE to (STAGING/LOCAL)

# Default settings (override in Dagster UI)
DEFAULT_PARENT_TABLE = "company_regions"
DEFAULT_PARENT_ID_COLUMN = "id"
DEFAULT_PARENT_ID_VALUE = 2
DEFAULT_BATCH_SIZE = 1000

# ════════════════════════════════════════════════════════════════════════════


class CIVDataMigrationConfig(Config):
    """
    Configuration for CIV regional data migration
    
    Parameters:
    -----------
    parent_table : str
        Starting table for FK traversal (default: "company_regions")
    
    parent_id_column : str
        Column to filter on (default: "id")
    
    parent_id_value : int
        Specific region ID to migrate (default: 2)
    
    batch_size : int
        Rows per batch during streaming (default: 1000)
    
    recreate_tables : bool
        Drop and recreate tables (use for schema changes) (default: False)
    
    truncate_before_load : bool
        Clear data but keep structure - FOR DAILY SYNC (default: False)
        Set to True for automated daily syncs to prevent duplicates
    
    skip_validation : bool
        Skip row count validation (default: False)
    
    sql_mode : str
        Target SQL mode: 'permissive', 'strict', or 'default' (default: 'permissive')
        Use 'permissive' to handle legacy data with zero dates
    """
    
    parent_table: str = DEFAULT_PARENT_TABLE
    parent_id_column: str = DEFAULT_PARENT_ID_COLUMN
    parent_id_value: int = DEFAULT_PARENT_ID_VALUE
    batch_size: int = DEFAULT_BATCH_SIZE
    recreate_tables: bool = False
    skip_validation: bool = False
    truncate_before_load: bool = False  # ← KEY: Set to True for daily sync
    sql_mode: str = 'permissive'


# ============================================================================
# REGIONAL DATA MIGRATOR
# ============================================================================

class RegionalDataMigrator:
    """
    Handles migration of regional data from source to target MySQL database.
    
    Uses BFS (Breadth-First Search) to traverse FK relationships and extract
    only data related to the specified region. Streams data in batches for
    memory efficiency.
    
    Key Features:
    - Automatic FK relationship discovery
    - Streaming batch processing (no pandas)
    - TRUNCATE mode for daily sync (no duplicates)
    - Auto-detection of schema changes with recreation
    - Data validation
    - Handles circular FK dependencies
    - Supports legacy data (zero dates)
    
    Schema Change Handling:
    -----------------------
    During daily sync (truncate mode), the migrator automatically detects
    schema changes by comparing column names/order between source and target.
    
    - Schema matches → Fast TRUNCATE (~0.1s per table)
    - Schema changed → Auto DROP+CREATE with new schema (~2-5s per table)
    
    This handles the common case where columns are added/removed in the source
    database without manual intervention or failed INSERTs.
    """
    
    def __init__(
        self,
        source_conn,
        target_conn,
        context: AssetExecutionContext
    ):
        self.source_conn = source_conn
        self.target_conn = target_conn
        self.context = context
        
        # Track migration progress
        self.migrated_tables = {}  # {table_name: row_count}
        self.failed_tables = {}    # {table_name: error_message}
    
    def get_table_primary_key(self, table_name: str) -> Optional[str]:
        """Get the primary key column name for a table using INFORMATION_SCHEMA"""
        query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND CONSTRAINT_NAME = 'PRIMARY'
        ORDER BY ORDINAL_POSITION
        LIMIT 1
        """
        
        with self.source_conn.cursor() as cursor:
            cursor.execute(query, (table_name,))
            result = cursor.fetchone()
            
            if result:
                return result['COLUMN_NAME']
            
            self.context.log.warning(f"  ⚠️  No primary key found for {table_name}")
            return None
    
    def get_child_tables(self, parent_table: str) -> List[Dict]:
        """Get all BASE TABLES (not views) that reference the parent table."""
        query = """
        SELECT 
            kcu.TABLE_NAME as child_table,
            kcu.COLUMN_NAME as child_column,
            kcu.REFERENCED_TABLE_NAME as parent_table,
            kcu.REFERENCED_COLUMN_NAME as parent_column,
            kcu.CONSTRAINT_NAME
        FROM 
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        JOIN 
            INFORMATION_SCHEMA.TABLES t 
            ON kcu.TABLE_SCHEMA = t.TABLE_SCHEMA 
            AND kcu.TABLE_NAME = t.TABLE_NAME
        WHERE 
            kcu.REFERENCED_TABLE_SCHEMA = DATABASE()
            AND kcu.REFERENCED_TABLE_NAME = %s
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            AND t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY kcu.TABLE_NAME
        """
        
        with self.source_conn.cursor() as cursor:
            cursor.execute(query, (parent_table,))
            return cursor.fetchall()
    
    def get_all_descendant_tables(self, parent_table: str) -> Dict[str, List[Dict]]:
        """
        Recursively discover all tables that depend on the parent table.
        Returns a relationships map: {parent_table: [child_relationships]}
        """
        visited = set()
        relationships_map = {}
        
        def explore_children(table: str, level: int = 0):
            if table in visited:
                return
            
            visited.add(table)
            children = self.get_child_tables(table)
            
            if children:
                relationships_map[table] = children
                self.context.log.info(
                    f"{'  ' * level}└─ {table} has {len(children)} child table(s)"
                )
                
                for child_rel in children:
                    child_table = child_rel['child_table']
                    explore_children(child_table, level + 1)
            else:
                self.context.log.debug(f"{'  ' * level}└─ {table} (leaf node)")
        
        self.context.log.info(
            f"\n🔍 Discovering table hierarchy starting from '{parent_table}':"
        )
        explore_children(parent_table)
        
        return relationships_map
    
    def is_base_table(self, table_name: str) -> bool:
        """Check if table is a BASE TABLE (not a VIEW)"""
        query = """
        SELECT TABLE_TYPE 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        """
        
        with self.source_conn.cursor() as cursor:
            cursor.execute(query, (table_name,))
            result = cursor.fetchone()
            
            if result and result['TABLE_TYPE'] == 'BASE TABLE':
                return True
            
            if result and result['TABLE_TYPE'] == 'VIEW':
                self.context.log.debug(f"  ⊗ Skipping {table_name} (VIEW)")
            
            return False
    
    def get_table_create_statement(self, table_name: str) -> str:
        """Get CREATE TABLE statement from source database"""
        query = f"SHOW CREATE TABLE {table_name}"
        
        with self.source_conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result['Create Table']
    
    def table_exists_in_target(self, table_name: str) -> bool:
        """Check if table exists in target database"""
        query = """
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = DATABASE()
        AND table_name = %s
        """
        
        with self.target_conn.cursor() as cursor:
            cursor.execute(query, (table_name,))
            result = cursor.fetchone()
            return result['count'] > 0
    
    def get_table_columns(self, conn, table_name: str) -> List[str]:
        """
        Get ordered list of column names for a table.
        Used for schema comparison between source and target.
        """
        query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        
        with conn.cursor() as cursor:
            cursor.execute(query, (table_name,))
            rows = cursor.fetchall()
            return [row['COLUMN_NAME'] for row in rows]
    
    def schemas_match(self, table_name: str) -> bool:
        """
        Compare schemas between source and target tables.
        
        Returns:
            True if columns match (names and order), False otherwise
        
        Note: Only compares column names/order, not types or constraints.
              This catches the most common schema change: added/removed columns.
        """
        try:
            source_cols = self.get_table_columns(self.source_conn, table_name)
            target_cols = self.get_table_columns(self.target_conn, table_name)
            
            if source_cols != target_cols:
                self.context.log.debug(
                    f"    Schema mismatch: source has {len(source_cols)} columns, "
                    f"target has {len(target_cols)} columns"
                )
                return False
            
            return True
        
        except Exception as e:
            self.context.log.warning(f"    ⚠️  Could not compare schemas: {e}")
            # Assume mismatch on error — safer to recreate
            return False
    
    def detect_sync_mode(
        self,
        parent_table: str,
        parent_id_column: str,
        parent_id_value: int,
        user_truncate_flag: bool
    ) -> bool:
        """
        Auto-detect whether to truncate based on target DB state.
        
        Logic:
        - Parent table exists AND has data → subsequent run → truncate
        - Parent table doesn't exist OR is empty → first run → don't truncate
        - User explicitly set truncate=True → always honour it
        
        Returns:
            True if we should truncate, False otherwise
        """
        # If user explicitly asked for truncate, honour it
        if user_truncate_flag:
            return True
        
        # Check if parent table exists in target
        if not self.table_exists_in_target(parent_table):
            self.context.log.info("  📊 Parent table not found → first run detected")
            return False
        
        # Table exists — check if it has data for this region
        query = f"SELECT COUNT(*) as count FROM {parent_table} WHERE {parent_id_column} = %s"
        with self.target_conn.cursor() as cursor:
            cursor.execute(query, (parent_id_value,))
            result = cursor.fetchone()
            row_count = result['count']
        
        if row_count > 0:
            self.context.log.info(
                f"  📊 Found {row_count} existing row(s) in {parent_table} "
                f"→ subsequent run detected, enabling truncate"
            )
            return True
        else:
            self.context.log.info(
                f"  📊 {parent_table} exists but is empty → first run detected"
            )
            return False
    
    def create_table_in_target(
        self, 
        table_name: str, 
        recreate: bool = False, 
        truncate: bool = False
    ):
        """
        Create or prepare table in target database.
        
        Parameters:
        -----------
        table_name : str
            Name of the table to create/prepare
        
        recreate : bool
            If True, drops and recreates table (for schema changes)
        
        truncate : bool
            If True, empties table but keeps structure (for daily sync)
            This is MUCH faster than drop/recreate!
        
        Behavior:
        ---------
        - If table doesn't exist: Creates it with full structure (FKs, indexes)
        - If recreate=True: Drops and recreates (slow, use for schema changes)
        - If truncate=True: Empties data, keeps structure (fast, use for daily sync)
        - Otherwise: Does nothing (table exists, not truncate mode)
        """
        table_exists = self.table_exists_in_target(table_name)
        
        # DAILY SYNC MODE: Truncate existing table
        if table_exists and truncate and not recreate:
            self.context.log.info(f"  🗑️  Truncating {table_name} (keeping structure)")
            with self.target_conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {table_name}")
                self.target_conn.commit()
            return  # Table ready for fresh data
        
        # Table exists and we're not recreating or truncating
        if table_exists and not recreate and not truncate:
            self.context.log.debug(f"  ℹ️  Table {table_name} already exists, skipping")
            return
        
        # RECREATE MODE: Drop and recreate (for schema changes)
        if table_exists and recreate:
            self.context.log.info(f"  🗑️  Dropping table {table_name} for recreation")
            with self.target_conn.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                self.target_conn.commit()
        
        # Create table from source schema
        create_statement = self.get_table_create_statement(table_name)
        
        with self.target_conn.cursor() as cursor:
            cursor.execute(create_statement)
            self.target_conn.commit()
        
        self.context.log.info(f"  ✓ Created table {table_name}")
    
    def get_row_count(
        self, 
        conn, 
        table_name: str, 
        where_clause: str = None, 
        where_params: tuple = None
    ) -> int:
        """Get row count for a table with optional WHERE clause"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        with conn.cursor() as cursor:
            if where_params:
                cursor.execute(query, where_params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchone()
            return result['count']
    
    def stream_and_load_table(
        self,
        table_name: str,
        where_clause: str,
        where_params: tuple,
        batch_size: int = 1000
    ) -> int:
        """
        Stream data from source and load directly to target in batches.
        
        Uses server-side cursor (SSCursor) to avoid loading all data into memory.
        Inserts in batches for efficiency.
        
        Returns:
            Number of rows loaded
        
        Raises:
            Exception if any batch fails (fail-fast for data integrity)
        """
        query = f"SELECT * FROM {table_name} WHERE {where_clause}"
        
        total_rows = 0
        batch_count = 0
        
        # Use server-side cursor for streaming
        with self.source_conn.cursor(pymysql.cursors.SSCursor) as source_cursor:
            source_cursor.execute(query, where_params)
            
            # Get column names from cursor description
            columns = [desc[0] for desc in source_cursor.description]
            column_names = ', '.join(f"`{col}`" for col in columns)
            placeholders = ', '.join(['%s'] * len(columns))
            
            insert_query = f"""
            INSERT INTO `{table_name}` ({column_names})
            VALUES ({placeholders})
            """
            
            # Stream and insert in batches
            while True:
                batch = source_cursor.fetchmany(batch_size)
                if not batch:
                    break
                
                batch_count += 1
                
                try:
                    with self.target_conn.cursor() as target_cursor:
                        target_cursor.executemany(insert_query, batch)
                    
                    total_rows += len(batch)
                    
                    # Log progress every 10 batches
                    if batch_count % 10 == 0:
                        self.context.log.debug(
                            f"    Progress: {total_rows:,} rows loaded ({batch_count} batches)"
                        )
                
                except Exception as e:
                    self.context.log.error(
                        f"  ❌ Batch {batch_count} failed for {table_name}: {e}"
                    )
                    raise  # Fail fast - don't continue with partial data
            
            # Commit all inserts
            self.target_conn.commit()
        
        self.context.log.info(
            f"  ✓ {table_name}: {total_rows:,} rows loaded in {batch_count} batches"
        )
        return total_rows
    
    def extract_ids_for_next_level(
        self,
        table_name: str,
        where_clause: str,
        where_params: tuple,
        pk_column: str
    ) -> List:
        """
        Extract primary key values from a table for filtering child tables.
        Uses a separate query to avoid interfering with streaming cursor.
        """
        query = f"SELECT {pk_column} FROM {table_name} WHERE {where_clause}"
        
        with self.source_conn.cursor() as cursor:
            cursor.execute(query, where_params)
            rows = cursor.fetchall()
            return [row[pk_column] for row in rows]
    
    def validate_row_counts(self) -> List[str]:
        """
        Validate that row counts match between source and target.
        Returns list of validation errors (empty if all valid).
        """
        errors = []
        
        self.context.log.info("\n🔍 Validating row counts...")
        
        for table_name, expected_count in self.migrated_tables.items():
            try:
                actual_count = self.get_row_count(self.target_conn, table_name)
                
                if actual_count != expected_count:
                    error = (
                        f"  ❌ {table_name}: expected {expected_count:,} rows, "
                        f"found {actual_count:,} rows"
                    )
                    errors.append(error)
                    self.context.log.error(error)
                else:
                    self.context.log.info(
                        f"  ✓ {table_name}: {actual_count:,} rows (validated)"
                    )
            
            except Exception as e:
                error = f"  ❌ {table_name}: validation failed - {e}"
                errors.append(error)
                self.context.log.error(error)
        
        return errors
    
    def extract_and_migrate_regional_data(
        self,
        parent_table: str,
        parent_id_column: str,
        parent_id_value: int,
        batch_size: int = 1000,
        recreate_tables: bool = False,
        truncate_before_load: bool = False,
        skip_validation: bool = False
    ) -> Dict:
        """
        Extract and migrate regional data using BFS traversal of FK relationships.
        
        Algorithm:
        ----------
        1. Start with parent table (e.g., company_regions WHERE id=2)
        2. Extract parent data and IDs
        3. For each child table referenced by parent:
           - Filter by parent IDs
           - Extract child data and IDs
           - Add children to processing queue
        4. Repeat until all related tables processed
        
        Parameters:
        -----------
        parent_table : str
            Starting table (e.g., "company_regions")
        
        parent_id_column : str
            Column to filter on (e.g., "id")
        
        parent_id_value : int
            Specific value to filter (e.g., 2 for region_id=2)
        
        batch_size : int
            Rows per batch during streaming
        
        recreate_tables : bool
            Drop and recreate tables (for schema changes)
        
        truncate_before_load : bool
            Clear data but keep structure (FOR DAILY SYNC - prevents duplicates)
        
        skip_validation : bool
            Skip row count validation
        
        Returns:
        --------
        Dict with migration statistics:
        - tables_created: Number of tables created/prepared
        - tables_loaded: Number of tables with data loaded
        - tables_failed: Number of failed tables
        - total_rows_loaded: Total rows migrated
        - details: Per-table details
        """
        self.context.log.info("=" * 70)
        self.context.log.info(
            f"📊 REGIONAL DATA MIGRATION: {parent_table}.{parent_id_column} = {parent_id_value}"
        )
        self.context.log.info("=" * 70)
        
        results = {
            "tables_created": 0,
            "tables_loaded": 0,
            "tables_failed": 0,
            "total_rows_loaded": 0,
            "details": []
        }
        
        # Track what we've processed
        processed = set()
        
        # Track extracted IDs for filtering child tables
        # Format: {table_name: {pk_column: [id1, id2, ...]}}
        extracted_ids = {}
        
        try:
            # Step 1: Auto-detect sync mode (first run vs subsequent)
            self.context.log.info("\n🔍 Detecting sync mode...")
            truncate_before_load = self.detect_sync_mode(
                parent_table,
                parent_id_column,
                parent_id_value,
                truncate_before_load  # pass user's flag through
            )
            
            if truncate_before_load:
                self.context.log.info("🔄 MODE: DAILY SYNC (TRUNCATE + INSERT)")
            else:
                self.context.log.info("🔄 MODE: INITIAL MIGRATION (CREATE + INSERT)")
            
            # Step 2: Discover all related tables via FK relationships
            self.context.log.info("\n🔍 Discovering table relationships...")
            relationships_map = self.get_all_descendant_tables(parent_table)
            
            # Step 3: Disable FK checks for bulk loading
            self.context.log.info("\n🔓 Disabling foreign key checks for migration...")
            with self.target_conn.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                self.target_conn.commit()
            
            # Step 4: Process parent table
            self.context.log.info(f"\n📦 Processing parent table: {parent_table}")
            
            try:
                # Create table if it doesn't exist yet (never truncate here)
                self.create_table_in_target(
                    parent_table, 
                    recreate=recreate_tables, 
                    truncate=False
                )
                results["tables_created"] += 1
                
                # Check source FIRST before touching target data
                parent_query = f"SELECT * FROM {parent_table} WHERE {parent_id_column} = %s"
                
                with self.source_conn.cursor() as cursor:
                    cursor.execute(parent_query, (parent_id_value,))
                    parent_rows = cursor.fetchall()
                
                if not parent_rows:
                    self.context.log.warning(
                        f"⚠️  No data found for {parent_table}.{parent_id_column} = {parent_id_value}"
                    )
                    return results
                
                # Source confirmed — decide whether to truncate or recreate
                if truncate_before_load:
                    # Check if schema changed
                    if not self.schemas_match(parent_table):
                        self.context.log.warning(
                            f"  ⚠️  Schema changed for {parent_table}, recreating table..."
                        )
                        # Drop and recreate with new schema
                        with self.target_conn.cursor() as cursor:
                            cursor.execute(f"DROP TABLE IF EXISTS {parent_table}")
                            self.target_conn.commit()
                        
                        create_statement = self.get_table_create_statement(parent_table)
                        with self.target_conn.cursor() as cursor:
                            cursor.execute(create_statement)
                            self.target_conn.commit()
                        self.context.log.info(f"  ✓ Recreated {parent_table} with updated schema")
                    else:
                        # Schema matches — fast truncate path
                        self.context.log.info(f"  🗑️  Truncating {parent_table} (keeping structure)")
                        with self.target_conn.cursor() as cursor:
                            cursor.execute(f"TRUNCATE TABLE {parent_table}")
                            self.target_conn.commit()
                
                # Extract parent IDs for filtering children
                extracted_ids[parent_table] = {
                    parent_id_column: [row[parent_id_column] for row in parent_rows]
                }
                
                # Stream and load parent data
                load_start = time.time()
                rows_loaded = self.stream_and_load_table(
                    parent_table,
                    f"{parent_id_column} = %s",
                    (parent_id_value,),
                    batch_size
                )
                load_duration = time.time() - load_start
                
                # Track for validation
                self.migrated_tables[parent_table] = rows_loaded
                
                results["tables_loaded"] += 1
                results["total_rows_loaded"] += rows_loaded
                results["details"].append({
                    "table": parent_table,
                    "status": "success",
                    "rows": rows_loaded,
                    "duration": round(load_duration, 2)
                })
                
                processed.add(parent_table)
                
            except Exception as e:
                self.context.log.error(f"  ❌ Failed to process parent table: {e}")
                self.failed_tables[parent_table] = str(e)
                results["tables_failed"] += 1
                results["details"].append({
                    "table": parent_table,
                    "status": "failed",
                    "error": str(e)
                })
                raise
            
            # Step 5: Process child tables using BFS traversal
            self.context.log.info(f"\n📦 Processing child tables via BFS traversal...")
            
            # Queue: (table_name, extracted_ids_for_this_table)
            to_process = [(parent_table, extracted_ids[parent_table])]
            
            while to_process:
                current_table, current_ids = to_process.pop(0)
                
                # Get children of current table
                if current_table not in relationships_map:
                    continue
                
                for child_rel in relationships_map[current_table]:
                    child_table = child_rel['child_table']
                    child_fk_column = child_rel['child_column']
                    parent_pk_column = child_rel['parent_column']
                    
                    # Skip if already processed
                    if child_table in processed:
                        continue
                    
                    # Skip views
                    if not self.is_base_table(child_table):
                        processed.add(child_table)
                        continue
                    
                    # Get parent IDs for this relationship
                    if parent_pk_column not in current_ids:
                        self.context.log.warning(
                            f"  ⚠️  Cannot find {parent_pk_column} in {current_table} - skipping {child_table}"
                        )
                        processed.add(child_table)
                        continue
                    
                    parent_values = current_ids[parent_pk_column]
                    
                    if not parent_values:
                        self.context.log.debug(
                            f"  ℹ️  No parent IDs for {child_table} - skipping"
                        )
                        processed.add(child_table)
                        continue
                    
                    self.context.log.info(f"\n🔄 Processing: {child_table}")
                    
                    try:
                        # Create table if it doesn't exist yet (never truncate here)
                        self.create_table_in_target(
                            child_table, 
                            recreate=recreate_tables, 
                            truncate=False
                        )
                        results["tables_created"] += 1
                        
                        # Build WHERE clause for filtering
                        placeholders = ','.join(['%s'] * len(parent_values))
                        where_clause = f"{child_fk_column} IN ({placeholders})"
                        where_params = tuple(parent_values)
                        
                        # Check source FIRST before touching target data
                        source_count = self.get_row_count(
                            self.source_conn,
                            child_table,
                            where_clause,
                            where_params
                        )
                        
                        if source_count == 0:
                            self.context.log.info(f"  ℹ️  No data found, skipping")
                            results["details"].append({
                                "table": child_table,
                                "status": "skipped",
                                "rows": 0,
                                "reason": "no_data"
                            })
                            processed.add(child_table)
                            continue
                        
                        self.context.log.info(f"  📊 Found {source_count:,} rows to migrate")
                        
                        # Source confirmed — decide whether to truncate or recreate
                        if truncate_before_load:
                            # Check if schema changed
                            if not self.schemas_match(child_table):
                                self.context.log.warning(
                                    f"  ⚠️  Schema changed for {child_table}, recreating table..."
                                )
                                # Drop and recreate with new schema
                                with self.target_conn.cursor() as cursor:
                                    cursor.execute(f"DROP TABLE IF EXISTS {child_table}")
                                    self.target_conn.commit()
                                
                                create_statement = self.get_table_create_statement(child_table)
                                with self.target_conn.cursor() as cursor:
                                    cursor.execute(create_statement)
                                    self.target_conn.commit()
                                self.context.log.info(f"  ✓ Recreated {child_table} with updated schema")
                            else:
                                # Schema matches — fast truncate path
                                self.context.log.info(f"  🗑️  Truncating {child_table} (keeping structure)")
                                with self.target_conn.cursor() as cursor:
                                    cursor.execute(f"TRUNCATE TABLE {child_table}")
                                    self.target_conn.commit()
                        
                        # Extract IDs for next level (for filtering this table's children)
                        pk_column = self.get_table_primary_key(child_table)
                        if pk_column:
                            ids = self.extract_ids_for_next_level(
                                child_table,
                                where_clause,
                                where_params,
                                pk_column
                            )
                            
                            if ids:
                                extracted_ids[child_table] = {pk_column: ids}
                                self.context.log.debug(
                                    f"  🔑 Extracted {len(ids):,} IDs from {pk_column}"
                                )
                        
                        # Stream and load data
                        load_start = time.time()
                        rows_loaded = self.stream_and_load_table(
                            child_table,
                            where_clause,
                            where_params,
                            batch_size
                        )
                        load_duration = time.time() - load_start
                        
                        # Track for validation
                        self.migrated_tables[child_table] = rows_loaded
                        
                        results["tables_loaded"] += 1
                        results["total_rows_loaded"] += rows_loaded
                        results["details"].append({
                            "table": child_table,
                            "status": "success",
                            "rows": rows_loaded,
                            "duration": round(load_duration, 2)
                        })
                        
                        # Add to processing queue if we extracted IDs
                        if child_table in extracted_ids:
                            to_process.append((child_table, extracted_ids[child_table]))
                        
                    except Exception as e:
                        self.context.log.error(f"  ❌ Failed to process {child_table}: {e}")
                        self.failed_tables[child_table] = str(e)
                        results["tables_failed"] += 1
                        results["details"].append({
                            "table": child_table,
                            "status": "failed",
                            "error": str(e)
                        })
                        # Continue with other tables (partial migration acceptable)
                    
                    processed.add(child_table)
            
            # Step 6: Validate data integrity
            if not skip_validation and self.migrated_tables:
                validation_errors = self.validate_row_counts()
                
                if validation_errors:
                    self.context.log.error("\n❌ Validation failed!")
                    for error in validation_errors:
                        self.context.log.error(error)
                    self.context.log.warning(
                        f"⚠️  {len(validation_errors)} table(s) failed validation"
                    )
                else:
                    self.context.log.info("\n✅ All row counts validated successfully")
        
        except Exception as e:
            self.context.log.error(f"\n❌ Migration failed: {e}")
            raise
        
        finally:
            # Step 7: Always re-enable FK checks
            self.context.log.info("\n🔒 Re-enabling foreign key checks...")
            try:
                with self.target_conn.cursor() as cursor:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                    self.target_conn.commit()
                self.context.log.info("  ✓ Foreign key checks re-enabled")
            except Exception as e:
                self.context.log.error(f"  ❌ Failed to re-enable FK checks: {e}")
                raise
        
        self.context.log.info("\n" + "=" * 70)
        self.context.log.info("✅ MIGRATION COMPLETE")
        self.context.log.info(f"Tables created: {results['tables_created']}")
        self.context.log.info(f"Tables loaded: {results['tables_loaded']}")
        self.context.log.info(f"Tables failed: {results['tables_failed']}")
        self.context.log.info(f"Total rows: {results['total_rows_loaded']:,}")
        self.context.log.info("=" * 70)
        
        return results


# ============================================================================
# DAGSTER ASSET
# ============================================================================

@asset(
    name="civ_regional_data_migration",
    group_name="data_migration",
    compute_kind="MYSQL_MIGRATION",
    description=f"Migrate CIV regional data from {SOURCE_RESOURCE} to {TARGET_RESOURCE} with TRUNCATE mode for daily sync",
    required_resource_keys={
        "sc_mysql_amtdb_replica_resource",
        "local_mysql_db_resource", 
        "grdata_mysql_db_resource"
    },
)
def civ_regional_data_migration(
    context: AssetExecutionContext,
    config: CIVDataMigrationConfig
) -> Output[Dict]:
    """
    CIV Regional Data Migration - Production Asset
    
    Supports two modes:
    
    1. INITIAL MIGRATION (First Run):
       - Creates tables with full structure (FKs, indexes)
       - Loads regional data
       - Config: truncate_before_load=False
    
    2. DAILY SYNC (Automated):
       - Truncates tables (empties data, keeps structure)
       - Reloads fresh data
       - No duplicates, fast (~60 seconds)
       - Config: truncate_before_load=True
    
    Configuration:
    --------------
    parent_table: Starting table (default: "company_regions")
    parent_id_column: Column to filter on (default: "id")
    parent_id_value: Specific region ID (default: 2)
    batch_size: Rows per batch (default: 1000)
    recreate_tables: Drop/recreate tables (default: False)
    truncate_before_load: Clear data for daily sync (default: False)
    skip_validation: Skip row count validation (default: False)
    sql_mode: 'permissive', 'strict', or 'default' (default: 'permissive')
    
    Example Daily Sync Config:
    ---------------------------
    {
        "parent_id_value": 2,
        "truncate_before_load": true
    }
    """
    
    start_time = time.time()
    
    # Log configuration
    context.log.info("🚀 Starting CIV Regional Data Migration")
    context.log.info(f"📖 Source: {SOURCE_RESOURCE}")
    context.log.info(f"📝 Target: {TARGET_RESOURCE}")
    context.log.info(f"🎯 Region: {config.parent_table}.{config.parent_id_column} = {config.parent_id_value}")
    context.log.info(f"📦 Batch Size: {config.batch_size:,} rows")
    context.log.info(f"🔄 Recreate Tables: {config.recreate_tables}")
    context.log.info(f"🗑️  Truncate Before Load: {config.truncate_before_load}")
    context.log.info(f"✓ Validation: {'Disabled' if config.skip_validation else 'Enabled'}")
    context.log.info(f"⚙️  SQL Mode: {config.sql_mode}")
    
    # Get database resources
    try:
        source_resource = getattr(context.resources, SOURCE_RESOURCE)
    except AttributeError:
        error_msg = (
            f"❌ Source resource '{SOURCE_RESOURCE}' not found!\n"
            f"Available: {list(context.resources._asdict().keys())}\n"
            f"💡 Check SOURCE_RESOURCE in script matches definitions.py"
        )
        context.log.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        target_resource = getattr(context.resources, TARGET_RESOURCE)
    except AttributeError:
        error_msg = (
            f"❌ Target resource '{TARGET_RESOURCE}' not found!\n"
            f"Available: {list(context.resources._asdict().keys())}\n"
            f"💡 Check TARGET_RESOURCE in script matches definitions.py"
        )
        context.log.error(error_msg)
        raise ValueError(error_msg)
    
    source_conn = None
    target_conn = None
    
    try:
        # Connect to source database
        context.log.info("\n🔌 Connecting to source database...")
        source_conn = pymysql.connect(
            host=source_resource.host,
            port=source_resource.port,
            user=source_resource.user,
            password=source_resource.password,
            database=source_resource.database,
            charset=source_resource.charset,
            cursorclass=DictCursor,
            connect_timeout=source_resource.connect_timeout
        )
        context.log.info(f"  ✓ Connected to {source_resource.database}")
        
        # Connect to target database
        is_local_target = "local" in TARGET_RESOURCE.lower()
        
        context.log.info(f"\n🔌 Connecting to target database...")
        if is_local_target:
            context.log.info("  ℹ️  Detected local target, connecting without SSL")
            target_conn = pymysql.connect(
                host=target_resource.host,
                port=target_resource.port,
                user=target_resource.user,
                password=target_resource.password,
                database=target_resource.database,
                charset=target_resource.charset,
                cursorclass=DictCursor,
                connect_timeout=target_resource.connect_timeout
            )
            context.log.info(f"  ✓ Connected to {target_resource.database} (no SSL)")
        else:
            context.log.info("  ℹ️  Detected remote target, connecting with SSL")
            target_conn = pymysql.connect(
                host=target_resource.host,
                port=target_resource.port,
                user=target_resource.user,
                password=target_resource.password,
                database=target_resource.database,
                charset=target_resource.charset,
                cursorclass=DictCursor,
                connect_timeout=target_resource.connect_timeout,
                ssl={'ssl_mode': 'REQUIRED'}
            )
            context.log.info(f"  ✓ Connected to {target_resource.database} (SSL enabled)")
        
        # Configure SQL mode for legacy data compatibility
        if config.sql_mode != 'default':
            context.log.info(f"  🔧 Configuring SQL mode: {config.sql_mode}")
            with target_conn.cursor() as cursor:
                if config.sql_mode == 'permissive':
                    cursor.execute("SET SESSION sql_mode = 'NO_ENGINE_SUBSTITUTION'")
                    context.log.info("  ✓ Permissive mode: allows zero dates, auto conversions")
                elif config.sql_mode == 'strict':
                    cursor.execute("""
                        SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,
                        ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'
                    """)
                    context.log.info("  ✓ Strict mode: enforces data validation")
                target_conn.commit()
        else:
            context.log.info("  ℹ️  Using target database's default SQL mode")
        
        # Create migrator and execute
        migrator = RegionalDataMigrator(source_conn, target_conn, context)
        
        results = migrator.extract_and_migrate_regional_data(
            parent_table=config.parent_table,
            parent_id_column=config.parent_id_column,
            parent_id_value=config.parent_id_value,
            batch_size=config.batch_size,
            recreate_tables=config.recreate_tables,
            truncate_before_load=config.truncate_before_load,
            skip_validation=config.skip_validation
        )
        
        if results['total_rows_loaded'] == 0:
            context.log.warning("⚠️  No data migrated")
            return Output({
                "status": "skipped",
                "reason": "no_data",
                "duration": round(time.time() - start_time, 2)
            })
        
        # Calculate statistics
        duration = time.time() - start_time
        
        # Log completion
        logger.info(
            "civ_migration_complete",
            source_resource=SOURCE_RESOURCE,
            target_resource=TARGET_RESOURCE,
            parent_table=config.parent_table,
            parent_id=config.parent_id_value,
            tables_created=results["tables_created"],
            tables_loaded=results["tables_loaded"],
            tables_failed=results["tables_failed"],
            total_rows=results["total_rows_loaded"],
            duration=round(duration, 2),
            truncate_mode=config.truncate_before_load
        )
        
        # Create metadata for Dagster UI
        metadata = {
            "source_resource": MetadataValue.text(SOURCE_RESOURCE),
            "target_resource": MetadataValue.text(TARGET_RESOURCE),
            "source_database": MetadataValue.text(source_resource.database),
            "target_database": MetadataValue.text(target_resource.database),
            "parent_table": MetadataValue.text(config.parent_table),
            "parent_id": MetadataValue.int(config.parent_id_value),
            "tables_created": MetadataValue.int(results["tables_created"]),
            "tables_loaded": MetadataValue.int(results["tables_loaded"]),
            "tables_failed": MetadataValue.int(results["tables_failed"]),
            "total_rows": MetadataValue.int(results["total_rows_loaded"]),
            "duration_seconds": MetadataValue.float(round(duration, 2)),
            "ssl_enabled": MetadataValue.bool(not is_local_target),
            "truncate_mode": MetadataValue.bool(config.truncate_before_load),
            "validation_enabled": MetadataValue.bool(not config.skip_validation),
        }
        
        # Add table details as markdown
        if results['details']:
            details_md = "## Migration Details\n\n"
            details_md += "| Table | Status | Rows | Duration |\n"
            details_md += "|-------|--------|------|----------|\n"
            
            for detail in results['details']:
                if detail['status'] == 'success':
                    details_md += (
                        f"| {detail['table']} | ✅ Success | "
                        f"{detail['rows']:,} | {detail['duration']}s |\n"
                    )
                elif detail['status'] == 'skipped':
                    details_md += (
                        f"| {detail['table']} | ⊗ Skipped | - | "
                        f"{detail.get('reason', 'N/A')} |\n"
                    )
                else:
                    details_md += (
                        f"| {detail['table']} | ❌ Failed | - | "
                        f"{detail.get('error', 'Unknown error')} |\n"
                    )
            
            metadata["migration_details"] = MetadataValue.md(details_md)
        
        # Return results
        return Output(
            {
                "status": "success",
                "source_resource": SOURCE_RESOURCE,
                "target_resource": TARGET_RESOURCE,
                "tables_created": results["tables_created"],
                "tables_loaded": results["tables_loaded"],
                "tables_failed": results["tables_failed"],
                "total_rows": results["total_rows_loaded"],
                "duration": round(duration, 2),
                "truncate_mode": config.truncate_before_load,
                "details": results["details"]
            },
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(
            "civ_migration_failed",
            source_resource=SOURCE_RESOURCE,
            target_resource=TARGET_RESOURCE,
            error=str(e),
            exc_info=True
        )
        raise
        
    finally:
        # Always close connections
        if source_conn:
            source_conn.close()
            context.log.info("🔌 Source connection closed")
        if target_conn:
            target_conn.close()
            context.log.info("🔌 Target connection closed")


# ============================================================================
# EXPORT
# ============================================================================

assets = [civ_regional_data_migration]