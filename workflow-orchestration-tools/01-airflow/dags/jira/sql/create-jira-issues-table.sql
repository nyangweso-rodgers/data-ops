CREATE TABLE IF NOT EXISTS {schema}.{table} (
    issue_key VARCHAR(50) PRIMARY KEY,
    summary TEXT,
    issue_type VARCHAR(50),
    status VARCHAR(50),
    created TIMESTAMP,
    updated TIMESTAMP,
    priority VARCHAR(50),
    assignee VARCHAR(100),
    project_key VARCHAR(50),
    sync_time TIMESTAMP
);
