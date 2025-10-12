# dagster_pipeline/utils/state_manager.py
"""
State management using Dagster's built-in kvs table
No need to create additional tables
"""

from typing import Dict, Any, Optional
from dagster import AssetExecutionContext
from dagster_pipeline.resources.databases.v1.databases import PostgreSQLResource
import json


class StateManager:
    """Manages ETL state using Dagster's kvs table"""
    
    @staticmethod
    def _get_state_key(source_type: str, source_database: str, source_table: str) -> str:
        """Generate a unique key for kvs table"""
        return f"etl_sync_state:{source_type}:{source_database}:{source_table}"
    
    @staticmethod
    def load_incremental_state(
        context: AssetExecutionContext,
        postgres_resource: PostgreSQLResource,
        source_type: str,
        source_database: str,
        source_table: str
    ) -> Optional[Dict[str, Any]]:
        """Load the incremental state from Dagster's kvs table"""
        
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        query = """
            SELECT value FROM kvs
            WHERE key = %s
        """
        
        try:
            with postgres_resource.get_connection("dagster") as conn:
                cursor = conn.cursor()
                cursor.execute(query, (key,))
                result = cursor.fetchone()
                cursor.close()
                
                if result is None:
                    context.log.info(f"No previous state found for {source_type}.{source_database}.{source_table}")
                    return None
                
                state = json.loads(result[0])
                context.log.info(f"Loaded state from kvs: {state}")
                return state
                
        except Exception as e:
            context.log.warning(f"Failed to load state from kvs: {e}")
            return None
    
    @staticmethod
    def save_incremental_state(
        context: AssetExecutionContext,
        postgres_resource: PostgreSQLResource,
        source_type: str,
        source_database: str,
        source_table: str,
        incremental_key: str,
        last_value: Any
    ) -> None:
        """Save the incremental state to Dagster's kvs table"""
        
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        state_json = json.dumps({
            'last_value': str(last_value),
            'key': incremental_key,
            'source_type': source_type,
            'source_database': source_database,
            'source_table': source_table
        })
        
        # Upsert into kvs table
        upsert_query = """
            INSERT INTO kvs (key, value) VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """
        
        try:
            with postgres_resource.get_connection("dagster") as conn:
                cursor = conn.cursor()
                cursor.execute(upsert_query, (key, state_json))
                conn.commit()
                cursor.close()
                context.log.info(f"✓ State saved to kvs: {incremental_key} = {last_value}")
        except Exception as e:
            context.log.error(f"Failed to save state to kvs: {e}")
    
    @staticmethod
    def clear_incremental_state(
        context: AssetExecutionContext,
        postgres_resource: PostgreSQLResource,
        source_type: str,
        source_database: str,
        source_table: str
    ) -> None:
        """Clear the state for a table (for full re-syncs)"""
        
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        delete_query = """
            DELETE FROM kvs WHERE key = %s
        """
        
        try:
            with postgres_resource.get_connection("dagster") as conn:
                cursor = conn.cursor()
                cursor.execute(delete_query, (key,))
                conn.commit()
                cursor.close()
                context.log.info(f"✓ Cleared state for {source_type}.{source_database}.{source_table}")
        except Exception as e:
            context.log.warning(f"Failed to clear state: {e}")
    
    @staticmethod
    def get_all_states(
        context: AssetExecutionContext,
        postgres_resource: PostgreSQLResource
    ) -> Dict[str, Dict[str, Any]]:
        """Get all ETL sync states (for monitoring)"""
        
        query = """
            SELECT key, value FROM kvs
            WHERE key LIKE 'etl_sync_state:%'
        """
        
        try:
            with postgres_resource.get_connection("dagster") as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()
                
                states = {}
                for row in rows:
                    states[row[0]] = json.loads(row[1])
                
                return states
        except Exception as e:
            context.log.warning(f"Failed to fetch all states: {e}")
            return {}