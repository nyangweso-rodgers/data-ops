with
collection_officer_assignments_cte as (
	SELECT accountId, accountRef, accountType, status, funnel_status, 
	product, days_late_current, arrears, 
	#PowerBI_balance, companyRegion, 
	#latitude, longitude, 
	town, County, region, snapshot_date, first_expected_date, is_fpd_amount, fpd_amount_days_late, next_expected_date, 
	#next_payment_sequence, current_expected_date, 
	id, batch_id, 
	assigned_function, assigned_employee_id, assigned_employee_name, 
	assignment_start, assignment_end, created_at,
	#created_by, 
	updated_at,
	#updated_by
	note
	FROM test.collection_officer_assignments
	#where assigned_function not in ('Unassigned')
	#where assigned_function not in ('Unassigned', 'Credit Collections Associate (CCA)', 'Field Credit Collection (FCA)', 'SMS Alert', 'Watchful')
	#where assigned_function = 'Credit Collections Associate (CCA)'
	#where assigned_function = 'Field Fraud Officer (FFO)'
	#where assigned_function = 'Debt Recovery Officer (DRO)'
	#where assigned_function = 'SMS Alert'
	#and assigned_employee_name = 'John Shikoli'
	#and batch_id = '7fb9a28b-5212-431f-986b-18ad05558326'
	#where status = 'Write Off'
	#where status = 'Arrears'
	#where note = "Manual CCA gap-fill from CCA team's '5th Accounts in Arrears' extract"
	#where updated_at = '2026-09-07 20:59:09'
	#where date(updated_at) = '2026-09-09'
	where accountRef = '0389306-3-KIL-PAYG'
	#order by updated_at asc
	),
agg_status_cte as (
	select distinct 
	assignment_start,
	assignment_end,
	#status,
	#assigned_function,
	#funnel_status,
	#assigned_employee_name,
	#note,
	count(*) as record_count,
	count(distinct accountId) as account_id_count,
	sum(arrears) as arrears
	from collection_officer_assignments_cte
	group by 1,2
	order by 1, 2
	),
agg_collection_officer_assignments_cte as (
	select distinct batch_id,
	created_at,
	#date(created_at) as created_at, 
	assignment_start,
	assignment_end,
	snapshot_date,
	assigned_function,
	#status,
	assigned_employee_id,
	assigned_employee_name,
	#count(distinct region) as region_count,
	#count(distinct product) as product_count,
	count(*) as record_count,
	count(distinct accountId) as account_id_count,
	sum(arrears) as arrears
	from collection_officer_assignments_cte
	group by 1,2,3,4,5,6,7,8
	order by assigned_function, arrears DESC
	)
/*
check_duplicates_cte as (
	select distinct accountId,
	count(*) as record_count
	from collection_officer_assignments_cte
	group by 1
	having record_count > 1
	)
*/
select *
#distinct note
#count(*)
#max(assignment_start) as max_assignment_start
#max(updated_at) as max_updated_at
from collection_officer_assignments_cte
#from agg_status_cte
#from agg_collection_officer_assignments_cte
#from check_duplicates_cte
#where assigned_function = 'NEEDS_REVIEW' and status in ('Arrears', 'Advance')
#where assigned_function = 'Credit Collections Associate (CCA)'
limit 1000
#order by assigned_function, arrears desc, assigned_employee_name