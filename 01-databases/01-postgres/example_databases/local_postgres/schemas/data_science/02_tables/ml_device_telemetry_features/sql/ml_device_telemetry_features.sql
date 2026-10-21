with
ml_device_telemetry_features_cte as (
	SELECT country, device_timestamp_month, customer_id, device_id_count, account_id_count, days_with_data, total_time_interval_mins, avg_time_interval_mins, avg_energy_consumption_kwh, total_energy_consumption_kwh, total_telemetry_record_count, _feature_generated_at, _exported_at
	FROM data_science.ml_device_telemetry_features
	),
agg_ml_device_telemetry_features_cte as (
	select distinct device_timestamp_month,
	count(*) as record_count
	from ml_device_telemetry_features_cte
	group by 1
	order by 1 desc
	)
select *
--from ml_device_telemetry_features_cte
from agg_ml_device_telemetry_features_cte
limit 1000