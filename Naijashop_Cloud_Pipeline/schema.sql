--- Building Naijashop data pipeline - CORE SCHEMA
-- 

DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- CREATING CUSTOMERS TABLE - will show details of the customer who wants to make a purchase


CREATE TABLE customers(
            customer_id SERIAL PRIMARY KEY,
			full_name VARCHAR(120) NOT NULL,
			email VARCHAR(150) UNIQUE,
			city VARCHAR(80),
			state VARCHAR(80),
			signup_date DATE NOT NULL

);

SELECT *
FROM customers;

-- CREATING PRODUCTS TABLE - Will show the products available on the shop

CREATE TABLE products(
        product_id SERIAL PRIMARY KEY,
		product_name VARCHAR(150) NOT NULL,
		category VARCHAR(80) NOT NULL,
		price NUMERIC(10, 2) NOT NULL CHECK(price >= 0),
		stock_qty INTEGER NOT NULL DEFAULT 0 CHECK(stock_qty >= 0)


);


SELECT *
FROM products;

-- CREATING ORDERS TABLE - Will show the details of the order made

CREATE TABLE orders(
       order_id SERIAL PRIMARY KEY,
	   customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
	   order_date TIMESTAMP NOT NULL,
	   status VARCHAR(20) NOT NULL CHECK (status IN('pending', 'paid', 'shipped', 'delivered', 'cancelled'))


);

SELECT *
FROM orders;

-- CREATING ORDER ITEMS TABLE - will act as the junction table that will connect the order items , orders and products

CREATE TABLE order_items(
        order_item_id SERIAL PRIMARY KEY,
		order_id INTEGER NOT NULL REFERENCES orders(order_id),
		product_id INTEGER NOT NULL REFERENCES products(product_id),
		quantity INTEGER NOT NULL CHECK (quantity > 0),
		unit_price   NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)  -- price captured at the time of order
		
		
);

SELECT *
FROM order_items;

-- CREATING PAYMENTS TABLE - Will show details of the transaction made 

CREATE TABLE payments(
       payment_id SERIAL PRIMARY KEY,
	   order_id INTEGER NOT NULL REFERENCES orders(order_id),
	   method VARCHAR(30) NOT NULL CHECK (method IN ('card', 'bank_transfer','ussd','cash_on_delivery')),
	   amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
	   status VARCHAR(20) NOT NULL CHECK (status IN ('pending','successful','failed','refunded')),
	   paid_at TIMESTAMP


);

SELECT *
FROM payments;


-- We create indexes for common query patterns

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_payments_order_id ON payments(order_id);

-- Confirm your tables in the naijashop.db

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;


 
