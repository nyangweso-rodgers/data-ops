# dagster_pipeline/pipelines/etl/mysql_to_clickhouse.py
"""
All MySQL → ClickHouse ETL assets
"""

from dagster_pipeline.utils.factories.etl_mysql_to_clickhouse_factory import create_mysql_to_clickhouse_asset


# ============================================================================
# Sync MySQL AMT DB Tables → ClickHouse
# ============================================================================

mysql_amt_accounts = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_amt_accounts_to_clickhouse",
    group_name="mysql_amt_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_amt", 
    source_database="amtdb",
    source_table="accounts",
    incremental_key="updatedAt",
    
    # Destination Config (ClickHouse)
    destination_database="amt",
    destination_table="accounts_v1",  
    clickhouse_engine="ReplacingMergeTree(updatedAt)", 
    clickhouse_order_by=["id"],                         
    clickhouse_partition_by=None, 
)

# ============================================================================
# Sync MySQL Sales Service  DB Tables → ClickHouse
# ============================================================================
mysql_sales_service_leads = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_sales_service_leads_to_clickhouse",
    group_name="mysql_sales_service_to_clickhouse",
   
    # Source Config
    mysql_resource_key="mysql_sales_service",
    source_database="sales-service",
    source_table="leads",
    incremental_key="updatedAt", # Track by updatedAt for incremental sync
    
    # Destination Config (ClickHouse)
    destination_database="sales-service",
    destination_table="leads_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)",  # Deduplicate by leadId, keep latest updatedAt 
    clickhouse_order_by=["createdAt", "leadId", "updatedAt"],  # ← Daily granularity in ordering
   clickhouse_partition_by="toYYYYMM(createdAt)",  # ← Monthly instead of daily
)

mysql_sales_service_lead_channels = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_sales_service_lead_channels_to_clickhouse",
    group_name="mysql_sales_service_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_sales_service",
    source_database="sales-service",
    source_table="lead_channels",
    incremental_key="updatedAt", # Track by updatedAt for incremental sync
    
    # Destination Config (ClickHouse)
    destination_database="sales-service",
    destination_table="lead_channels_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)",  # Deduplicate by id, keep latest updatedAt 
    clickhouse_order_by=["id", "updatedAt"],  # Order by id first, then version
    clickhouse_partition_by=None,  # No partitioning needed
)

mysql_sales_service_leadsources = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_sales_service_leadsources_to_clickhouse",
    group_name="mysql_sales_service_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_sales_service",
    source_database="sales-service",
    source_table="leadsources",
    incremental_key="updatedAt",
    
    # Destination Config (ClickHouse)
    destination_database="sales-service",
    destination_table="leadsources_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)", # Use ReplacingMergeTree to keep only latest version
    clickhouse_order_by=["id"],
    clickhouse_partition_by=None, # Small table, no partitioning
)

mysql_sales_service_cds = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_sales_service_cds_to_clickhouse",
    group_name="mysql_sales_service_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_sales_service",
    source_database="sales-service",
    source_table="cds",
    incremental_key="updatedAt",
    # Destination Config (ClickHouse)
    destination_database="sales-service",
    destination_table="cds_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)",  
    clickhouse_order_by=["cdsId", "updatedAt"],  
    clickhouse_partition_by=None,  
)

mysql_sales_service_form_answers = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_sales_service_form_answers_to_clickhouse",
    group_name="mysql_sales_service_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_sales_service",
    source_database="sales-service",
    source_table="form_answers",
    incremental_key="updatedAt",
    
    # Destination Config (ClickHouse)
    destination_database="sales-service",
    destination_table="form_answers_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)",  
    clickhouse_order_by=["id", "createdAt", "updatedAt"],  
    clickhouse_partition_by=None,  
)

mysql_sales_service_kyc_requests = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_sales_service_kyc_requests_to_clickhouse",
    group_name="mysql_sales_service_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_sales_service",
    source_database="sales-service",
    source_table="kyc_requests",
    incremental_key="updatedAt",
    
    # Destination Config (ClickHouse)
    destination_database="sales-service",
    destination_table="kyc_requests_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)",  
    clickhouse_order_by=["externalRefId", "updatedAt"],  
    clickhouse_partition_by=None,  
)

mysql_sales_service_forms = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_sales_service_forms_to_clickhouse",
    group_name="mysql_sales_service_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_sales_service",
    source_database="sales-service",
    source_table="forms",
    incremental_key="updatedAt",
    
    # Destination Config (ClickHouse)
    destination_database="sales-service",
    destination_table="forms_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)",
    clickhouse_order_by=["id", "updatedAt"],
    clickhouse_partition_by=None,
)
# ============================================================================
# Sync MySQL Soil Testing Prod DB Tables → ClickHouse
# ============================================================================
mysql_soil_testing_prod_policies = create_mysql_to_clickhouse_asset(
    # Asset Identity
    asset_name="mysql_soil_testing_prod_policies_to_clickhouse",
    group_name="mysql_soil_testing_prod_to_clickhouse",
    
    # Source Config
    mysql_resource_key="mysql_soil_testing_prod_db",
    source_database="soil_testing_prod",
    source_table="policies",
    incremental_key="updatedAt",
    
    # Destination Config (ClickHouse)
    destination_database="soil_testing_prod",
    destination_table="policies_v1",
    clickhouse_engine="ReplacingMergeTree(updatedAt)",
    clickhouse_order_by=["id", "updatedAt"],
    clickhouse_partition_by=None,
)
# ============================================================================
# ASSET COLLECTION
# ============================================================================
assets = [
    # MySQL AMT DB Tables
    mysql_amt_accounts, 
    
    # MySQL Sales Service DB Tables
    mysql_sales_service_leadsources, 
    mysql_sales_service_leads,
    mysql_sales_service_lead_channels,
    mysql_sales_service_cds,
    mysql_sales_service_form_answers,
    mysql_sales_service_kyc_requests,
    mysql_sales_service_forms,
    
    # MySQL Soil Testing Prod DB Tables
    mysql_soil_testing_prod_policies
    ]