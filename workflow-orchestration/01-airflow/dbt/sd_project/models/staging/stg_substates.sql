{{ config(
    materialized='view'
) }}

SELECT 
	id, 
	state_id, 
	substate_name
FROM {{ source('postgres-ep', 'substates') }}