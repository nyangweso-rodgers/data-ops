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
