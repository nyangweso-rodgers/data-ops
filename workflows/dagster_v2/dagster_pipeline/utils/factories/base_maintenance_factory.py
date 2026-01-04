# dagster_pipeline/utils/factories/base_maintenance_factory.py
"""
Abstract base factory for database maintenance operations

Unlike ETL factories (which move data between systems), maintenance factories
perform operations on a single system like deduplication, optimization, or cleanup.

Architecture:
- Single-system operations (e.g., ClickHouse only)
- Partition or table-level operations
- No schema loading or type mapping needed
- Returns operation statistics and metadata
- Can be scheduled independently of ETL jobs

Usage:
    class ClickHouseCleanupFactory(BaseMaintenanceFactory):
        def maintenance_type(self) -> str:
            return "clickhouse_deduplication"
        
        def get_required_resource_keys(self) -> set:
            return {"clickhouse_resource"}
        
        def perform_maintenance(self, context, client):
            # Implementation
            pass
    
    factory = ClickHouseCleanupFactory(
        asset_name="cleanup_leads_table",
        database="sales-service",
        table="leads_v2"
    )
    
    asset = factory.build()
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from dagster import asset, AssetExecutionContext, Output, MetadataValue
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class BaseMaintenanceFactory(ABC):
    """
    Abstract base class for database maintenance operations
    
    Key Features:
    - Single-system operations (no source/destination split)
    - Flexible operation types (cleanup, optimization, stats, etc.)
    - Rich metadata and logging
    - Error handling with proper Dagster integration
    - Scheduling-friendly (designed for cron jobs)
    
    Subclasses should implement:
    - maintenance_type(): Operation identifier
    - get_required_resource_keys(): Resource dependencies
    - perform_maintenance(): Core operation logic
    """
    
    def __init__(
        self,
        asset_name: str,
        group_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ):
        self.asset_name = asset_name
        self.group_name = group_name or "database_maintenance"
        self.tags = tags or {}
        self.custom_description = description
        
        # Add maintenance metadata to tags
        self.tags.update({
            "operation_type": "maintenance",
            "maintenance_type": self.maintenance_type(),
        })
    
    # ========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ========================================================================
    
    @abstractmethod
    def maintenance_type(self) -> str:
        """
        Return maintenance operation type identifier
        
        Examples: 'deduplication', 'vacuum', 'optimize', 'stats_collection'
        """
        pass
    
    @abstractmethod
    def get_required_resource_keys(self) -> set:
        """
        Return set of required resource keys
        
        Example:
            return {"clickhouse_resource"}
        """
        pass
    
    @abstractmethod
    def perform_maintenance(
        self,
        context: AssetExecutionContext,
        **resources
    ) -> Dict[str, Any]:
        """
        Perform the maintenance operation
        
        Args:
            context: Dagster execution context
            **resources: Resource instances (e.g., client connections)
        
        Returns:
            Dictionary with operation results:
            {
                "status": "success" | "no_action_needed" | "partial_success",
                "items_processed": int,
                "items_modified": int,
                "operation_details": {...},
                "warnings": [...],
                "duration_seconds": float,
            }
        
        Raises:
            Exception: On critical failure
        """
        pass
    
    # ========================================================================
    # OPTIONAL METHODS - Can be overridden
    # ========================================================================
    
    def get_asset_description(self) -> str:
        """
        Generate asset description
        
        Override to customize description
        """
        if self.custom_description:
            return self.custom_description
        
        return f"Database maintenance: {self.maintenance_type()}"
    
    def validate_configuration(self, context: AssetExecutionContext) -> bool:
        """
        Validate configuration before running maintenance
        
        Override to add custom validation logic
        
        Args:
            context: Dagster execution context
        
        Returns:
            True if valid, raises ValueError if invalid
        """
        return True
    
    def pre_maintenance_hook(
        self,
        context: AssetExecutionContext,
        **resources
    ):
        """
        Hook called before maintenance operation
        
        Override to add custom pre-operation logic:
        - Backup critical data
        - Lock tables
        - Send notifications
        """
        pass
    
    def post_maintenance_hook(
        self,
        context: AssetExecutionContext,
        result: Dict[str, Any],
        **resources
    ):
        """
        Hook called after maintenance operation
        
        Override to add custom post-operation logic:
        - Verify results
        - Send notifications
        - Trigger dependent jobs
        """
        pass
    
    def format_metadata(
        self,
        result: Dict[str, Any]
    ) -> Dict[str, MetadataValue]:
        """
        Format operation results as Dagster metadata
        
        Override to customize metadata display in Dagster UI
        
        Args:
            result: Operation result dictionary
        
        Returns:
            Dictionary of Dagster MetadataValue objects
        """
        metadata = {
            "status": MetadataValue.text(result.get("status", "unknown")),
            "operation_type": MetadataValue.text(self.maintenance_type()),
        }
        
        # Add numeric metrics
        if "items_processed" in result:
            metadata["items_processed"] = MetadataValue.int(result["items_processed"])
        
        if "items_modified" in result:
            metadata["items_modified"] = MetadataValue.int(result["items_modified"])
        
        if "duration_seconds" in result:
            metadata["duration_seconds"] = MetadataValue.float(result["duration_seconds"])
        
        # Add warnings if present
        if result.get("warnings"):
            metadata["warnings_count"] = MetadataValue.int(len(result["warnings"]))
            metadata["warnings"] = MetadataValue.text("\n".join(result["warnings"]))
        
        return metadata
    
    # ========================================================================
    # MAIN BUILD METHOD
    # ========================================================================
    
    def build(self) -> Callable:
        """
        Build and return Dagster asset function
        
        Returns:
            Decorated Dagster asset function
        """
        
        def _maintenance_asset(context: AssetExecutionContext) -> Output:
            """Generated maintenance asset"""
            
            start_time = datetime.now()
            
            context.log.info("=" * 80)
            context.log.info(f"🔧 MAINTENANCE START: {self.asset_name}")
            context.log.info(f"📋 Operation: {self.maintenance_type()}")
            context.log.info("=" * 80)
            
            try:
                # ============================================================
                # STEP 1: VALIDATE CONFIGURATION
                # ============================================================
                context.log.info("✓ STEP 1: Validating configuration...")
                
                self.validate_configuration(context)
                context.log.info("✅ Configuration valid")
                
                # ============================================================
                # STEP 2: GATHER RESOURCES
                # ============================================================
                context.log.info("🔌 STEP 2: Gathering resources...")
                
                resources = {}
                for resource_key in self.get_required_resource_keys():
                    if not hasattr(context.resources, resource_key):
                        raise ValueError(
                            f"Required resource '{resource_key}' not available. "
                            f"Add it to Definitions resources."
                        )
                    resources[resource_key] = getattr(context.resources, resource_key)
                
                context.log.info(f"✅ Resources gathered: {list(resources.keys())}")
                
                # ============================================================
                # STEP 3: PRE-MAINTENANCE HOOK
                # ============================================================
                context.log.info("🎣 STEP 3: Running pre-maintenance hook...")
                
                self.pre_maintenance_hook(context, **resources)
                context.log.info("✅ Pre-maintenance hook complete")
                
                # ============================================================
                # STEP 4: PERFORM MAINTENANCE
                # ============================================================
                context.log.info(f"🔨 STEP 4: Performing {self.maintenance_type()}...")
                
                result = self.perform_maintenance(context, **resources)
                
                # Ensure result has required fields
                if "status" not in result:
                    result["status"] = "success"
                
                if "duration_seconds" not in result:
                    result["duration_seconds"] = (datetime.now() - start_time).total_seconds()
                
                context.log.info(f"✅ Maintenance complete: {result['status']}")
                
                # ============================================================
                # STEP 5: POST-MAINTENANCE HOOK
                # ============================================================
                context.log.info("🎣 STEP 5: Running post-maintenance hook...")
                
                self.post_maintenance_hook(context, result, **resources)
                context.log.info("✅ Post-maintenance hook complete")
                
                # ============================================================
                # FINALIZE
                # ============================================================
                duration = (datetime.now() - start_time).total_seconds()
                result["total_duration_seconds"] = duration
                
                # Format metadata
                metadata = self.format_metadata(result)
                
                # Log summary
                context.log.info("=" * 80)
                context.log.info(f"🎉 MAINTENANCE COMPLETE: {result['status']}")
                
                if "items_processed" in result:
                    context.log.info(f"   Items processed: {result['items_processed']:,}")
                
                if "items_modified" in result:
                    context.log.info(f"   Items modified: {result['items_modified']:,}")
                
                context.log.info(f"   Duration: {duration:.2f}s")
                
                if result.get("warnings"):
                    context.log.info(f"   ⚠️  Warnings: {len(result['warnings'])}")
                
                context.log.info("=" * 80)
                
                return Output(result, metadata=metadata)
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                context.log.error("=" * 80)
                context.log.error(f"❌ MAINTENANCE FAILED after {duration:.2f}s")
                context.log.error(f"❌ Error: {str(e)}")
                context.log.error("=" * 80)
                
                # Re-raise so Dagster marks as failed
                raise
        
        # Get required resource keys
        required_keys = self.get_required_resource_keys()
        
        # Apply @asset decorator
        return asset(
            name=self.asset_name,
            group_name=self.group_name,
            compute_kind=self.maintenance_type().upper(),
            description=self.get_asset_description(),
            tags=self.tags,
            required_resource_keys=required_keys,
        )(_maintenance_asset)