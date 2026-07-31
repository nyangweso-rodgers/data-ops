with
ml_payg_default_model_predictions_cte as (
	SELECT id, accountId, accountRef, customerId, score_month, tier, tier_source, default_probability, recommendation, recommendation_detail, model_version, feature_run_id, scoring_rules_version, 
	totalArrearsAmount, totalOutstandingBalance, totalPaidAmount, totalLoanAmount, outstanding_balance, daysLate, accountStatus, funnel_status, country, region, county, subcounty, town, latitude, longitude, customerName, customerPhoneNumber, customerIdentificationNumber, customer_age, gender, sale_date, jsfDate, expectedDate, last_payment_date, installment_number, next_expected_amount, months_overdue, consecutive_misses, loan_age_months, prior_payment_rate, recent_3m_payment_rate, days_since_last_payment, productName, productQty, scored_at, createdAt, createdBy
	FROM test_reporting_service.ml_payg_default_model_predictions
	where country = 'kenya'
	)
select *
#count(*)
from ml_payg_default_model_predictions_cte
limit 100