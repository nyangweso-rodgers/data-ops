with
payg_interventions_cte as (
	SELECT id, accountId, accountRef, customerId, score_month, tier, tier_source, default_probability, recommendation, recommendation_detail, model_version, recommended_officer, 
	recommended_function, assigned_to, assigned_function, assignment_status, is_current, totalArrearsAmount, totalOutstandingBalance, totalPaidAmount, totalLoanAmount, 
	outstanding_balance, daysLate, accountStatus, funnel_status, country, region, county, subcounty, town, latitude, longitude, customerName, 
	customerPhoneNumber, customerIdentificationNumber, customer_age, gender, cds1_date, cds2_date, sale_date, jsfDate, dispatchDate, expectedDate, last_payment_date, 
	installment_number, months_overdue, consecutive_misses, loan_age_months, prior_payment_rate, recent_3m_payment_rate, days_since_last_payment, productName, productQty, assignment_start, assignment_end, scored_at, createdAt, updatedAt, createdBy, updatedBy
	FROM test_reporting_service.ml_payg_interventions
	),
validation_cte as (
	select distinct accountId,
	count(*) as record_count
	from payg_interventions_cte
	GROUP BY 1
	HAVING record_count > 1
	),
agg_results_cte as (
	select distinct scored_at,
	country,
	count(distinct accountId) as account_id_count
	from payg_interventions_cte
	group by 1,2
	)
select *
#count(*), count(distinct accountId) 
#distinct score_month, scored_at, assignment_start
#from payg_interventions_cte
from validation_cte
#from payg_interventions_cte where accountId in (select distinct accountId from validation_cte ORDER  BY accountId, scored_at)
#from agg_results_cte
#where accountRef = '24996097'
#where accountRef = '0044536'
#where accountRef = '22102646'
#order by accountRef, 
#order by score_month, scored_at
limit 100