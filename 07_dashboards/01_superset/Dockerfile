FROM apache/superset:6.0.0

# Install additional dependencies into the app's venv (the image manages
# it with uv; plain `pip` on PATH is the system pip and installs where
# Superset's venv-based CLI/app can't see it)
USER root
RUN uv pip install --python /app/.venv/bin/python --no-cache \
    psycopg2-binary pymysql pyodbc clickhouse-connect

# Copy entrypoint
COPY configs/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy superset_config.py (points the metadata DB at Postgres instead of the default SQLite)
ENV PYTHONPATH="/app/pythonpath:${PYTHONPATH}"
RUN mkdir -p /app/pythonpath
COPY configs/superset_config.py /app/pythonpath/superset_config.py

# Bake the database-connection manifest into the image. This is the only copy of it
# the container ever sees — changing a connection means editing connections.json and
# rebuilding, not running a script against a live instance.
COPY provisioning/ /app/provisioning/

# Switch back to the superset user
USER superset

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]