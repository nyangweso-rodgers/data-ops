# dagster_pipeline/assets/clickhouse/ingest/from_mysql/builder.py
"""
MySQL → ClickHouse ingestion builder

Only the MySQL (source) side lives here - everything else is shared via
_shared/base_builder.py.
"""

from typing import Any, Dict

from dagster import AssetExecutionContext

from dagster_pipeline.assets.clickhouse.ingest._shared.base_builder import ClickHouseIngestBuilder
from dagster_pipeline.connectors.sources.mysql_source_connector import MySQLSourceConnector


class MySQLToClickHouseBuilder(ClickHouseIngestBuilder):
    def source_type(self) -> str:
        return "mysql"

    def get_source_connector(self, context: AssetExecutionContext):
        """Create MySQL source connector"""
        mysql_res = getattr(context.resources, self.resource_key, None)

        if mysql_res is None:
            available = [attr for attr in dir(context.resources) if not attr.startswith('_')]
            self.logger.error("mysql_resource_not_found", requested=self.resource_key, available=available)
            raise ValueError(
                f"MySQL resource '{self.resource_key}' not found. "
                f"Available resources: {available}"
            )

        config = {
            **mysql_res.get_config(),
            "database": self.source_database,
            "table": self.source_table,
        }

        self.logger.debug("mysql_connector_created")
        return MySQLSourceConnector(context, config)


def build_mysql_to_clickhouse_asset(spec: Dict[str, Any]):
    """Build one MySQL → ClickHouse asset from a table spec (see utils/ingest_config_loader.py)"""
    return MySQLToClickHouseBuilder(**spec).build()
