# FROM confluentinc/cp-server-connect-base:7.7.0
FROM confluentinc/cp-kafka-connect:7.1.0-1-ubi8
ENV CONNECT_PLUGIN_PATH: "/usr/share/java,/usr/share/confluent-hub-components"

############## Install neo4j ##############
#RUN confluent-hub install --no-prompt neo4j/kafka-connect-neo4j:2.0.2

############## Install Avro plugins ##############
#RUN confluent-hub install --no-prompt confluentinc/kafka-connect-avro-converter:5.5.4
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-avro-converter:7.7.0

# https://www.confluent.io/hub/confluentinc/kafka-connect-protobuf-converter
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-protobuf-converter:7.7.0 

############## Install JDBC plugins ##############
#RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.1.1
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.6

############## Install BigQuery plugins ##############
RUN confluent-hub install --no-prompt wepay/kafka-connect-bigquery:2.5.6
#RUN confluent-hub install --no-prompt wepay/kafka-connect-bigquery:latest

############## Install MongoDB plugins ##############
#RUN confluent-hub install --no-prompt mongodb/kafka-connect-mongodb:1.13.0