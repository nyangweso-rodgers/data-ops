# dagster_pipeline/assets/clickhouse/ingest/from_postgres/builder.py
"""
PostgreSQL → ClickHouse ingestion builder

Only the Postgres (source) side lives here - everything else is shared via
_shared/base_builder.py.
"""

from typing import Any, Dict, Optional

from dagster import AssetExecutionContext

from dagster_pipeline.assets.clickhouse.ingest._shared.base_builder import ClickHouseIngestBuilder
from dagster_pipeline.connectors.sources.postgres_source_connector import PostgresSourceConnector
from dagster_pipeline.utils.schema_loader import TableSchema


class PostgresToClickHouseBuilder(ClickHouseIngestBuilder):
    def source_type(self) -> str:
        return "postgres"

    def get_source_connector(self, context: AssetExecutionContext):
        """Create PostgreSQL source connector"""
        postgres_res = getattr(context.resources, self.resource_key, None)

        if postgres_res is None:
            available = [attr for attr in dir(context.resources) if not attr.startswith('_')]
            self.logger.error("postgres_resource_not_found", requested=self.resource_key, available=available)
            raise ValueError(
                f"Postgres resource '{self.resource_key}' not found. "
                f"Available resources: {available}"
            )

        config = {
            **postgres_res.get_config(),
            "database": self.source_database,
            "table": self.source_table,
        }

        self.logger.debug("postgres_connector_created")
        return PostgresSourceConnector(context, config)

    def validate_and_correct_incremental_key(self, context: AssetExecutionContext, schema: TableSchema) -> Optional[str]:
        """
        Validate incremental key exists in schema

        Postgres folds unquoted identifiers to lowercase, so fall back to the
        lowercase key before failing.
        """
        if not self.incremental_key:
            self.logger.info("no_incremental_key")
            return None

        column_names = schema.get_column_names(use_source_names=True)

        if self.incremental_key in column_names:
            self.logger.info("incremental_key_validated", key=self.incremental_key)
            context.log.info(f"✅ Incremental key validated: {self.incremental_key}")
            return self.incremental_key

        incremental_key_lower = self.incremental_key.lower()
        if incremental_key_lower in column_names:
            self.logger.warning("incremental_key_case_corrected", requested=self.incremental_key, corrected=incremental_key_lower)
            context.log.warning(
                f"⚠️ Incremental key found with different case: '{self.incremental_key}' → '{incremental_key_lower}'"
            )
            return incremental_key_lower

        self._raise_incremental_key_not_found(column_names)


def build_postgres_to_clickhouse_asset(spec: Dict[str, Any]):
    """Build one PostgreSQL → ClickHouse asset from a table spec (see utils/ingest_config_loader.py)"""
    return PostgresToClickHouseBuilder(**spec).build()
