# Windmill

- **Windmill** is a fast, open-source workflow engine and developer platform. **Windmill** supports both UI-based operations via its webIDE and low-code builders.
- **Features**
  1. **An efficient runtime**: Execute code [across languages](https://www.windmill.dev/docs/getting_started/scripts_quickstart) with minimal overhead and instant starts. It supports coding in TypeScript, Python, Go, PHP, Bash, C#, SQL and Rust, or any Docker image, alongside intuitive low-code builders
  2. **Smart dependency and input management**: automatically generate lockfiles and input specs from your code, ensuring consistent [dependency versions](https://www.windmill.dev/docs/advanced/imports) and simplified [input handling](https://www.windmill.dev/docs/core_concepts/json_schema_and_parsing).
  3. An [execution runtime](https://www.windmill.dev/docs/script_editor) for scalable, low-latency function execution across a worker fleet.
  4. An [orchestrator](https://www.windmill.dev/docs/flows/flow_editor) for assembling these functions into efficient, low-latency flows, using either a low-code builder or YAML.
  5. **Dynamic web IDE and Low-Code builders**: create [scripts](https://www.windmill.dev/docs/script_editor) with advanced editing tools and [auto-generated UIs](https://www.windmill.dev/docs/core_concepts/auto_generated_uis), build [flows](https://www.windmill.dev/docs/flows/flow_editor) with a drag-and-drop interface, and design apps without extensive coding(JS frameworks like React).
  6. **Enterprise-Ready**: Windmill offers robust [permissioning](https://www.windmill.dev/docs/core_concepts/roles_and_permissions), [secret management](https://www.windmill.dev/docs/core_concepts/variables_and_secrets), OAuth, and more, wrapped in an enterprise-grade platform.
  7. **Integrations and Automations**: with [webhooks](https://www.windmill.dev/docs/core_concepts/webhooks), an [open API](https://app.windmill.dev/openapi.html), and a [scheduler](https://www.windmill.dev/docs/core_concepts/scheduling), Windmill fits seamlessly into your infrastructure, allowing for extensive automation capabilities.

# Installation

- Using `curl`

  ```sh
    curl https://raw.githubusercontent.com/windmill-labs/windmill/main/docker-compose.yml -o docker-compose.yml
    curl https://raw.githubusercontent.com/windmill-labs/windmill/main/Caddyfile -o Caddyfile
    curl https://raw.githubusercontent.com/windmill-labs/windmill/main/.env -o .env

    docker compose up -d
  ```
