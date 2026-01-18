# dagster_pipeline/resources/registry.py
"""
Central registry of all MySQL, PostgreSQL, and ClickHouse source instances.

IMPORTANT: All PostgreSQL resources now REQUIRE explicit schema specification.
"""

from dagster import EnvVar
from .mysql_resource import MySQLResource
from .postgres_resource import PostgreSQLResource
from .clickhouse_resource import ClickHouseResource
from .dagster_postgres_resource import DagsterPostgresResource

# ═════════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE RESOURCES (Dagster state management, etc.)
# ═════════════════════════════════════════════════════════════════════════════

dagster_postgres_resource = DagsterPostgresResource(
    host=EnvVar("DAGSTER_PG_DB_HOST"),
    port=5432,
    user=EnvVar("DAGSTER_PG_DB_USER"),
    password=EnvVar("DAGSTER_PG_DB_PASSWORD"),
    database=EnvVar("DAGSTER_PG_DB_NAME"),
    db_schema="dagster",  # ← REQUIRED: Dagster metadata schema
)

# ═════════════════════════════════════════════════════════════════════════════
# MySQL - AMT 
# ═════════════════════════════════════════════════════════════════════════════

mysql_amt = MySQLResource(
    host=EnvVar("SC_AMT_REPLICA_MYSQL_DB_HOST"),
    port=3306, 
    user=EnvVar("SC_AMT_REPLICA_MYSQL_DB_USER"),
    password=EnvVar("SC_AMT_REPLICA_MYSQL_DB_PASSWORD"),
    database=EnvVar("SC_AMT_REPLICA_MYSQL_DB_NAME")
)

# ═════════════════════════════════════════════════════════════════════════════
# MySQL - SALES SERVICE DEV RESOURCE
# ═════════════════════════════════════════════════════════════════════════════

mysql_sales_service_dev = MySQLResource(
    host=EnvVar("SC_SALES_SERVICE_DEV_MYSQL_DB_HOST"),
    port=3306,
    user=EnvVar("SC_SALES_SERVICE_DEV_MYSQL_DB_USER"),
    password=EnvVar("SC_SALES_SERVICE_DEV_MYSQL_DB_PASSWORD"),
    database=EnvVar("SC_SALES_SERVICE_DEV_MYSQL_DB_NAME")
)

# ═════════════════════════════════════════════════════════════════════════════
# MySQL - SALES SERVICE PROD RESOURCE
# ═════════════════════════════════════════════════════════════════════════════

mysql_sales_service = MySQLResource(
    host=EnvVar("SC_SALES_SERVICE_MYSQL_DB_HOST"),
    port=3306,
    user=EnvVar("SC_SALES_SERVICE_MYSQL_DB_USER"),
    password=EnvVar("SC_SALES_SERVICE_MYSQL_DB_PASSWORD"),
    database=EnvVar("SC_SALES_SERVICE_MYSQL_DB_NAME")
)

# ═════════════════════════════════════════════════════════════════════════════
# MySQL - Soil Testing Prod
# ═════════════════════════════════════════════════════════════════════════════

mysql_soil_testing_prod_db = MySQLResource(
    host=EnvVar("SC_SOIL_TESTING_PROD_MYSQL_DB_HOST"),
    port=3306,
    user=EnvVar("SC_SOIL_TESTING_PROD_MYSQL_DB_USER"),
    password=EnvVar("SC_SOIL_TESTING_PROD_MYSQL_DB_PASSWORD"),
    database=EnvVar("SC_SOIL_TESTING_PROD_MYSQL_DB_NAME")
)

# ═════════════════════════════════════════════════════════════════════════════
# ClickHouse Cloud
# ═════════════════════════════════════════════════════════════════════════════

clickhouse_resource = ClickHouseResource(
    host=EnvVar("SC_CH_DB_HOST"),
    port=8443,
    user=EnvVar("SC_CH_DB_USER"),
    password=EnvVar("SC_CH_DB_PASSWORD"),
    secure=False,
)

# ═════════════════════════════════════════════════════════════════════════════
# PostgreSQL - FMA
# ═════════════════════════════════════════════════════════════════════════════

postgres_fma = PostgreSQLResource(
    host=EnvVar("SC_EP_PG_DB_HOST"),
    port=5432,
    user=EnvVar("SC_EP_PG_DB_USER"),
    password=EnvVar("SC_EP_PG_DB_PASSWORD"),
    database=EnvVar("SC_EP_PG_DB_NAME"),
    db_schema="public",  # ← REQUIRED: FMA data schema (change if different)
)