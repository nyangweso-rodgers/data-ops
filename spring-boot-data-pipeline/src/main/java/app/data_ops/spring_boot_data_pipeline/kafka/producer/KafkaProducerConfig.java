package app.data_ops.spring_boot_data_pipeline.kafka.producer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.context.annotation.Configuration;

import java.util.Properties;

@Configuration
public class KafkaProducerConfig {

    private static final Logger log = LoggerFactory.getLogger(KafkaProducerConfig.class);
  public static void main(String[] args) { 
		//System.out.println("Test Kafka Producer"); 
        log.info("............. Starting Kafka Producer");

        String bootstrapServers = "127.0.0.1:29092";

        // create Producer properties
        Properties properties = new Properties();
        properties.setProperty(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        properties.setProperty(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        properties.setProperty(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

        // create the producer
        KafkaProducer<String, String> producer = new KafkaProducer<>(properties);

        // create a producer record 
        ProducerRecord<String, String> producerRecord =
                new ProducerRecord<>("demo-java", "hello world");

        // send data - asynchronous
        producer.send(producerRecord);

        // flush data
        producer.flush();
        // flush and close producer
        producer.close();
	}     
}
