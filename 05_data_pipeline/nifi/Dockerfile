# Use the official NiFi image as the base
FROM apache/nifi:2.3.0

USER root
      RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

      # Add Postgres JDBC driver
      RUN wget -O /opt/nifi/nifi-current/lib/postgresql-42.7.3.jar \
          https://jdbc.postgresql.org/download/postgresql-42.7.3.jar

      # Add ClickHouse JDBC driver
      RUN wget -O /opt/nifi/nifi-current/lib/clickhouse-jdbc-0.6.4.jar \
          https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.6.4/clickhouse-jdbc-0.6.4.jar

      USER nifi