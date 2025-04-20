from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.models import Variable
from airflow.hooks.base import BaseHook
import clickhouse_connect
import logging
from datetime import timedelta, datetime
from airflow.utils.dates import days_ago
import pendulum
import requests
from airflow.exceptions import AirflowException


# Configure logging
logger = logging.getLogger(__name__)

# Default arguments for all DAGs
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['rodgerso65@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def get_clickhouse_cloud_client():
    """
    Return a ClickHouse client instance using Airflow connection.
    Uses connection 'clickhouse_cloud' with secure setting from extra field.
    """
    try:
        conn = BaseHook.get_connection('clickhouse_cloud')
        extra = conn.extra_dejson if conn.extra else {}
        secure = extra.get('secure', True)
        client = clickhouse_connect.get_client(
            host=conn.host,
            port=conn.port or 8443,
            username=conn.login or 'default',
            password=conn.password,
            database=conn.schema,
            secure=secure
        )
        client.ping()
        logger.info("Successfully connected to ClickHouse Cloud")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ClickHouse Cloud: {str(e)}")
        raise

def get_mysql_amtdb_hook():
    conn_id = Variable.get("mysql_conn_id", default_var="mysql_amtdb")
    return MySqlHook(mysql_conn_id=conn_id)

def get_postgres_ep_stage_hook(postgres_conn_id=None):
    conn_id = postgres_conn_id or Variable.get("postgres_conn_id", default_var="postgres_ep_stage")
    return PostgresHook(postgres_conn_id=conn_id)


def get_postgres_reporting_service_db_hook():
    conn_id = Variable.get("postgres_conn_id", default_var="postgres-reporting-service-db")
    return PostgresHook(postgres_conn_id=conn_id)