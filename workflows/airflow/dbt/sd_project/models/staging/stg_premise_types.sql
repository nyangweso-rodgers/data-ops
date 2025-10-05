{{ config(
    materialized='view'
) }}

SELECT 
	id, 
	premise_type_name
FROM {{ source('postgres-ep', 'premise_types') }}