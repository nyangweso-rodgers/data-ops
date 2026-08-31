with
collection_officers_cte as (
	SELECT employee_id, employee_name, active, primary_role, created_at, created_by, updated_at, updated_by, region
	FROM test.collection_officers
	)
select * 
from collection_officers_cte