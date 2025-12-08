# Architecture

# Priority

1. Scalability
2. Maintanability
3. State management
4. Developer experience

# Centralized Schemas

- Centralized schema is the source of truth in that:

  - Data Team adds a YAML file
  - Minimal code changes needed
  - Assets are generated from schemas

- The schemas become configuration, not code artifacts. It should be:
  - Easy to discover (one place to look)
  - Easy to review (PR reviewers see all schema changes in one directory)
  - Versioned indeendently from implementation logic

# PostgreSQL

- PostgreSQL for Dagster metadata (runs, events, schedules)
- Why PostgreSQL
  - **Native support**: Dagster is built and optimized for Postgres
  - **Performance**: Better query performance for Dagster's metadata queries (complex JOINs, aggregations)
  - **JSON support**: Dagster stores structured logs; Postgres handles JSONB better
  - **Community standard**: Most production Dagster deployments use Postgres

# S3

- S3 for compute logs (optional, for log archival and cost savings)
- Good as artifact storage (large intermediate files, result artifacts).
- Dagster supports using S3 for object store (storing assets/results), but not ideal as primary run/event database because querying runs and event logs is harder and less efficient.

# ETL Factories - The Orchestration Layer

- Factories tie everything together! They use connectors to create end-to-end ETL pipelines.
- Factories orchestrate the ETL flow:
  - Load schema (SchemaLoader)
  - Map Types (TypeMapper)
  - Extract Data (Source Connector)
  - Tranform Data (in batches)
  - Load Data (Destination Connector)
  - Manage State (StateManager)
