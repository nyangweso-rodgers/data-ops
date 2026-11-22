with
accounts_cte as (
	SELECT id, accountRef, accountTypeId, status, customerId, fullDepositDate, createdAt, updatedAt, sync_at
	FROM test_kaleidofin.accounts
	)
select  
count(*), max(updatedAt), max(sync_at)
from accounts_cte