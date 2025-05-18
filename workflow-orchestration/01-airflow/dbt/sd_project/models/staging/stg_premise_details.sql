{{ config(
    materialized='view'
) }}

SELECT 
	id, 
	premise_id
FROM {{ source('postgres-ep', 'premise_details') }}