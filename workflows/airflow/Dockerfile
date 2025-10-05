FROM apache/airflow:2.10.5
# FROM apache/airflow:3.0.2
# Switch to root for installing system dependencies
USER root
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean
# Create scripts directory and copy scripts
COPY ./scripts/ /opt/airflow/scripts/
RUN chmod +x /opt/airflow/scripts/*.sh

# Switch back to airflow user for installing Python packages and runtime
USER airflow

# Update pip to latest version
RUN pip install --no-cache-dir --upgrade pip==25.0.1

# Install Airflow-related packages
RUN pip install --no-cache-dir \
    apache-airflow-providers-mysql==6.2.1 \
    apache-airflow-providers-postgres==6.1.3 \
    apache-airflow-providers-common-sql==1.23.0 \
    mysqlclient==2.2.7 \
    psycopg2-binary==2.9.10 \
    connexion[swagger-ui] \
    requests==2.32.3 \
    clickhouse-connect==0.8.17

# Install dbt with compatible versions
RUN pip install --no-cache-dir \
    dbt-core==1.7.0 \
    dbt-postgres==1.7.0 \
    dbt-mysql==1.7.0 \
    dbt-clickhouse==1.7.0

# Set entrypoint
ENTRYPOINT ["/opt/airflow/scripts/entrypoint.sh"]