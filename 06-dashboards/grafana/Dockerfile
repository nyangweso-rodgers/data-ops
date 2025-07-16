# ./grafana/Dockerfile
FROM grafana/grafana:12.0.2

# ✅ Install Infinity plugin (from Grafana's plugin registry)
RUN echo "Installing Infinity plugin..." && \
    grafana cli plugins install yesoreyeram-infinity-datasource && \
    echo "Infinity plugin installation completed" || { echo "Failed to install Infinity plugin"; exit 1; }

# Install ClickHouse plugin (Grafana Labs version)
RUN echo "Installing ClickHouse plugin..." && \
    grafana cli plugins install grafana-clickhouse-datasource && \
    echo "ClickHouse plugin installation completed" || { echo "Failed to install ClickHouse plugin"; exit 1;}
    
# 🔍 Optional: Verify plugins installed
RUN ls -la /var/lib/grafana/plugins && echo "✅ Plugins installed successfully"

# Copy provisioning files
COPY datasources/ /etc/grafana/provisioning/datasources/