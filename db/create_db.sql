CREATE TABLE IF NOT EXISTS couriers(
    id INTEGER PRIMARY KEY,
    type VARCHAR(4) NOT NULL,
    regions TEXT NOT NULL,
    working_hours TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY,
    weight FLOAT NOT NULL,
    region INTEGER NOT NULL,
    delivery_hours TEXT NOT NULL,
    assigned INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    complete_time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders_assigned(
    order_id INTEGER PRIMARY KEY,
    courier_id INTEGER NOT NULL,
    assign_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (courier_id) REFERENCES couriers (id)
);