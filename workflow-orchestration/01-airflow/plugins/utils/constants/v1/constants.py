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
    'clickhouse_cloud': 'clickhouse_cloud'
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
            'batch_size': 5000  # Suitable for MySQL
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
    'jira_sprints_to_postgres': {
        'source': {
            'database': None,
            'schema': None,
            'table': 'sprints',
            'source_type': 'apis',
            'source_subpath': 'jira',
            'batch_size': 100  # API limit (e.g., Jira)
        },
        'target': {
            'connection_id': CONNECTION_IDS['postgres_reporting_service'],
            'database': 'reporting-service',
            'schema': 'jira',
            'table': 'sprints',
            'target_type': 'postgres',
        },
    },
    'jira_issues_to_postgres': {
        'source': {
            'database': None,
            'schema': None,
            'table': 'issues',
            'source_type': 'apis',
            'source_subpath': 'jira',
            'batch_size': 100  # API limit (e.g., Jira)
            },
        'target':{
            'connection_id': CONNECTION_IDS['postgres_reporting_service'],
            'database': 'reporting-service',
            'schema': 'jira',
            'table': 'issues',
            'target_type': 'postgres',
            'upsert_conditions': ['id'],
        }
        },
    'mysql_amt_accounts_to_postgres': {
        'source': {
            'connection_id': CONNECTION_IDS['mysql_amtdb'],
            'database': 'amtdb',
            'schema': None,  # MySQL schema (same as database in this case)
            'table': 'accounts',
            'source_type': 'mysql',
            'source_subpath': 'amt',
            'batch_size': 5000  # Suitable for MySQL
        },
        'target': {
            'connection_id': CONNECTION_IDS['postgres_reporting_service'],
            'database': 'reporting-service',
            'schema': 'amt',
            'table': 'accounts',
            'target_type': 'postgres',
        },
    },
    'mysql_amt_products_to_postgres': {
        'source': {
            'connection_id': CONNECTION_IDS['mysql_amtdb'],
            'database': 'amtdb',
            'schema': None,
            'table': 'products',
            'source_type': 'mysql',
            'source_subpath': 'amt',
            'batch_size': 5000,
            'incremental_column': 'updatedAt'  # Matches MySQL column name
        },
        'target': {
            'connection_id': CONNECTION_IDS['postgres_reporting_service'],
            'database': 'reporting-service',
            'schema': 'amt',
            'table': 'products',
            'target_type': 'postgres',
            'upsert_conditions': ['id']
        }},
    'mysql_amt_customers_to_postgres': {
        'source': {
            'connection_id': CONNECTION_IDS['mysql_amtdb'],
            'database': 'amtdb',
            'schema': None,  # MySQL schema (same as database in this case)
            'table': 'customers',
            'source_type': 'mysql',
            'source_subpath': 'amt',
            'batch_size': 5000 
        },
        'target': {
            'connection_id': CONNECTION_IDS['postgres_reporting_service'],
            'database': 'reporting-service',
            'schema': 'amt',
            'table': 'customers',
            'target_type': 'postgres',
            'upsert_conditions': ['id'] 
        },
    },
    # Add more sync configs as needed
}