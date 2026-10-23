with
ml_credit_history_features_cte as (
	SELECT country, customer_id, account_id, account_ref, account_type, account_status, deposit_amount, installment_amount, total_payplan_amount, total_number_payments, 
	payment_sequence, installment_type, expected_date, expected_amount, final_amount_paid, final_paid_date, amount_due, days_late, is_fully_paid, is_due, overdue_balance, total_balance, future_balance, _feature_generated_at, _exported_at
	FROM data_science.ml_credit_history_features
	)
select *
from ml_credit_history_features_cte
limit 1000