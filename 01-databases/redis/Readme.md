# Redis

## Table Of Contents

# Requirements

- **RedisInsight** (Optional)
  - RedisInsight is the official GUI / workbench for **Redis**.
  - Here's what you can do with it:
    1. Data Exploration & Browsing
       - View your keys (strings, lists, sets, hashes, sorted sets, JSON, streams, etc.)
       - Search & filter by key name or type.
       - Inspect and edit values in a friendly UI (instead of using `redis-cli`).
       - Explore **RedisJSON documents** in a structured tree view.
    2. Performance Monitoring
       - Monitor memory usage, CPU load, network traffic, and client connections in real time.
       - See top keys by memory consumption (helps detect memory leaks or hot keys).
       - Track **slow queries** (like `keys *` or heavy `zrange` calls).
    3. Query & Debugging
       - Built-in **command-line console** with autocomplete.
       - Run Redis commands (GET, HGETALL, ZADD, etc.) directly inside the UI.
       - Inspect performance impact of queries (latency, execution time).
    4. Module Support
       - If you’re using Redis modules, RedisInsight gives you a UI tailored for them:
         - **RedisJSON** → browse JSON docs like a NoSQL DB.
         - **RediSearch** → run full-text search queries.
         - **RedisGraph** → visualize graphs.
         - **RedisTimeSeries** → chart time series data.
    5. Database Management
       - Add/manage multiple Redis connections (local, remote, cloud).
       - Configure TLS/authentication for secure connections.
       - Export/import data

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
