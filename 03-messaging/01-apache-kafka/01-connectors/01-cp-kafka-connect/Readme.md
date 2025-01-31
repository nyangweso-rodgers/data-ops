# cp-kafka-connect

## Table Of Contents

# What is Kafka Connect?

- **Kafka Connect** is a component of **Apache Kafka** that’s used to perform streaming integration between **Kafka** and other systems such as **databases**, **cloud services**, **search indexes**, **file systems**, and **key-value stores**. It makes it simple to quickly define **connectors** that move large data sets in and out of **Kafka**.

# Commands

1. **Command 1**: **Get Available Connector Plugins**

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

2. **Command 2**: **Register Source Connector**

   - Register jdbc Postgres Source Connector by:

     ```sh
      curl -X POST --location "http://localhost:8083/connectors" -H "Content-Type: application/json" -H "Accept: application/json" -d @01-customers-postgresdb-using-json.json
     ```

   - Example Output:

3. **Command 3**: **Get a List of all Connectors**

   - To get a list of connectors for your Apache Kafka® cluster:

     ```sh
       curl --location --request GET 'http://localhost:8083/connectors'
     ```

   - Example Output:
     ```sh
       ["jdbc-json-connector-for-customers-postgresdb"]
     ```

4. **Command 4**: **Check the Connector Status**

   - Use the following command to check the status of your Kafka Connect connector

     ```sh
       curl -X GET http://localhost:8083/connectors/jdbc-json-connector-for-customers-postgresdb/status
     ```

   - Example Output:

5. **Command 5**: **Pause a Connector**

- Command:
- Examle:
  ```sh
    curl -X PUT http://localhost:8083/connectors/jdbc-json-connector-for-customers-postgresdb/pause
  ```

6. **Command 6**: **Delete a Connector**

   - Remove the **connectors** by:

     ```sh
       curl -X DELETE http://localhost:8083/connectors/jdbc-json-connector-for-customers-postgresdb
     ```

   - Example Output:

# Resources and Further Reading
