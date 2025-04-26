INSERT INTO {schema}.{table} (
    issue_key, summary, issue_type, status, 
    created, updated, priority, assignee, project_key, sync_time
)
VALUES %s
ON CONFLICT (issue_key)
DO UPDATE SET
    summary = EXCLUDED.summary,
    issue_type = EXCLUDED.issue_type,
    status = EXCLUDED.status,
    created = EXCLUDED.created,
    updated = EXCLUDED.updated,
    priority = EXCLUDED.priority,
    assignee = EXCLUDED.assignee,
    project_key = EXCLUDED.project_key,
    sync_time = CURRENT_TIMESTAMP;
