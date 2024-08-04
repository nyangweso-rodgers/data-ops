package app.data_ops.spring_boot_data_pipeline.kafka.consumer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;


@Configuration
public class KafkaConsumerConfig { 

    private static final Logger log = LoggerFactory.getLogger(KafkaConsumerConfig.class);
    public static void main(String[] args) { 
		//System.out.println("Test Kafka Consumer"); 
        log.info("Kafka Consumer");
	}  
}
