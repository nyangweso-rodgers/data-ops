{{ config(
    materialized='view'
) }}

SELECT id, 
	region_name 
FROM {{ source('postgres-ep', 'regions') }}