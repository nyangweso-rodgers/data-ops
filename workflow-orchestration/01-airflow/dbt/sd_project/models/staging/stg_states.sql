{{ config(
    materialized='view'
) }}

SELECT 
	id, 
	state_name, 
	country_id, 
	region_id
FROM {{ source('postgres-ep', 'states') }}