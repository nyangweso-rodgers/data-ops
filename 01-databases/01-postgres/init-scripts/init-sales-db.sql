-- Create the `sales` database
CREATE DATABASE sales;

-- Switch to the `sales` database
\c sales

-- Install the pgcrypto extension to enable gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the default tables in `sales` database
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_date TIMESTAMP DEFAULT now(),
    amount NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT now() NOT NULL,
    updated_at TIMESTAMP DEFAULT now() NOT NULL,
    created_by VARCHAR(255) DEFAULT 'default@admin.com',
    updated_by VARCHAR(255) DEFAULT 'default@admin.com'
);