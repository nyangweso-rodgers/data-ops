# dagster_pipeline/assets/sync_accounts.py
from dagster import asset, HourlyPartitionsDefinition
from dagster_pipeline.utils.base_sync import BaseSyncConfig, execute_table_sync

class AccountsSyncConfig(BaseSyncConfig):
    """Account-specific sync configuration with predefined defaults"""
    table_name: str = "accounts"
    source_resource: str = "sc_amt_replica_mysql_db"
    destination_resource: str = "sc_reporting_service_pg_db"
    incremental_column: str = "last_modified"
    batch_size: int = 10000  # Smaller batches for more frequent sync
    
    # Account-specific field requirements (must be explicit)
    selected_fields: list = [
        "createdAt",
        "updatedAt",
        "id",
        "customerId",
        "accountTypeId",
        "accountRef",
        "status",
        "jsfDate",
        "jsfId",
        "parentAccountId",
        "dispatchDate",
        "expctedStartDate",
        "firstInstallmentDate",
        "installationId",
        "installationDate",
        "depositPaymentId",
        "fullDepositDate",
        "salesAgents",
        "assignmentId",
        "assignmentDate"
    ]
    
    # Account field mapping (if needed)
    field_mapping: dict = {
        "createdAt": "created_at",
        "updatedAt" : "updated_at",
        "id": "id",
        "customerId": "customer_id",
        "accountTypeId" : "account_type_id",
        "accountRef" : "account_ref",
        "status": "status",
        "jsfDate" :"jsf_date",
        "jsfId": "jsf_id",
        "parentAccountId": "parent_account_id",
        "dispatchDate": "dispatch_date",
        "expctedStartDate": "expected_start_date",
        "firstInstallmentDate": "first_installment_date",
        "installationId" : "installation_id",
        "installationDate": "installation_date",
        "depositPaymentId": "deposit_payment_id",
        "fullDepositDate": "full_deposit_date",
        "salesAgents": "sales_agents",
        "assignmentId": "assignment_id",
        "assignmentDate": "assignment_date"
    }
    
    # Account table schema
    table_schema: dict = {
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
        "id": "INTEGER PRIMARY KEY",
        "customer_id": "INTEGER",
        "account_type_id": "INTEGER",   
        "account_ref": "VARCHAR(255)",
        "status": "VARCHAR(50)",
        "jsf_date": "DATE",
        "jsf_id": "INTEGER",
        "parent_account_id": "INTEGER",
        "dispatch_date": "DATE",    
        "expected_start_date": "DATE",
        "first_installment_date": "DATE",
        "installation_id": "INTEGER",
        "installation_date": "DATE",
        "deposit_payment_id": "INTEGER",
        "full_deposit_date": "DATE",
        "sales_agents": "INTEGER",
        "assignment_id": "INTEGER",
        "assignment_date": "DATE"
    }


@asset(
    name="sync_accounts", 
    partitions_def=HourlyPartitionsDefinition(start_date="2025-01-01"),
    description="Sync account data from MySQL to PostgreSQL - runs every 15 minutes during business hours"
)
def sync_accounts(context, config: AccountsSyncConfig):
    """
    Account data sync asset with explicit field specification
    - Source: MySQL accounts table
    - Target: PostgreSQL accounts table with foreign key to customers
    - Schedule: Every 15 minutes during business hours
    """
    return execute_table_sync(context, config)