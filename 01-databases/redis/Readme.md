# Redis

## Table Of Contents

# Requirements

# Setup

- Connect to Redis:

  ```sh
  redis-cli -a $REDIS_PASSWORD
  ```

- Step: Test Connectivity:

  1. Using Docker Exec (if Redis runs in a container)

     ```sh
        docker exec -it <redis-container-name> redis-cli ping
     ```

  2. Using Python Script

     ```py
        import os
        import redis
        from dotenv import load_dotenv

        load_dotenv()

        r = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )

        print(r.ping())  # should print True
     ```

# Resources and Further Reading
