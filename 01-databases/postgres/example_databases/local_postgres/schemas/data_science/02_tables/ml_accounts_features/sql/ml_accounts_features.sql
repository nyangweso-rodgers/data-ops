with
ml_accounts_features_cte as (
	SELECT account_id, customer_id, status, account_type, company_regions_id, _feature_generated_at, _exported_at
	FROM data_science.ml_accounts_features
	)
select --*
max(_exported_at)
from ml_accounts_features_cte
limit 1000