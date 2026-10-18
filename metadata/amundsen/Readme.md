# Amundsen

- **Why Amundsen Uses Neo4j**: Amundsen is a data catalog - it needs to track:

  - Tables and their columns
  - Which schemas contain which tables
  - Relationships between tables (lineage)
  - Who owns what data
  - Usage statistics
  - Column statistics

- All these are highly interconnected relationships, which is exactly what graph databases excel at! Graph databases allow you to navigate deep hierarchies, find hidden connections between distant items, and discover inter-relationships between items

# Setup

## Prerequisites

1.  Neo4j container is running (container name: `neo4j`)
2.  Elasticsearch container is running (container name: `elasticsearch`)

# Resources and Further Reading

1. [amundsen.io](https://www.amundsen.io/)
