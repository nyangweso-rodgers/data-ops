from typing import Dict, Any, List
import pandas as pd
from dagster import AssetExecutionContext
from datetime import datetime


class ETLUtils:
    """Common ETL transformation utilities"""
    
    @staticmethod
    def get_source_columns(schema: Dict[str, Any]) -> List[str]:
        """Extract source column names from schema"""
        return [col['name'] for col in schema['columns']]
    
    @staticmethod
    def get_target_columns(schema: Dict[str, Any]) -> List[str]:
        """Extract target column names from schema"""
        return [col['target_name'] for col in schema['columns']]
    
    @staticmethod
    def get_primary_keys(schema: Dict[str, Any]) -> List[str]:
        """Extract primary key columns from schema"""
        return [
            col['target_name'] 
            for col in schema['columns'] 
            if col.get('primary_key', False)
        ]
    
    @staticmethod
    def transform_data(
        context: AssetExecutionContext,
        df: pd.DataFrame,
        schema: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Transform data according to schema mappings
        
        Args:
            context: Dagster execution context
            df: Source DataFrame
            schema: Schema configuration
            
        Returns:
            Transformed DataFrame
        """
        if df.empty:
            context.log.warning("Empty DataFrame provided for transformation")
            return df
        
        context.log.info(f"Transforming {len(df)} rows according to schema")
        
        df_transformed = df.copy()
        
        # Rename columns according to mapping
        column_mapping = {
            col['name']: col['target_name'] 
            for col in schema['columns']
        }
        df_transformed = df_transformed.rename(columns=column_mapping)
        context.log.info(f"Renamed columns: {list(column_mapping.keys())} -> {list(column_mapping.values())}")
        
        # Handle NULL backfill rules (column-specific)
        context.log.info("Applying NULL backfill rules...")
        for col in schema['columns']:
            target_name = col['target_name']
            
            # Only process if column has explicit backfill configuration
            backfill_config = col.get('backfill_from')
            
            if not backfill_config:
                # No backfill rule for this column, skip
                continue
            
            if target_name not in df_transformed.columns:
                context.log.warning(f"Target column {target_name} not found in data, skipping backfill")
                continue
            
            source_col = backfill_config
            
            if source_col not in df_transformed.columns:
                context.log.warning(f"Backfill source column {source_col} not found in data for {target_name}, skipping")
                continue
            
            # Find rows where target column is NULL
            null_mask = df_transformed[target_name].isna()
            num_nulls = null_mask.sum()
            
            if num_nulls > 0:
                # Fill NULLs with values from source column
                df_transformed.loc[null_mask, target_name] = df_transformed.loc[null_mask, source_col]
                context.log.info(f"Backfilled {num_nulls} NULL values in {target_name} from {source_col}")
            else:
                context.log.info(f"No NULL values found in {target_name}, no backfill needed")
        
        # Add sync metadata if enabled
        sync_metadata = schema['target'].get('sync_metadata', {})
        if sync_metadata.get('enabled', False):
            for col_name, col_config in sync_metadata.get('columns', {}).items():
                if col_config.get('enabled', False):
                    # Handle different metadata column types
                    if col_name in ['sync_at', '_sync_timestamp']:
                        df_transformed[col_name] = datetime.now()
                        context.log.info(f"Added sync metadata column: {col_name}")
                    elif col_name in ['_sync_date']:
                        df_transformed[col_name] = datetime.now().date()
                        context.log.info(f"Added sync metadata column: {col_name}")
        
        context.log.info(f"✓ Transformation complete. Shape: {df_transformed.shape}")
        
        return df_transformed