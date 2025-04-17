-- Drop tables if they exist to ensure a clean state
DROP TABLE IF EXISTS transaction_items;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS treatment_categories;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS bookings; -- Add drop for bookings
DROP TABLE IF EXISTS users; -- Add drop for users
-- Add drop statements for future tables (like transactions, customers) here

-- Users Table (For application login)
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, -- Store hashed passwords, not plain text
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Locations Table
CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT,
    latitude REAL, -- Add latitude
    longitude REAL -- Add longitude
);

-- Treatment Categories Table
CREATE TABLE treatment_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- Services Table (Treatments)
CREATE TABLE services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    standard_price REAL NOT NULL,
    standard_cost REAL, -- Add column for cost of service
    FOREIGN KEY (category_id) REFERENCES treatment_categories (category_id)
);

-- Products Table
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sku TEXT UNIQUE,
    retail_price REAL NOT NULL,
    category_id INTEGER, -- Can be NULL if not linked to a treatment category
    FOREIGN KEY (category_id) REFERENCES treatment_categories (category_id)
);

-- Employees Table
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT,
    location_id INTEGER,
    is_active INTEGER DEFAULT 1, -- 1 for true, 0 for false
    FOREIGN KEY (location_id) REFERENCES locations (location_id)
);

-- Customers Table
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT, -- Optional for simplicity
    last_name TEXT, -- Optional for simplicity
    address TEXT, -- Add address field
    latitude REAL, -- Add latitude
    longitude REAL, -- Add longitude
    -- email TEXT UNIQUE, -- Keep simple for now
    -- phone TEXT, -- Keep simple for now
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP -- Track when customer record was created
);

-- Bookings Table
CREATE TABLE bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    location_id INTEGER NOT NULL,
    service_id INTEGER, -- Optional: link to specific service booked
    employee_id INTEGER, -- Optional: link to specific employee booked
    booking_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- When the booking was made
    appointment_time TIMESTAMP NOT NULL, -- When the appointment is scheduled for
    status TEXT NOT NULL CHECK(status IN ('Booked', 'Completed', 'Cancelled', 'No Show')), -- Booking status
    notes TEXT, -- Optional notes
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    FOREIGN KEY (location_id) REFERENCES locations (location_id),
    FOREIGN KEY (service_id) REFERENCES services (service_id),
    FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

-- Transactions Table
CREATE TABLE transactions (
   transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
   customer_id INTEGER, -- Link to customer
   employee_id INTEGER,
   location_id INTEGER NOT NULL,
   transaction_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Ensure this stores datetime
   total_amount REAL NOT NULL, -- Calculated from items
   -- payment_method TEXT, -- Optional detail
   FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
   FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
   FOREIGN KEY (location_id) REFERENCES locations (location_id)
);

-- Transaction Items Table (Line items for each transaction)
CREATE TABLE transaction_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL,
    item_type TEXT NOT NULL, -- 'product' or 'service'
    product_id INTEGER,
    service_id INTEGER,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL, -- Price at the time of transaction
    -- discount REAL DEFAULT 0.0, -- Keep simple for now
    net_price REAL NOT NULL, -- (unit_price * quantity)
    FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE, -- Cascade delete if transaction is removed
    FOREIGN KEY (product_id) REFERENCES products (product_id),
    FOREIGN KEY (service_id) REFERENCES services (service_id),
    CHECK (item_type IN ('product', 'service')),
    CHECK ((item_type = 'product' AND product_id IS NOT NULL AND service_id IS NULL) OR
           (item_type = 'service' AND service_id IS NOT NULL AND product_id IS NULL))
); 