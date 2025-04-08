from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime
import json

# Define ingestion config as a JSON string
ingestion_config = {
    "source": {
        "type": "postgres",
        "serviceName": "postgres-local",
        "serviceConnection": {
            "config": {
                "type": "Postgres",
                "username": "postgres",
                "authType": {
                    "password": "mypassword"
                },
                "hostPort": "postgres-db:5432",
                "database": "users"
            }
        },
        "sourceConfig": {
            "config": {
                "type": "DatabaseMetadata",
                "schemaFilterPattern": {"includes": ["public"]}
            }
        }
    },
    "sink": {
        "type": "metadata-rest",
        "config": {}
    },
    "workflowConfig": {
        "openMetadataServerConfig": {
            "hostPort": "http://open-metadata-server:8585/api",
            "authProvider": "openmetadata",
            "securityConfig": {
                "jwtToken": "eyJraWQiOiJHYjM4OWEtOWY3Ni1nZGpzLWE5MmotMDI0MmJrOTQzNTYiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJvcGVuLW1ldGFkYXRhLm9yZyIsInN1YiI6ImFkbWluIiwicm9sZXMiOlsiQWRtaW4iXSwiZW1haWwiOiJhZG1pbkBvcGVuLW1ldGFkYXRhLm9yZyIsImlzQm90IjpmYWxzZSwidG9rZW5UeXBlIjoiUEVSU09OQUxfQUNDRVNTIiwiaWF0IjoxNzQzNDI1MzI5LCJleHAiOjE3NDYwMTczMjl9.l7OVnxp8vfSG9DbMKQFyIn0o2BNs4TyNGSf67HStdTHJWOV3UmRwSHSKsOYMBYYDm03AMVd4w3jf4AJHfNebBMqO8Acm56sP7ivkluVVTwWVKDuKI3VovmxwUjCsm5Zxj2KLhXHRFI_ll4gwHQHJSbbxlIKqBAO1R8TjDX9uD0qeGJuuTID98b2dTBHTdkvBNgmSb9ZX45cCBx67PuIbz7ddO_Vww6hO9LjmGTT3KtqBr8Nf0e0rOGCia2VQsX1nPP646lr93g-CWsMwVB0h4AcFVE-Sp89Y4IVJFJT1kTil8BsQr-tRYkwJkyKrU7ZqM3E07a6lIVdhVxCVC6kRUA"  # Replace with token from curl
            }
        }
    }
}

# Write config to a temporary file
config_json = json.dumps(ingestion_config)

# Define the DAG
with DAG(
    dag_id="postgres_metadata_ingestion",
    schedule_interval=None,
    start_date=datetime(2025, 3, 31),
    catchup=False
) as dag:
    ingestion_task = BashOperator(
        task_id="run_postgres_ingestion",
        bash_command=f"echo '{config_json}' > /tmp/ingestion_config.json && metadata ingest -c /tmp/ingestion_config.json",
        dag=dag
    )