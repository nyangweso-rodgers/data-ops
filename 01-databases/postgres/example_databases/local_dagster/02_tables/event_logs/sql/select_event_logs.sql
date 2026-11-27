SELECT count(*) 
--id, run_id, "event", dagster_event_type, "timestamp", step_key, asset_key, "partition"
FROM dagster.event_logs
--order by "timestamp" DESC