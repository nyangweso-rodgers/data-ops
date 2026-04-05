-- n8n Database Initialization Script
-- This script creates the n8n database and user in your existing PostgreSQL instance
-- Run this manually or add it to your postgres init scripts

-- Create n8n database
CREATE DATABASE n8n
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Create n8n user (if not exists)
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'n8n') THEN
        CREATE USER n8n WITH PASSWORD 'your-secure-password-here';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n;

-- Switch to n8n database
\c n8n

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO n8n;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO n8n;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO n8n;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO n8n;

-- Add comment
COMMENT ON DATABASE n8n IS 'n8n Workflow Automation Platform Database';