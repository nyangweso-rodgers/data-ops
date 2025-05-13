from datetime import timedelta

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