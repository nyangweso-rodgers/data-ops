package app.data_ops.spring_boot_data_pipeline.kafka;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.Bean; // <-- Add this import
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class KafkaConfig {

    @Bean
    public NewTopic testJavaTopic() {
        return TopicBuilder.name("test-java-topic")
        .partitions(1)
        .replicas(1)
        .build();
    }
}
