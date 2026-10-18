SELECT EXISTS (
    SELECT 1
    FROM system.tables
    WHERE database = %s AND name = %s
)