CREATE TABLE IF NOT EXISTS couriers(
    id INTEGER PRIMARY KEY,
    type VARCHAR(4) NOT NULL,
    regions TEXT NOT NULL,
    working_hours TEXT NOT NULL,
    rating FLOAT DEFAULT 0,
    earning INT DEFAULT 0
);