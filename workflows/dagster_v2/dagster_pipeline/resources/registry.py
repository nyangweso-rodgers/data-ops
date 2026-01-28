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
# MySQL - LOCAL DB (for local development) 
# ═════════════════════════════════════════════════════════════════════════════
local_mysql_db_resource = MySQLResource(
    host=EnvVar("LOCAL_MYSQL_DB_HOST"),
    port=3306, 
    user=EnvVar("LOCAL_MYSQL_DB_USER"),
    password=EnvVar("LOCAL_MYSQL_DB_PASSWORD"),
    database=EnvVar("LOCAL_MYSQL_DB_NAME")
)

# ═════════════════════════════════════════════════════════════════════════════
# MySQL - AMTDB RESOURCE
# ═════════════════════════════════════════════════════════════════════════════

mysql_amt = MySQLResource(
    host=EnvVar("SC_AMT_REPLICA_MYSQL_DB_HOST"),
    port=3306, 
    user=EnvVar("SC_AMT_REPLICA_MYSQL_DB_USER"),
    password=EnvVar("SC_AMT_REPLICA_MYSQL_DB_PASSWORD"),
    database=EnvVar("SC_AMT_REPLICA_MYSQL_DB_NAME")
)

# ═════════════════════════════════════════════════════════════════════════════
# MySQL - SC AMTDB REPLICA RESOURCE
# ═════════════════════════════════════════════════════════════════════════════
sc_mysql_amtdb_replica_resource = MySQLResource(
    host=EnvVar("SC_MYSQL_AMTDB_v39_REPLICA_HOST"),
    port=3306,
    user=EnvVar("SC_MYSQL_AMTDB_v39_REPLICA_USER"),
    password=EnvVar("SC_MYSQL_AMTDB_v39_REPLICA_PASSWORD"),
    database=EnvVar("SC_MYSQL_AMTDB_v39_REPLICA_DB")
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
# MySQL - GRDATA DB
# ═════════════════════════════════════════════════════════════════════════════
grdata_mysql_db_resource = MySQLResource(
    host=EnvVar("GRDATA_MYSQL_DB_HOST"),
    port=3306, 
    user=EnvVar("GRDATA_MYSQL_DB_USER"),
    password=EnvVar("GRDATA_MYSQL_DB_PASSWORD"),
    database=EnvVar("GRDATA_MYSQL_DB_NAME")
    )

# ═══════════════════════════════════════════════════════════════════════════
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