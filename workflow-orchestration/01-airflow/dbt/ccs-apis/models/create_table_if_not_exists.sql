{{ config(materialized='table') }}

{% set table_exists = adapter.get_relation(
    database=env_var('POSTGRES_REPORTING_SERVICE_DB'),
    schema='ccs',
    identifier='my_test_table'
) %}

{% if table_exists %}
    -- Table already exists, no action needed
    SELECT 1 AS dummy
{% else %}
    -- Create table with predefined schema
    CREATE TABLE ccs.my_test_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Insert a sample row for testing
    INSERT INTO ccs.my_test_table (name) VALUES ('test_record');
{% endif %}