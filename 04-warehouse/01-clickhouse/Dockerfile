FROM clickhouse/clickhouse-server:24.8.7.41

# Copy main config file to required location
COPY ./config/config.xml /etc/clickhouse-server/config.xml

# Copy users config to standard location
COPY ./users/users.xml /etc/clickhouse-server/users.d/users.xml

# Create needed directories
RUN mkdir -p /var/lib/clickhouse/{preprocessed_configs,tmp,user_files,format_schemas} \
    && chown -R 101:101 /var/lib/clickhouse

EXPOSE 8123 9000
CMD ["clickhouse-server"]