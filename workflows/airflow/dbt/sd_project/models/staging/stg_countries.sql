{{ config(
    materialized='view'
) }}

SELECT
	id, 
	country_name
FROM {{ source('postgres-ep', 'countries') }}