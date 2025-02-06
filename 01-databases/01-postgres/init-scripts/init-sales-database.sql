
-- Create the `sales` database
CREATE DATABASE sales;

-- Create default tables in `orders` database
\c orders

-- Install the pgcrypto extension to enable gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the default tables in `orders` database
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    --customer_id UUID NOT NULL,
    order_date TIMESTAMP DEFAULT now(),
    amount NUMERIC(10, 2) NOT NULL,
    --FOREIGN KEY (customer_id) REFERENCES customers(id)
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(255) DEFAULT 'default@admin.com',
    updated_by VARCHAR(255) DEFAULT 'default@admin.com'
);
