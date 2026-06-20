SELECT id, "key", value
FROM dagster.kvs
--where key like 'etl_sync_state:mysql:amtdb:%'
--where key like 'etl_sync_state:mysql:sales-service:%'
--WHERE key LIKE 'etl_sync_state:clickhouse_export:%'
--WHERE key LIKE 'etl_sync_state:partner_kaleidofin:%'
order by key