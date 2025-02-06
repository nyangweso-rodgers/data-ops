-- Create the `users` database
CREATE DATABASE users;

-- Create default tables in `users` database
\c customers

-- Install the pgcrypto extension to enable gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the default tables in `users` database
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(18) NOT NULL,
    status BOOLEAN DEFAULT TRUE,
    
    email VARCHAR(100) NOT NULL,
    alt_email VARCHAR(100),

    phone_number VARCHAR(18) NOT NULL,
    alt_phone_number VARCHAR(18),

    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(255) DEFAULT 'default@admin.com',
    updated_by VARCHAR(255) DEFAULT 'default@admin.com'
);
