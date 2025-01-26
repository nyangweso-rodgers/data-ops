FROM  clickhouse/clickhouse:24.9.3.128
#FROM yandex/clickhouse-server:19.14.13.4

#FROM clickhouse/clickhouse-server:23.8

# Copy custom configuration file (optional)
#COPY ./config.xml /etc/clickhouse-server/config.xml

# Set environment variables (if needed)
#ENV CLICKHOUSE_USER default
#ENV CLICKHOUSE_PASSWORD ""

# Expose necessary ports
#EXPOSE 9000 8123 9009

# Start ClickHouse server
#CMD ["clickhouse-server"]

# Create the config directory and copy your config.xml file into the image
#COPY ./clickhouse-config/config.xml /etc/clickhouse-server/config.xml

# Expose necessary ports
EXPOSE 8123 9000

# Entrypoint is the ClickHouse server
CMD ["clickhouse-server"]