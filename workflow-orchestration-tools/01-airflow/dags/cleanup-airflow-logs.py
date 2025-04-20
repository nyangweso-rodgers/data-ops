from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'airflow_log_cleanup',
    default_args=default_args,
    description='Clean up Airflow logs older than 28 days',
    schedule_interval='@daily',  # Run daily
    start_date=datetime(2025, 4, 20),
    catchup=False,
) as dag:

    cleanup_task = BashOperator(
        task_id='cleanup_airflow_logs',
        bash_command=(
            "echo 'Cleaning up logs older than 28 days...' && "
            "[ -d /opt/airflow/logs ] || { echo 'Log directory does not exist'; exit 1; } && "
            "count=$(find /opt/airflow/logs -type f -mtime +14 -print -delete | wc -l) || "
            "{ echo 'Failed to delete logs'; exit 1; } && "
            "find /opt/airflow/logs -type d -empty -delete && "
            "echo \"Deleted $count log files.\""
        ),
    )