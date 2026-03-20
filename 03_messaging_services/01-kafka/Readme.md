# Apache Kafka Docker Container

## Tabel Of Contents

# Commands

1. **Command 1**: **Access Kafka Shell of the Kafka Container**

   ```sh
     docker exec -it kafka bash
   ```

2. **Command 2**: **List Available Kafka Topics**

   - Use the `kafka-topics` command to list the **topics** in the **Kafka cluster**:
     ```sh
       kafka-topics --list --bootstrap-server kafka:29092
     ```
   - If no **topics** exists, the following will be returned:
     ```sh
       __consumer_offsets
       _schemas
     ```

3. **Command 3**: **Inspect the contents of the Directories**

   ```sh
    ls /usr/bin
    #or
    ls /bin
   ```

4. **Command 4**: **Verify Kafka binaries**

   ```sh
    ls -l /usr/bin | grep kafka
   ```

5. **Command 5**: **Create a New Kafka Topic**

   - Syntax
     ```sh
        kafka-topics --bootstrap-server localhost:8098 --create --topic <topic_name> --partitions <num_partitions> --replication-factor <replication_factor>
     ```
   - Examle:
     ```sh
      kafka-topics --create --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 --topic users.customers
     ```

6. **Command 6**: **Describe Kafka Topics**
   - Example:
     ```sh
      kafka-topics --bootstrap-server localhost:29092 --describe --topic test-kafka-topic
     ```
7. **Command 7**: **Delete Kafka Topic**
   - Syntax:
     ```sh
      kafka-topics --bootstrap-server localhost:29092 --delete --topic <topic_name>
     ```  
    - Example:
      ```sh
         kafka-topics --bootstrap-server localhost:29092 --delete --topic  test-kafka-topic
      ``` 
# Resources and Further Reading
