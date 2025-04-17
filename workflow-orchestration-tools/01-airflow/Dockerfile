FROM apache/airflow:2.9.0

# Switch to root for installing system dependencies
USER root

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean

# Switch back to airflow user for installing Python packages and runtime
USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-mysql==5.6.0 \
    mysqlclient==2.2.4 \
    psycopg2-binary==2.9.9 \
    connexion[swagger-ui] \
    requests==2.31.0 \
    clickhouse-connect==0.7.0 \
    openmetadata-managed-apis==1.6.7 \
    openmetadata-ingestion==1.6.7

# Back to root to copy and chmod the script
USER root
COPY ./scripts/init-airflow.sh /opt/airflow/init-apache-airflow.sh
RUN chmod +x /opt/airflow/init-apache-airflow.sh

# Back to airflow user and set entrypoint
USER airflow
ENTRYPOINT ["/opt/airflow/init-apache-airflow.sh"]