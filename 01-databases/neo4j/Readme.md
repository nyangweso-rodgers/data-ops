# Neo4j

## Table of Contents

# Neo4j

- **Neo4j** is a graph database that stores data as nodes, relationships, and properties instead of in tables or documents
- **Features**
  - Stores relationships natively alongside the data elements in a more flexible format, allowing optimization of data traversing and millions of connections to be accessed per second
  - Relationships are "first-class citizens" - treated as importantly as the data itself
  -

# Key Concepts

## Nodes

- **Nodes**: Represent entities (like a table, a person, a company)
- **Relationships**: Connections between nodes (like "Table BELONGS_TO Schema")
- **Properties**: Key-value pairs stored on nodes or relationships

## The Query Language (Cypher)

- **Neo4j** uses **Cypher**, which allows you to match patterns and relationships using a visual, SQL-like syntax Atlan.
- For example:

  ```cypher
    // Find all tables in the public schema
    MATCH (t:Table)-[:BELONGS_TO]->(s:Schema {name: 'public'})
    RETURN t.name

    // Find columns with high null percentages
    MATCH (c:Column)-[:HAS_STATS]->(s:Stats)
    WHERE s.null_percentage > 10
  RETURN c.name, s.null_percentage
  ```

# Setup

- **Neo4j** comes with a built-in web-based GUI called **Neo4j Browser**, which is perfect for exploring your database visually. It's accessible right after your container starts up, and it lets you:

  - Run Cypher queries (Neo4j's query language) to inspect data.
  - Visualize graphs (nodes, relationships, properties) in an interactive diagram.
  - View database schema details like labels (similar to "tables" in relational DBs), node/relationship types, and indexes.
  - Export results, manage sessions, and more.

- **How to Access:**

  - Ensure your Neo4j container is running: `docker-compose up -d neo4j`
  - Open a web browser and go to: http://localhost:7474
  - Log in with the credentials from your environment variables:

- **Understanding the Directories in Neo4j Setup**

  - In the Docker Compose configuration, the volume mount `./data/neo4j:/data` maps the host directory `./data/neo4j` to the `/data` path inside the **Neo4j container**. This is where **Neo4j** stores its persistent data by default (the official Neo4j Docker image for version 3.5 is configured to use `/data` as the data directory). When you start the container and create or query data, **Neo4j** populates subdirectories under `/data`, which appear on your host as `./data/neo4j/<subdir>`. These ensure your graph data survives container restarts.
  - `./data/neo4j/databases/` directory:

    - Stores the core files for your graph database(s). In Community Edition 3.5, there's only one default database (named graph.db), so you'll see a graph.db/ subdirectory here.

  - `./data/neo4j/dbms/` directory:
    - Holds DBMS (Database Management System) metadata and supporting files for overall system management, separate from the actual graph data.

# Resources and Further Reading
