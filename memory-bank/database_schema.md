# Database Schema (PostgreSQL) - Rella Analytics

This document outlines the proposed initial database schema. Relationships are indicative and types are standard PostgreSQL types.

**Legend:**
*   `PK`: Primary Key
*   `FK`: Foreign Key
*   `NN`: Not Null

## Core Entities

**locations**
*   `location_id` PK SERIAL NN
*   `name` VARCHAR(100) NN (e.g., 'Napa', 'Vacaville')
*   `address` TEXT
*   `created_at` TIMESTAMP NN DEFAULT CURRENT_TIMESTAMP

**treatment_categories**
*   `category_id` PK SERIAL NN
*   `name` VARCHAR(100) NN UNIQUE (e.g., 'Injectables', 'Laser Treatments')
*   `description` TEXT

**services**
*   `service_id` PK SERIAL NN
*   `category_id` FK REFERENCES treatment_categories(category_id) NN
*   `name` VARCHAR(150) NN (e.g., 'Botox Injection', 'Hydrafacial Basic')
*   `description` TEXT
*   `standard_price` DECIMAL(10, 2)
*   `standard_duration_minutes` INTEGER
*   `is_active` BOOLEAN DEFAULT TRUE

**products**
*   `product_id` PK SERIAL NN
*   `name` VARCHAR(150) NN (e.g., 'Tirzepatide 1x Month', 'Tinted Defense')
*   `description` TEXT
*   `sku` VARCHAR(50) UNIQUE
*   `retail_price` DECIMAL(10, 2)
*   `cost_price` DECIMAL(10, 2) -- For profitability
*   `is_active` BOOLEAN DEFAULT TRUE

**expense_categories**
*   `expense_category_id` PK SERIAL NN
*   `name` VARCHAR(100) NN UNIQUE (e.g., 'Product/Consumables Cost', 'Staff Compensation')
*   `description` TEXT

**service_tools**
*   `tool_id` PK SERIAL NN
*   `name` VARCHAR(100) NN UNIQUE (e.g., 'Laser Machine A', 'CoolSculpting Unit 1')
*   `description` TEXT
*   `purchase_date` DATE
*   `initial_cost` DECIMAL(12, 2)
*   `location_id` FK REFERENCES locations(location_id) -- Where the tool resides
*   `is_active` BOOLEAN DEFAULT TRUE

**employees**
*   `employee_id` PK SERIAL NN
*   `first_name` VARCHAR(50) NN
*   `last_name` VARCHAR(50) NN
*   `role` VARCHAR(50) (e.g., 'Aesthetician', 'Nurse Injector', 'Front Desk')
*   `hire_date` DATE
*   `location_id` FK REFERENCES locations(location_id) -- Primary location
*   `is_active` BOOLEAN DEFAULT TRUE

**customers**
*   `customer_id` PK SERIAL NN -- Anonymized ID
*   `created_at` TIMESTAMP NN DEFAULT CURRENT_TIMESTAMP
*   `first_visit_date` DATE
*   `location_id` FK REFERENCES locations(location_id) -- Location of first visit/primary

## Transactional Data

**transactions**
*   `transaction_id` PK SERIAL NN
*   `customer_id` FK REFERENCES customers(customer_id) NN
*   `employee_id` FK REFERENCES employees(employee_id) NN -- Employee handling transaction
*   `location_id` FK REFERENCES locations(location_id) NN
*   `transaction_time` TIMESTAMP NN DEFAULT CURRENT_TIMESTAMP
*   `total_amount` DECIMAL(12, 2) NN
*   `discount_amount` DECIMAL(12, 2) DEFAULT 0
*   `tax_amount` DECIMAL(12, 2) DEFAULT 0
*   `payment_method` VARCHAR(50)

**transaction_items**
*   `item_id` PK SERIAL NN
*   `transaction_id` FK REFERENCES transactions(transaction_id) NN
*   `item_type` VARCHAR(10) NN CHECK (item_type IN ('service', 'product'))
*   `service_id` FK REFERENCES services(service_id) -- NULL if item_type is 'product'
*   `product_id` FK REFERENCES products(product_id) -- NULL if item_type is 'service'
*   `quantity` INTEGER NN DEFAULT 1
*   `unit_price` DECIMAL(10, 2) NN -- Price at time of transaction
*   `total_price` DECIMAL(12, 2) NN -- quantity * unit_price
*   `discount_amount` DECIMAL(12, 2) DEFAULT 0
*   `cost_price` DECIMAL(10, 2) -- Cost at time of transaction (for profit calc)

**expenses**
*   `expense_id` PK SERIAL NN
*   `expense_category_id` FK REFERENCES expense_categories(expense_category_id) NN
*   `location_id` FK REFERENCES locations(location_id) NN
*   `expense_date` DATE NN
*   `amount` DECIMAL(12, 2) NN
*   `description` TEXT
*   `vendor` VARCHAR(100)
*   `related_entity_type` VARCHAR(20) -- Optional (e.g., 'service_tool', 'product')
*   `related_entity_id` INTEGER -- Optional FK (e.g., tool_id, product_id)

**bookings**
*   `booking_id` PK SERIAL NN
*   `customer_id` FK REFERENCES customers(customer_id) NN
*   `employee_id` FK REFERENCES employees(employee_id) NN -- Provider
*   `service_id` FK REFERENCES services(service_id) NN
*   `location_id` FK REFERENCES locations(location_id) NN
*   `booking_time` TIMESTAMP NN -- Scheduled start time
*   `duration_minutes` INTEGER NN -- Scheduled duration
*   `status` VARCHAR(20) NN DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'Completed', 'Cancelled', 'No Show'))
*   `notes` TEXT
*   `created_at` TIMESTAMP NN DEFAULT CURRENT_TIMESTAMP
*   `related_transaction_id` FK REFERENCES transactions(transaction_id) -- Link if resulted in sale

**tool_usage_log** -- To track utilization
*   `log_id` PK SERIAL NN
*   `tool_id` FK REFERENCES service_tools(tool_id) NN
*   `employee_id` FK REFERENCES employees(employee_id) -- Who used it
*   `booking_id` FK REFERENCES bookings(booking_id) -- Link to appointment
*   `start_time` TIMESTAMP NN
*   `end_time` TIMESTAMP NN
*   `usage_minutes` INTEGER -- Calculated (end_time - start_time)
*   `notes` TEXT

## Notes
*   Indexing strategies will be crucial for performance on larger datasets (e.g., on date/time columns, foreign keys, filterable fields).
*   Consider adding tables for marketing campaigns, inventory tracking, etc. as needed.
*   Data types like `DECIMAL` ensure precision for financial calculations. 