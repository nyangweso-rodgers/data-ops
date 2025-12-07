SELECT id, run_id, "event", dagster_event_type, "timestamp", step_key, asset_key, "partition"
FROM public.event_logs
order by "timestamp" DESC