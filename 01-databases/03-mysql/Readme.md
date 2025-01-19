# How To Run Mysql In Docker With Data Persistence

## Step 1. Create Dockerfile

- Create a new file with the name `DockerFile`. Add the following lines of code to the file.

  ```DockerFile
    # Use the official MySQL image as the base image
    FROM mysql:latest
    LABEL authors="msamgan" # update with your name.

    # Set the default environment variables (customize as needed)
    ENV MYSQL_ROOT_PASSWORD=root
    ENV MYSQL_DATABASE=my_database
    ENV MYSQL_USER=user
    ENV MYSQL_PASSWORD=password

    # Expose the default MySQL port
    EXPOSE 3306
  ```

## Step 2. Create `docker-compose.yml`

- Create a new file with the name `docker-compose.yml` and add the following content to the file.
  ```yml
  services: # Define services
    mysql: # Define MySQL service
      build: . # Build MySQL image from Dockerfile in the same directory
      container_name: mysql_service # Name the container
      environment: # Set environment variables
      MYSQL_ROOT_PASSWORD: root # Set MySQL root password
      MYSQL_DATABASE: my_database # Create a database named my_database
      MYSQL_USER: user # Create a user named user
      MYSQL_PASSWORD: password # Set user password
      ports: # Expose MySQL port
        - "3306:3306" # Map container port 3306 to host port 3306
      volumes: # Attach volumes
        - ./mysql_data:/var/lib/mysql # Attach volume to persist MySQL data in the same directory
  ```

## Step 3. Run Docker Container

- Run docker container by:
  ```sh
    docker compose up -d
  ```
