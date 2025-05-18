WITH source_data AS (
    SELECT DISTINCT
        p.id as premises_id,
        p.premise_name,

        c.country_name,
        r.region_name,
        ss.substate_name,
        pt.premise_type_name,
        p.town as premises_town,
        --p.customer_id,
        --p.account_id,
        --pd.crops_to_be_grown,
        p.updated_at,  -- Critical for incremental logic
        CURRENT_TIMESTAMP AS sync_time
    FROM {{ ref('stg_premises') }} p
    LEFT JOIN {{ ref('stg_substates') }} ss ON ss.id = p.substate_id
    LEFT JOIN {{ ref('stg_states') }} s ON s.id = ss.state_id
    LEFT JOIN {{ ref('stg_countries') }} c ON c.id = s.country_id
    LEFT JOIN {{ ref('stg_premise_details') }} pd ON pd.premise_id = p.id
    LEFT JOIN {{ ref('stg_premise_types') }} pt ON pt.id = p.premise_type_id
    LEFT JOIN {{ ref('stg_regions') }} r ON r.id = s.region_id
    {% if is_incremental() %}
    WHERE p.updated_at > (SELECT COALESCE(MAX(updated_at), '1970-01-01'::timestamp) FROM {{ this }})
    {% endif %}
)

SELECT 
    * 
FROM source_data