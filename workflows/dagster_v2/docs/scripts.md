# How to Use The Scripts For Testing

## Table Of Contents

# Script 1: `cleanup_clickhouse_tables.py`

- Use Cases:

  - Deduplicate

- Dry Run (All Partitions)

  ```sh
    py cleanup_clickhouse_tables.py \
        --database <database-name> \
        --table <table-name>
        --dry-run
  ```

- Actual Cleanup (If Dry Run Looks Good)

  ```sh
    py cleanup_clickhouse_tables.py \
        --database <database-name> \
        --table <table-name>
  ```

- Optional: Override Defaults
  - Only clean last 90 days
    ```sh
        # Only clean last 90 days
        py cleanup_clickhouse_tables.py \
        --database <database-name> \
        --table <table-name> \
        --window-days 90 \
        --dry-run
    ```
  - Or be more selective
    ```sh
        py cleanup_clickhouse_tables.py \
        --database <database-name> \
        --table <table-name> \
        --window-days 180 \
        --min-duplicates 10 \
        --min-pct 0.5 \
        --dry-run
    ```
