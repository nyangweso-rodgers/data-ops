with
collection_officer_assignments_cte as (
	SELECT accountId, accountRef, accountType, status, funnel_status, product, days_late_current, arrears, 
	#PowerBI_balance, 
	companyRegion, latitude, longitude, town, County, region, 
	snapshot_date, id, assigned_function, 
	assigned_employee_id, assigned_employee_name ,
	assignment_start, assignment_end, 
	created_at
	#created_by, updated_at, updated_by
	FROM test.collection_officer_assignments
	where date(created_at) = '2026-08-28'
	),
agg_collection_officer_assignments_cte as (
	select distinct date(created_at) as created_at, 
	assigned_function,
	#status,
	assigned_employee_id,
	assigned_employee_name,
	count(distinct region) as region_count,
	count(distinct product) as product_count,
	count(*) as record_count,
	count(distinct accountId) as account_id_count
	from collection_officer_assignments_cte
	group by 1,2,3,4
	order by 1,2, 5 desc
	)
select *
#count(*)
from collection_officer_assignments_cte
#from agg_collection_officer_assignments_cte
#where assigned_function = 'NEEDS_REVIEW' and status in ('Arrears', 'Advance')
#where assigned_function = 'Credit Collections Associate (CCA)'
#limit 1000