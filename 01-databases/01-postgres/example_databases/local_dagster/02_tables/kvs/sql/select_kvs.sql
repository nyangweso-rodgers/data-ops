SELECT id, "key", value
FROM dagster.kvs
where key like 'etl_sync_state:mysql:amtdb:%'
--where key like 'etl_sync_state:mysql:sales-service:%'
order by key