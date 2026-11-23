-- Sample ride-hailing schema (Ola-style), used by db/seed.py

DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS drivers;

CREATE TABLE customers (
    customer_id       INTEGER PRIMARY KEY,
    customer_name     VARCHAR(100) NOT NULL,
    city              VARCHAR(50)  NOT NULL,
    signup_date       DATE,
    avg_rating_given  NUMERIC(2,1)
);

CREATE TABLE drivers (
    driver_id     INTEGER PRIMARY KEY,
    driver_name   VARCHAR(100) NOT NULL,
    city          VARCHAR(50)  NOT NULL,
    vehicle_type  VARCHAR(20),
    driver_rating NUMERIC(2,1),
    total_trips   INTEGER
);

CREATE TABLE bookings (
    booking_id      INTEGER PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(customer_id),
    driver_id       INTEGER REFERENCES drivers(driver_id),
    city            VARCHAR(50) NOT NULL,
    pickup_area     VARCHAR(100),
    drop_area       VARCHAR(100),
    distance_km     NUMERIC(5,1),
    fare_amount     NUMERIC(10,2),
    booking_status  VARCHAR(20),          -- Completed / Cancelled
    customer_rating NUMERIC(2,1),
    booking_date    TIMESTAMP
);
