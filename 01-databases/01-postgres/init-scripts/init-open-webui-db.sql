-- Create the `open_webui` database
CREATE DATABASE open_webui;

-- Switch to the `open_webui` database
\c open_webui

-- Install the pgcrypto extension to enable gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the default tables in `open_webui` database
-- Create a sample table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);