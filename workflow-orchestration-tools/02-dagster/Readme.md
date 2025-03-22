# Dagster

- **Dagster** is an open-source data orchestrator designed for building, running, and observing data pipelines and workflows.

- **Features**:
  1. **Asset-Centric Approach**: Adopts an asset-centric model, where assets are first-class citizens. This allows you to define and track data assets directly, making it easier to manage and monitor the flow of data throughout your pipelines.
  2. **Scalability**: Dagster empowers users to scale their data workflows efficiently as their requirements evolve, making it a versatile choice for growing organizations needing to manage complex ML workflows.
  3. **Developer Productivity**: By focusing on enhancing developer productivity and debugging capabilities, Dagster streamlines the process of orchestrating complex data pipelines.
  4. **Observability and Monitoring**: Dagster provides built-in tools for observability, giving you detailed insights into the execution of your workflows. You can monitor pipeline runs, view logs, and track the status of individual components, ensuring greater transparency and control, especially for model training jobs.
  5. **Modular Architecture**: The highly modular design promotes reusability and flexibility. You can easily create reusable pipeline components, making it simpler to adapt and scale your workflows. While Prefect and Airflow support modular workflows, Dagster’s focus on modularity makes it particularly powerful for complex data engineering tasks.
  6. **Web UI**: It has Dagit, a web-based graphical interface that provides a real-time view of pipeline execution, configuration, and system health.

# Installation

- Using `docker-compose.yml` File

  ```yml
  version: "3.7"

  services:
  docker_example_postgresql:
    image: postgres:11
    container_name: docker_example_postgresql
    environment:
    POSTGRES_USER: "postgres_user"
    POSTGRES_PASSWORD: "postgres_password"
    POSTGRES_DB: "postgres_db"
    networks:
      - docker_example_network
    healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres_user -d postgres_db"]
    interval: 10s
    timeout: 8s
    retries: 5

  docker_example_user_code:
    build:
    context: .
    dockerfile: ./Dockerfile_user_code
    container_name: docker_example_user_code
    image: docker_example_user_code_image
    restart: always
    environment:
    DAGSTER_POSTGRES_USER: "postgres_user"
    DAGSTER_POSTGRES_PASSWORD: "postgres_password"
    DAGSTER_POSTGRES_DB: "postgres_db"
    DAGSTER_CURRENT_IMAGE: "docker_example_user_code_image"
    networks:
      - docker_example_network

  docker_example_webserver:
    build:
    context: .
    dockerfile: ./Dockerfile_dagster
    entrypoint:
      - dagster-webserver
      - -h
      - "0.0.0.0"
      - -p
      - "3000"
      - -w
      - workspace.yaml
    container_name: docker_example_webserver
    expose:
      - "3000"
    ports:
      - "3000:3000"
    environment:
    DAGSTER_POSTGRES_USER: "postgres_user"
    DAGSTER_POSTGRES_PASSWORD: "postgres_password"
    DAGSTER_POSTGRES_DB: "postgres_db"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/io_manager_storage:/tmp/io_manager_storage
    networks:
      - docker_example_network
    depends_on:
    docker_example_postgresql:
      condition: service_healthy
    docker_example_user_code:
      condition: service_started

  docker_example_daemon:
    build:
    context: .
    dockerfile: ./Dockerfile_dagster
    entrypoint:
      - dagster-daemon
      - run
    container_name: docker_example_daemon
    restart: on-failure
    environment:
    DAGSTER_POSTGRES_USER: "postgres_user"
    DAGSTER_POSTGRES_PASSWORD: "postgres_password"
    DAGSTER_POSTGRES_DB: "postgres_db"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/io_manager_storage:/tmp/io_manager_storage
    networks:
      - docker_example_network
    depends_on:
    docker_example_postgresql:
      condition: service_healthy
    docker_example_user_code:
      condition: service_started

  networks:
  docker_example_network:
    driver: bridge
    name: docker_example_network
  ```
