# dagster_pipeline/assets/sync_customers.py
from dagster import asset, DailyPartitionsDefinition
from dagster_pipeline.utils.base_sync import BaseSyncConfig, execute_table_sync
from typing import Optional

class CustomersSyncConfig(BaseSyncConfig):
    """Customer-specific sync configuration"""
    sync_mode: str = "incremental"
    batch_size: int = 15000
    destination_schema: str = "public"
    incremental_column: str = "updatedAt"
    
     # These are fixed for customers, but could be made configurable if needed
    table_name: str = "customers"
    source_resource: str = "sc_amt_replica_mysql_db"
    destination_resource: str = "sc_reporting_service_pg_db"
    
    # Customer-specific field requirements
    selected_fields: list = [
       "id",
       "companyRegionId",
       "customerTypeId",
       "name",
       "phoneNumber",
       "gender",
       "interests",
       "customerSource",
       "referredById",
       "referralName",
       "referralPhoneNumber",
       "creditCheck",
       "createdAt",
       "updatedAt",
       "salesAgents"
    ]
    
    # Customer field mapping (camelCase to snake_case)
    field_mapping: dict = {
        "id": "id",
        "companyRegionId": "company_region_id",
        "customerTypeId": "customer_type_id",
        "name": "name",
        "phoneNumber": "phone_number",
        "gender": "gender",
        "interests": "interests",
        "customerSource": "customer_source",
        "referredById": "referred_by_id",
        "referralName": "referral_name",    
        "referralPhoneNumber": "referral_phone_number",
        "creditCheck": "credit_check",
        "createdAt": "created_at",
        "updatedAt": "updated_at",
        "salesAgents": "sales_agents"
    }
    
    # Customer table schema (PostgreSQL destination)
    table_schema: dict = {
        "id": "INTEGER PRIMARY KEY",
        "company_region_id": "INTEGER",
        "customer_type_id": "INTEGER",
        "name": "VARCHAR(255)",
        "phone_number": "VARCHAR(50)",
        "gender": "VARCHAR(20)",
        "interests": "TEXT",
        "customer_source": "VARCHAR(100)",
        "referred_by_id": "INTEGER",
        "referral_name": "VARCHAR(255)",
        "referral_phone_number": "VARCHAR(50)",
        "credit_check": "VARCHAR(100)",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
        "sales_agents": "INTEGER"
    }


@asset(
    name="sync_customers",
    partitions_def=DailyPartitionsDefinition(start_date="2025-01-01"),
    description="Sync customer data from MySQL to PostgreSQL",
    required_resource_keys={"sc_amt_replica_mysql_db", "sc_reporting_service_pg_db"}
)
def sync_customers(context, config: CustomersSyncConfig):
    """
    Customer data sync asset with explicit field specification and mapping
    - Source: MySQL customers table (camelCase fields)
    - Target: PostgreSQL customers table (snake_case fields)
    - Schedule: Daily incremental sync
    """
    return execute_table_sync(context, config)