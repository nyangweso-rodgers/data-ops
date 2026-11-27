with
ml_customer_location_features_cte as (
	SELECT customerid, latitude, longitude, customer_created_date, _feature_generated_at, _exported_at
	FROM data_science.ml_customer_location_features
	)
select *
from ml_customer_location_features_cte
limit 1000