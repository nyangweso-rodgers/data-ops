with
ml_payments_features_cte as (
	SELECT customer_created_date, country, customer_id, customer_type, payment_month, total_payment_count, total_payment_amount, _feature_generated_at, _exported_at
	FROM data_science.ml_payments_features
	)
select *
from ml_payments_features_cte
limit 1000