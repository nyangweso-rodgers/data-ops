# Elasticsearch (ES)

## Table of Contents

# Elasticsearch (ES)

- ES is primarily a distributed search and analytics engine, not a traditional database like MySQL or PostgreSQL. It's built on top of Apache Lucene (a powerful full-text search library) and excels at handling large volumes of data for fast, complex searches—think querying logs, logs, documents, or metrics in milliseconds.

# Kibana

- **Authenitication to Kibana**:

  1. Option 1: Using Username/Password (Recommended for Development)
  2. Option 2: Generate and Use Service Account Token (Production)
     - First, start only Elasticsearch and create a service account token:
       ```sh
           # Replace YOUR_PASSWORD with your actual password
           docker exec -it elasticsearch curl -X POST \
           -u elastic:YOUR_PASSWORD \
           "http://localhost:9200/_security/service/elastic/kibana/credential/token/kibana-token"
       ```

- Test basic authentication:
  ```sh
    docker exec -it elasticsearch curl -u elastic:YOUR_PASSWORD \
    "http://localhost:9200/_cluster/health"
  ```

# Resources and Further Reading
