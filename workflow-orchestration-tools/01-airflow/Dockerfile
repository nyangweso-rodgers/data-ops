FROM apache/airflow:2.10.5

# Switch to root for installing system dependencies
USER root

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean

# Switch back to airflow user for installing Python packages and runtime
USER airflow
# Install Airflow-related packages first
RUN pip install --no-cache-dir \
    apache-airflow-providers-mysql==6.2.1 \
    mysqlclient==2.2.7 \
    psycopg2-binary==2.9.10 \
    connexion[swagger-ui] \
    requests==2.32.3 \
    clickhouse-connect==0.8.17 \
    openmetadata-managed-apis==1.7.0 \
    openmetadata-ingestion==1.7.0

# Install dbt with compatible versions
RUN pip install --no-cache-dir \
    dbt-core==1.7.0 \
    dbt-postgres==1.7.0 \
    dbt-mysql==1.7.0 \
    dbt-clickhouse==1.7.0

# Back to root to copy and chmod the script
USER root
COPY ./scripts/init-airflow.sh /opt/airflow/init-apache-airflow.sh
RUN chmod +x /opt/airflow/init-apache-airflow.sh

# Back to airflow user and set entrypoint
USER airflow
ENTRYPOINT ["/opt/airflow/init-apache-airflow.sh"]