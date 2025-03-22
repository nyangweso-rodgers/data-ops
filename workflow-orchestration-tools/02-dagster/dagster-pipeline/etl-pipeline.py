# dagster_pipeline/etl_pipeline.py
from dagster import asset, job
from sqlalchemy import create_engine
import clickhouse_connect

@asset
def postgres_data():
    # Connect to Postgres (using your docker-compose service name)
    engine = create_engine("postgresql://admin:admin@postgres-db:5432/postgres")
    # Example: Fetch all rows from a table named 'orders'
    return engine.execute("SELECT * FROM customers").fetchall()

@asset
def clickhouse_table(postgres_data):
    # Connect to ClickHouse (using your docker-compose service name)
    client = clickhouse_connect.get_client(host="clickhouse-server", port=9000)
    # Example: Insert into a ClickHouse table named 'orders'
    client.insert("customers", postgres_data, column_names=["id", "created_by", "updated_by", "created_at", "updated_at"])
    return True

@job
def postgres_to_clickhouse():
    clickhouse_table(postgres_data())