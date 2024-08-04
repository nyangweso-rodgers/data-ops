package app.data_ops.spring_boot_data_pipeline;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class SpringBootDataPipelineApplication {

	private static final Logger logger = LoggerFactory.getLogger(SpringBootDataPipelineApplication.class);
 
	public static void main(String[] args) { 
		SpringApplication.run(SpringBootDataPipelineApplication.class, args);
		logger.info("Spring Boot Data Pipeline Application started successfully.");
		//System.out.println("This is My First Java Program"); 
	}

}
