from datetime import timedelta
from typing import Dict, Any

# Default arguments for all DAGs
DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['rodgerso65@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Common database connection IDs
CONNECTION_IDS = {
    'mysql_amtdb': 'mysql_amtdb',
    'postgres_ep_stage': 'postgres_ep_stage',
    'postgres_reporting_service': 'postgres-reporting-service-db',
    'postgres_ep': 'postgres-sunculture-ep-db',
    'clickhouse_cloud': 'clickhouse_cloud',
}

# Log levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50,
}


# Sync configurations for source-to-target data pipelines
SYNC_CONFIGS: Dict[str, Dict[str, Any]] = {
    'mysql_amt_customers_to_clickhouse_cloud': {
        'source': {
            'connection_id': CONNECTION_IDS['mysql_amtdb'],
            'database': 'amt',
            'schema': None,  # MySQL schema (same as database in this case)
            'table': 'customers',
            'source_type': 'mysql',
            'source_subpath': 'amt',
        },
        'target': {
            'connection_id': CONNECTION_IDS['clickhouse_cloud'],
            'database': 'test',
            'schema': None,  # ClickHouse doesn't use schemas in the same way
            'table': 'customers',
            'target_type': 'clickhouse',
            'engine': 'ReplacingMergeTree(updated_at)',
            'order_by': 'id',
            'partition_by': 'toYYYYMM(updated_at)',  # ClickHouse partitioning expression
        },
    },
    # Add more sync configs as needed
}