# Use an official OpenJDK runtime as a parent image
#FROM openjdk:17-jdk-slim
FROM openjdk:21-jdk-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project’s jar file into the container at /app
#COPY target/spring-boot-data-pipeline-0.0.1-SNAPSHOT.jar /app/spring-boot-data-pipeline.jar
COPY build/libs/spring-boot-data-pipeline-0.0.1-SNAPSHOT.jar /app/spring-boot-data-pipeline.jar

# Make port 8080 available to the world outside this container
EXPOSE 9093

# Run the jar file
ENTRYPOINT ["java", "-jar", "spring-boot-data-pipeline.jar"]