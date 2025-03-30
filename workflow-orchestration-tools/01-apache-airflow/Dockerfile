# Use the official Airflow image as a base
FROM apache/airflow:2.8.1

RUN pip install \
    connexion[swagger-ui] \
    requests

# Copy your DAGs or custom files (optional)
COPY ./dags /opt/airflow/dags
COPY ./init-scripts/init-apache-airflow.sh /opt/airflow/init-apache-airflow.sh

# Switch to airflow user (default in the image)
USER airflow