with
collection_officer_assignment_base_cte as (
	SELECT account_ref, cca, _synced_at, assignment_start, assignment_end
	FROM test.collection_officer_assignment_base
	)
select distinct cca,
count(*) as record_count,
count(distinct account_ref) as account_ref_count
from collection_officer_assignment_base_cte
group by 1