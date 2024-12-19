-- init-db.sql

-- Create a new database (optional, if not using POSTGRES_DB in environment variables)
CREATE DATABASE testdb;

-- Create a table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50),
  email VARCHAR(100)
);

-- Insert initial data
INSERT INTO users (username, email) VALUES ('admin', 'admin@example.com');