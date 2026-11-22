with
ml_payg_default_model_assignments_cte as (
	SELECT id, 
	predictionId, 
	accountId, accountRef, customerId, score_month, scored_at, 
	#ruleset_version, 
	recommended_officer, 
	recommended_function, assignment_recommendation, assigned_to, assigned_function, assignment_status, is_current, totalArrearsAmount, totalOutstandingBalance, totalPaidAmount, totalLoanAmount, outstanding_balance, daysLate, 
	assignment_start, assignment_end
	#createdAt, updatedAt
	#createdBy, updatedBy
	FROM test_reporting_service.ml_payg_default_model_assignments
	),
ml_payg_default_model_predictions_cte as (
	SELECT id, accountId, accountRef, customerId, score_month, tier, tier_source, default_probability, recommendation, recommendation_detail, model_version, feature_run_id, scoring_rules_version, 
	totalArrearsAmount, totalOutstandingBalance, totalPaidAmount, totalLoanAmount, outstanding_balance, daysLate, accountStatus, funnel_status, country, region, county, subcounty, town, latitude, longitude, customerName, customerPhoneNumber, customerIdentificationNumber, customer_age, gender, 
	sale_date, jsfDate, expectedDate, last_payment_date, installment_number, next_expected_amount, months_overdue, consecutive_misses, loan_age_months, prior_payment_rate, recent_3m_payment_rate, days_since_last_payment, productName, productQty, scored_at
	#createdAt, createdBy
	FROM test_reporting_service.ml_payg_default_model_predictions
	),
ml_payg_default_model_assignments_mashup_cte as (
	select ml_payg_default_model_assignments_cte.*,
	accountStatus,
	funnel_status,
	productName,
	country,region,county, subcounty, town, latitude, longitude
	from ml_payg_default_model_assignments_cte
	left join ml_payg_default_model_predictions_cte on ml_payg_default_model_predictions_cte.id = ml_payg_default_model_assignments_cte.predictionId
	),
agg_assignments_cte as (
	select distinct country,
	assigned_function,
	#accountStatus,
	assigned_to,
	count(distinct accountId) as account_id_count
	from ml_payg_default_model_assignments_mashup_cte
	where country = 'kenya'
	group by 1 ,2,3
	order by 1,2,3 desc
	),
check_duplicates_cte as (
	select distinct accountId,
	country,
	count(*) as record_count
	from ml_payg_default_model_assignments_mashup_cte
	group by 1,2
	having record_count > 1
	)
select *
#count(*)
#from ml_payg_default_model_assignments_cte
from ml_payg_default_model_assignments_mashup_cte
#from agg_assignments_cte
#from check_duplicates_cte
where assigned_function not in ('No Further Action - Exited', 'No Further Action - Pending Installation', 'No Further Action - Written Off')
and country = 'kenya'
and score_month = '2026_08'
#and accountId = '113890'
#limit 100