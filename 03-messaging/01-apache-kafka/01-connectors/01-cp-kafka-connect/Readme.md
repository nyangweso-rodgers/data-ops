# cp-kafka-connect

## Table Of Contents

# Commands:

## Command 1. Get Available Connector Plugins

- If you need to check the list of available **plugins** you should hit `localhost:8083/connector-plugins`

  ```sh
      curl localhost:8083/connector-plugins
      # or
      curl localhost:8083/connector-plugins | json_pp
  ```

- Examle Output:

  ```json
  [
    {
      "class": "io.confluent.connect.jdbc.JdbcSinkConnector",
      "type": "sink",
      "version": "10.7.6"
    },
    {
      "class": "io.confluent.connect.jdbc.JdbcSourceConnector",
      "type": "source",
      "version": "10.7.6"
    },
    {
      "class": "org.apache.kafka.connect.mirror.MirrorCheckpointConnector",
      "type": "source",
      "version": "1"
    },
    {
      "class": "org.apache.kafka.connect.mirror.MirrorHeartbeatConnector",
      "type": "source",
      "version": "1"
    },
    {
      "class": "org.apache.kafka.connect.mirror.MirrorSourceConnector",
      "type": "source",
      "version": "1"
    }
  ]
  ```

## Command 2. Register Source Connector

- Register jdbc Postgres Source Connector by:

  ```sh
   curl -X POST --location "http://localhost:8083/connectors" -H "Content-Type: application/json" -H "Accept: application/json" -d @01-customers-postgresdb-using-json.json
  ```

- Example Output:

## Command 3. Get a List of all Connectors

- To get a list of connectors for your Apache Kafka® cluster:

  ```sh
    curl --location --request GET 'http://localhost:8083/connectors'
  ```

- Example Output:
  ```sh
    ["jdbc-json-connector-for-customers-postgresdb"]
  ```

## Command 4. Check the Connector Status

- Use the following command to check the status of your Kafka Connect connector
  ```sh
    curl -X GET http://localhost:8083/connectors/jdbc-json-connector-for-customers-postgresdb/status
  ```
- Example Output:

## Command 5. Pause a Connector

- Command:
- Examle:
  ```sh
    curl -X PUT http://localhost:8083/connectors/jdbc-json-connector-for-customers-postgresdb/pause
  ```

## Command 6. Delete a Connector

- Remove the **connectors** by:
  ```sh
    curl -X DELETE http://localhost:8083/connectors/jdbc-json-connector-for-customers-postgresdb
  ```
- Example Output:

# Resources and Further Reading
