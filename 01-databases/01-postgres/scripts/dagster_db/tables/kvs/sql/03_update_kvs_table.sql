UPDATE public.kvs 
SET value = '{"last_value": "2025-01-01 00:00:00", "key": "updatedAt", ...}'
WHERE key = 'etl_sync_state:mysql:amtdb:accounts';