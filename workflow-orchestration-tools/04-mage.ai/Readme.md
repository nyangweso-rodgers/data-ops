# Mage.ai

- **Mage** is a free and open-source data pipeline tool for data transformation and integration. Each stage in the pipeline is a separate file that contains reusable, tested code with data validations.

- **Features**
  1. **Simplified Development**: Mage-AI utilizes Python, R, and SQL, allowing data engineers to leverage their existing skillsets. Additionally, its interactive notebook UI streamlines development and visualization.
  2. **Focus on Data**: Mage-AI prioritizes data as a first-class citizen. It offers seamless data lineage tracking and facilitates the transformation of large datasets directly within your data warehouse or using Spark integration.
  3. **Scalability Made Easy**: Mage-AI empowers single developers or small teams to manage thousands of pipelines efficiently. It provides effortless deployment on major cloud platforms and scales to handle massive datasets without burdensome infrastructure requirements.
  4. **Operational Excellence**: Mage-AI integrates built-in monitoring, alerting, and an intuitive UI for comprehensive pipeline observability. This allows proactive identification and resolution of issues.
  5. User-friendly interface
  6. Interactive notebook UI
  7. Streamlined development experience
  8. Focus on data-centric workflows
  9. Scalability for large datasets
  10. Built-in operational tools

# Installation

- Clone github repository
  ```bash
      git clone https://github.com/mage-ai/compose-quickstart.git mage-quickstart
      cd mage-quickstart
      cp dev.env .env && rm dev.env
      docker compose up
  ```
