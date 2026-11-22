with
account_payplans_cte as (
	SELECT id, accountId, payplanId, productQty, createdAt, updatedAt, sync_at
	FROM test_kaleidofin.account_payplans
	)
select 
count(*), max(sync_at)
from account_payplans_cte