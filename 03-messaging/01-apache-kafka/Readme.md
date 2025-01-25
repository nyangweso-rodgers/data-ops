# Apache Kafka Docker Container

## Tabel Of Contents

# Commands

## 2. List Available Kafka Topics

- Use the `kafka-topics` command to list the **topics** in the **Kafka cluster**:
  ```sh
    #available kafka topics
    kafka-topics --list --bootstrap-server kafka:29092
  ```
- If no **topics** exists, the following will be returned:
  ```sh
    __consumer_offsets
    _schemas
  ```

# Resources and Further Reading
