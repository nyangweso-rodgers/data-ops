from airflow.decorators import dag
from airflow.utils.dates import days_ago
from plugins.operators.mysql_to_postgres_sync_operator.v1.mysql_to_postgres_sync_operator import MySQLToPostgresSyncOperator
from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS

@dag(
    dag_id='sync_mysql_amt_products_to_postgres',
    default_args=DEFAULT_ARGS,  
    start_date=days_ago(1),
    schedule_interval='@daily',
    catchup=False,
    tags=['mysql', 'postgres', 'sync', 'amt', 'products'],
)
def sync_mysql_amt_products_to_postgres():
    """
    A DAG to sync the products table from MySQL to PostgreSQL using the custom MySQLToPostgresSyncOperator.
    """
    # Instantiate the operator for syncing the products table
    sync_products = MySQLToPostgresSyncOperator(
        task_id='sync_products',
        sync_key='mysql_amt_products_to_postgres'
    )

    # Since this is a single-task DAG, no additional dependencies are needed
    return sync_products

# Instantiate the DAG
dag = sync_mysql_amt_products_to_postgres()