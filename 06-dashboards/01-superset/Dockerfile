FROM apache/superset:latest

# Install additional dependencies
USER root
RUN pip install --no-cache-dir psycopg2-binary pymysql pyodbc

# Copy entrypoint
COPY configs/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch back to the superset user
USER superset

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]