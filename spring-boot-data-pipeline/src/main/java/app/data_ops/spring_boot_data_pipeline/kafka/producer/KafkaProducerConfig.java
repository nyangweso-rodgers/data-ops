package app.data_ops.spring_boot_data_pipeline.kafka.producer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.kafka.clients.admin.AdminClient;
import org.apache.kafka.clients.admin.AdminClientConfig;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.errors.TopicExistsException;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.context.annotation.Configuration;

import java.util.Collections;
import java.util.Properties;
import java.util.concurrent.ExecutionException;

@Configuration
public class KafkaProducerConfig {

    private static final Logger log = LoggerFactory.getLogger(KafkaProducerConfig.class);
  public KafkaProducerConfig() { 
		//System.out.println("Test Kafka Producer"); 
        log.info("............. Starting Kafka Producer");

        
        // Adjust the bootstrapServers value based on where your producer is running
        //String bootstrapServers = "127.0.0.1:29092";
        String bootstrapServers = "kafka:29092";  // Use 'localhost' for external clients

        String topicName = "demo-java";

        // create Producer properties
        Properties properties = new Properties();
        properties.setProperty(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        properties.setProperty(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        properties.setProperty(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

        // create the producer
        KafkaProducer<String, String> producer = new KafkaProducer<>(properties);

        // Create the topic if it doesn't exist
        createTopicIfNotExists(bootstrapServers, topicName);

        // create a producer record 
        ProducerRecord<String, String> producerRecord =
                new ProducerRecord<>("demo-java", "test kafka message with java");

        // send data - asynchronous
        producer.send(producerRecord);

        // flush data
        producer.flush();
        // flush and close producer
        producer.close();
	}  
        private static void createTopicIfNotExists(String bootstrapServers, String topicName) {
        Properties adminProperties = new Properties();
        adminProperties.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);

        try (AdminClient adminClient = AdminClient.create(adminProperties)) {
            NewTopic newTopic = new NewTopic(topicName, 1, (short) 1);
            adminClient.createTopics(Collections.singletonList(newTopic)).all().get();
            log.info("Topic '{}' created successfully", topicName);
        } catch (ExecutionException e) {
            if (e.getCause() instanceof TopicExistsException) {
                log.info("Topic '{}' already exists", topicName);
            } else {
                log.error("Error creating topic '{}'", topicName, e);
            }
        } catch (InterruptedException e) {
            log.error("Error creating topic '{}'", topicName, e);
            Thread.currentThread().interrupt();
        }
    }
        
        
}
