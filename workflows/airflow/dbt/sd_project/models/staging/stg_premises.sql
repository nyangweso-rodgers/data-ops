{{ config(
    materialized='view'
) }}

SELECT
    id,
    created_at,
    updated_at,
    premise_name,
    premise_type_id,
    substate_id,
    town
FROM {{ source('postgres-ep', 'premises') }}