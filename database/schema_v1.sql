CREATE TABLE cart (
    id INTEGER NOT NULL, 
    quantity INTEGER NOT NULL, 
    customer_link INTEGER NOT NULL, 
    product_link INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(customer_link) REFERENCES customer (id), 
    FOREIGN KEY(product_link) REFERENCES product (id)
)

CREATE TABLE customer (
    id INTEGER NOT NULL, 
    email VARCHAR(100), 
    username VARCHAR(100), 
    password_hash VARCHAR(150), 
    date_joined DATETIME, 
    PRIMARY KEY (id), 
    UNIQUE (email)
)

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_each FLOAT,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES product(id)
)

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    total_price FLOAT NOT NULL DEFAULT 0,
    payment_method VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, payment_reference VARCHAR(200), date_created DATETIME,
    FOREIGN KEY(customer_id) REFERENCES customer(id)
)

CREATE TABLE product (
    id INTEGER NOT NULL, 
    product_name VARCHAR(100) NOT NULL, 
    current_price FLOAT NOT NULL, 
    previous_price FLOAT NOT NULL, 
    in_stock INTEGER NOT NULL, 
    product_picture VARCHAR(1000) NOT NULL, 
    flash_sale BOOLEAN, 
    date_added DATETIME, 
    PRIMARY KEY (id)
)

CREATE TABLE sqlite_sequence(name,seq)
