# Data Ops

# Project Description

- For Data Pipeline Service with Apache Kafka, Postgres, and MongoDB.

# Running MongoDB Docker Containe

- Check my []() on how to run a MongoDB Docker container.

  ```yml
  version: "1"
  services:
  mongo:
    image: mongo
    container_name: mongo
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  volumes:
  mongodb_data:
  ```

# Running Postgres Docker Container

# Running Apache Kafka Docker Container

# Running Schema Registry Docker Container

# Running kafka-ui Docker Container

#

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Docker-Commands](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/01-Docker-Commands/Readme.md)
