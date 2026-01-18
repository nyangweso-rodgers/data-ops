SELECT 
    key,
    value::json->>'source_table' as table_name,
    value::json->>'last_value' as last_synced_value,
    value::json->>'synced_at' as synced_at,
    (value::json->'metadata'->>'rows_synced')::int as rows_synced,
    NOW() - (value::json->>'synced_at')::timestamp as age
FROM dagster.kvs
WHERE key LIKE 'etl_sync_state:mysql:%'
ORDER BY synced_at DESC;