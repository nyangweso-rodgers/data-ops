# Grafana

# Setup : Docker Compose

- When your system starts growing, you'll need more than just Grafana. You’ll likely want a data source, such as **Prometheus** or **InfluxDB**, to send data to **Grafana** for visualization. Docker Compose helps manage multiple containers as a single unit, simplifying the deployment process.

- **Steps**

  1. Step : Create `docker-compose.yml` File

     ```yml
     version: "1"
     services:
     grafana:
       image: grafana/grafana
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=supersecret
       ports:
         - "3000:3000"
       volumes:
         - grafana_data:/var/lib/grafana
     prometheus:
       image: prom/prometheus
       volumes:
         - prometheus_data:/prometheus
       ports:
         - "9090:9090"
     volumes:
     grafana_data:
     prometheus_data:
     ```

  2. Step 2: Start the Container
     ```sh
        docker-compose up -d
     ```

# How to monitor PosgreSQL with Prometheus and Grafana | Docker

- To monitor your **PostgreSQL** database running in a **Docker container** with **Prometheus** and **Grafana**, you'll need to set up the following additional services:

  1. **PostgreSQL Exporter**: This will connect to your **postgres-db** container and expose metrics in a format **Prometheus** can scrape.
  2. **Prometheus**:

     - This will periodically scrape metrics from the **PostgreSQL exporter** and store them.
     - Think of it as the heartbeat tracker for your setup—it periodically "scrapes" data (like **CPU usage**, **database queries**, or **custom app metrics**) from configured targets and stores them for analysis. In our case, it’s meant to monitor your **PostgreSQL database** (via the **postgres-db-exporter**) and potentially other services, feeding that data to **Grafana** for visualization.
     - Use cases:
       1. **Metrics Collection**: It pulls metrics from "exporters" (like `postgres-db-exporter`) or services that expose them directly (e.g., via an HTTP endpoint like `/metrics`).
       2. **Storage**: It keeps these metrics in a time-series database, letting you see trends over time (e.g., "How many database connections were active in the last hour?").
       3. **Querying**: You can use its query language (PromQL) to analyze the data (e.g., "Show me the rate of queries per second").
       4. **Bridge to Grafana**: Grafana uses Prometheus as a data source to create dashboards, making the raw numbers visual and actionable.

  3. **Grafana**: This will connect to **Prometheus** and provide a dashboard to visualize the metrics.

- Setup:

  1. **Step 1**: Setup `postgres-db` Container
  2. **Step 2**: Setup `postgres-exporter` Container

     - **Postgres Exporter**: Uses `prometheuscommunity/postgres-exporter`, connects to your `postgres-db` container via the `DATA_SOURCE_NAME` environment variable, and exposes metrics on port `9187`.
       ```yml
       postgres-db-exporter:
         image: prometheuscommunity/postgres-exporter:latest
         container_name: postgres-db-exporter
         ports:
           - "9187:9187"
         environment:
           DATA_SOURCE_NAME: "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-db:5432/postgres?sslmode=disable"
         depends_on:
           - postgres-db
         restart: always
         networks:
           - data-ops-network
       ```

  3. **Step 3**: Setup `prometheus` Container

     - **Prometheus**: Uses the official prom/prometheus image, maps port 9090 for its web UI, and mounts a prometheus.yml configuration file
       ```yml
       prometheus:
         #image: prom/prometheus
         image: prom/prometheus:latest
         container_name: prometheus
         restart: always
         ports:
           - "9090:9090"
         volumes:
           - ./prometheus.yml:/etc/prometheus/prometheus.yml
           - prometheus-volume:/prometheus
         command:
           - "--config.file=/etc/prometheus/prometheus.yml"
         networks:
           - data-ops-network
       ```

  4. **Step 4**: Setup `grafana` Container

     - **Grafana**: Uses the official grafana/grafana image, maps port 3000 for its web UI, and persists dashboard data in a volume.
       ```yml
       grafana:
         image: grafana/grafana:latest
         container_name: grafana
         restart: always
         ports:
           - "3006:3000" # Map host port 3006 to container port 3000
         environment:
           - GF_SECURITY_ADMIN_USER=${GF_SECURITY_ADMIN_USER}
           - GF_SECURITY_ADMIN_PASSWORD=${GF_SECURITY_ADMIN_PASSWORD}
         volumes:
           - grafana-volume:/var/lib/grafana
         networks:
           - data-ops-network
       ```

  5. **Step 5**: Create the `prometheus.yml` Configuration File

     - Create a file named `prometheus.yml` in the same directory as `docker-compose.yml`. This file tells **Prometheus** where to scrape metrics from (in this case, the Postgres exporter).

       ```yml
       global:
         scrape_interval: 15s # How often to scrape metrics

       scrape_configs:
         - job_name: "prometheus"
           static_configs:
             - targets: ["localhost:9090"] # Prometheus scrapes itself
         - job_name: "postgres-exporter"
           static_configs:
             - targets: ["postgres-exporter:9187"] # Scrape the Postgres exporter
       ```

     - Notes:
       - The `scrape_interval` is set to 15 seconds, but you can adjust this based on your needs.
       - The targets under `postgres-exporter` use the container name (`postgres-exporter`) and port (`9187`), which works because they’re on the same Docker network.

  6. **Step 6**: **Start the Services**

     - Start the services by:

  7. **Step 7**: **Verify the Setup**

     1. Check PostgreSQL Exporter

        - Open your browser and go to `http://localhost:9187/metrics`. You should see a list of metrics being exposed by the Postgres exporter.

     2. Check Prometheus

        - Go to `http://localhost:9090`. In the UI, click on "Status" > "Targets". You should see two targets: `prometheus` and `postgres-exporter`, both in the "UP" state.

     3. Check Grafana
        - Go to `http://localhost:3006`. Log in with the default credentials (username: `admin`, password: `admin`). You’ll be prompted to change the password.

  8. **Step 8**: **Configure Grafana**

     1. Add **Prometheus** as a **Data Source**
        - In Grafana, click the gear icon ("Configuration") in the left sidebar, then select "Data Sources".
        - Click "Add data source" and choose "Prometheus".
        - Set the URL to `http://prometheus:9090` (using the container name since they’re on the same network).
        - Click "Save & Test". It should say "Data source is working".
     2. Import a PostgreSQL Dashboard
        - Click the "+" icon in the left sidebar and select "Import".
        - Use a pre-built dashboard ID from Grafana’s dashboard library, such as `9628` (a popular PostgreSQL dashboard).
        - In the import screen, select your Prometheus data source from the dropdown and click "Import".
        - You should now see a dashboard displaying metrics like database connections, query performance, and more.

  9. **Step 9**: **Explore and Customize**
     - Prometheus UI: At `http://localhost:9090/graph`, you can query metrics like `pg_stat_activity_count` to see active connections.
     - Grafana Dashboard: Customize the imported dashboard by adding panels or tweaking queries to focus on metrics that matter to you (e.g., CPU usage, transaction rates).

# Optimizing Grafana Performance in Docker

1. **Docker Resource Allocation**

   - Memory and CPU Management: Containers, by default, don’t impose any strict limits on resources. However, you can configure Docker to allocate specific amounts of CPU and memory to the Grafana container.
   - This prevents the container from consuming all available resources, which could slow down the system or other containers.
     ```yml
     grafana:
       image: grafana/grafana
       mem_limit: 2g
       cpus: 1.0
     ```

2. **Persistent Data Storage**

   - For Grafana, persisting data means that your dashboards, settings, and data won’t disappear if the container restarts
     ```yml
     volumes:
       - grafana_data:/var/lib/grafana
     ```
   - Without this setup, Grafana’s configuration and dashboard data would be stored within the container, and it would be lost every time the container is removed.

3. **Security Considerations**
   - While Grafana is secure out of the box, Docker adds an extra layer of complexity. Make sure to:
     - **Use Environment Variables** for sensitive data like passwords and API keys.
     - **Configure SSL** using a reverse proxy like Nginx to encrypt traffic between clients and Grafana.
     - **Limit External Access** to the Grafana dashboard by configuring firewall rules or using a private network.

# Extending Grafana with Advanced Integrations

1. **Grafana + Loki for Log Aggregation**

   - **Loki**, **Grafana’s** log aggregation tool, can be deployed alongside Grafana to allow you to visualize logs next to your metrics.
     ```yml
     loki:
       image: grafana/loki
       ports:
         - "3100:3100"
     ```
   - This setup enables you to send logs from your services to **Loki**, which **Grafana** can then pull and visualize.

2. **Prometheus + Grafana for Comprehensive Monitoring**
   - **Prometheus** is a popular time-series database often paired with **Grafana**. **Prometheus** collects data from your systems and exposes it for Grafana to visualize. You can collect Docker container metrics using cAdvisor, a tool that exposes detailed information about running containers.
   - Example setup for cAdvisor with Prometheus:
     ```sh
        docker run -d \
            --name=cadvisor \
            -p 8080:8080 \
            --volume=/var/run/docker.sock:/var/run/docker.sock \
            gcr.io/cadvisor/cadvisor
     ```

# Resources and Further Reading

1. [Grafana and Docker: A Simple Way to Monitor Everything](https://last9.io/blog/grafana-and-docker/?ref=dailydev)
2. [Medium - How to monitor PosgreSQL with Prometheus and Grafana | Docker](https://nelsoncode.medium.com/how-to-monitor-posgresql-with-prometheus-and-grafana-docker-36d216532ea2)
