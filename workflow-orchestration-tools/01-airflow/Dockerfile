FROM apache/airflow:2.9.0
RUN pip install --no-cache-dir \
    mysql-connector-python \
    psycopg2-binary \
    connexion[swagger-ui] \
    requests
COPY ./scripts/init-airflow.sh /opt/airflow/init-apache-airflow.sh
USER airflow
ENTRYPOINT ["/opt/airflow/init-apache-airflow.sh"]