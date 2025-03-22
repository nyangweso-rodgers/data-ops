# Kestra

- **Kestra** is an open-source, event-driven orchestrator. It uses a declarative YAML interface for building orchestration logic.
- **Features**
  1. Large number of trigger types through [plugins](https://kestra.io/plugins)
  2. [Backfill](https://kestra.io/docs/concepts/backfill) capabilities
  3. Simple architecture where a script is treated as a one-step flow, only one editor
  4. Uses YAML-only configuration for workflows where scripts are referenced as files
  5. Requires passing arguments between steps through file I/O
  6. Passes simple arguments as environment variables
  7. No visual flow builder/editor

# Installation

- Using `curl`:
  ```sh
    curl -o docker-compose.yml https://raw.githubusercontent.com/kestra-io/kestra/develop/docker-compose.yml
    docker-compose up -d
  ```
