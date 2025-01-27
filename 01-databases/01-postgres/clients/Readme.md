# Database Clients

# What is a Database Client?

- A **database client** is essentially any interface or channel that allows you to connect to and interact with a database. The purpose of a client is to send queries to the database, retrieve results, and perform database operations like inserting, updating, or deleting records.
- **How Database Clients Work**: Under the hood, a database client:
  1. Connects to the database using a driver (a protocol-specific implementation, such as JDBC for Java, ODBC for Windows, or custom drivers for specific databases).
  2. Sends queries (SQL for relational databases or queries like BSON for MongoDB)
  3. Receives responses from the database, such as query results or success/failure messages.
