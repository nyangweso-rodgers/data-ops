-- Create the `customers` database
CREATE DATABASE customers;

-- Create default tables in `customers` database
\c customers

-- Install the pgcrypto extension to enable gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the default tables in `customers` database
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    status BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(255) DEFAULT 'default@admin.com',
    updated_by VARCHAR(255) DEFAULT 'default@admin.com'
);

-- Create the `orders` database
CREATE DATABASE orders;

-- Create default tables in `orders` database
\c orders

-- Install the pgcrypto extension to enable gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the default tables in `orders` database
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    order_date TIMESTAMP DEFAULT now(),
    amount NUMERIC(10, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
