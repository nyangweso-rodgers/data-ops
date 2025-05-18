{{ config(
    materialized='view',
    schema='staging'
) }}

SELECT
    call_id,
    call_key,
    call_date::TIMESTAMP,
    -- ... other fields with basic cleaning ...
FROM {{ source('public', 'call_records_raw') }}