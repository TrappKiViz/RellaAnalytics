from flask import Flask, jsonify, request, g, session # Add session
from flask_cors import CORS # Import CORS
import os
import random
import sqlite3 # Import sqlite3
import click # Import click for CLI commands
from flask.cli import with_appcontext # Import for CLI commands
from datetime import date, timedelta, datetime
import pandas as pd # Placeholder for future data loading
from statsmodels.tsa.statespace.sarimax import SARIMAX
from werkzeug.utils import secure_filename # For file uploads
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Import the boulevard client functions
import boulevard_client

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, instance_relative_config=True) # Enable instance folder
app.config.from_mapping(
    SECRET_KEY='dev', # Replace with a real secret key for production!
    # Configure session type if needed (e.g., using Flask-Session)
    # SESSION_TYPE = 'filesystem' 
)
# FlaskSession(app) # Uncomment if using Flask-Session

# Explicitly allow the frontend origin when credentials are supported
CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # The endpoint name (function name) for your login route

@login_manager.user_loader
def load_user(user_id):
    """Loads user object from user ID stored in session."""
    db = get_db()
    user_data = db.execute(
        'SELECT user_id, username FROM users WHERE user_id = ?', (user_id,)
    ).fetchone()
    if user_data:
        # Return a User object (needs User class defined below)
        return User(id=user_data['user_id'], username=user_data['username'])
    return None
# --- End Flask-Login Setup ---

# --- User Class for Flask-Login ---
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    # Flask-Login requires a get_id method
    def get_id(self):
       return str(self.id)

# --- End User Class ---

# --- MOVED ASSOCIATION RULES ENDPOINT (SIMPLIFIED DEBUG VERSION) ---
# @app.route('/api/v1/analysis/basket_rules', methods=['GET']) # Changed path
# def get_association_rules():
#     """Performs market basket analysis - TEMPORARILY SIMPLIFIED FOR DEBUGGING."""
#     print("\n>>> BASKET RULES ROUTE HIT! (Simplified Version - MOVED EARLIER) <<<") # Updated debug print
#     
#     # --- Simple Hardcoded Response for Debugging ---
#     print("Returning hardcoded debug response for association rules.")
#     debug_response = {
#         "rules": [
#             {"antecedents_name": ("DEBUG Item A",), "consequents_name": ("DEBUG Item B",), "support": 0.1, "confidence": 0.5, "lift": 2.0}
#         ],
#         "message": "DEBUG: Hardcoded response - Route is working.",
#         "item_counts": {"DEBUG Item A": 10, "DEBUG Item B": 5}
#     }
#     return jsonify(debug_response)
# --- END OF MOVED ENDPOINT ---

# --- Database Configuration ---
DATABASE = os.path.join(app.instance_path, 'rella_analytics.sqlite')

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

def get_db():
    """Connects to the specific database."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row # Return rows as dict-like objects
    return g.db

def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database based on schema.sql."""
    db = get_db()
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

app.teardown_appcontext(close_db) # Register close_db to be called when app context ends
app.cli.add_command(init_db_command) # Register the init-db command

def seed_db():
    """Seeds the database with mock data AND simulated transactions."""
    db = get_db()
    cursor = db.cursor() # Use cursor for fetching IDs

    # --- Seed Admin User --- 
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'password'
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (ADMIN_USERNAME,))
        if not cursor.fetchone():
            password_hash = generate_password_hash(ADMIN_PASSWORD)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (ADMIN_USERNAME, password_hash)
            )
            print(f"Admin user '{ADMIN_USERNAME}' created.")
            db.commit() # Commit user creation immediately
        else:
            print(f"Admin user '{ADMIN_USERNAME}' already exists.")
    except sqlite3.Error as e:
        print(f"Error seeding admin user: {e}")
        # Decide if we should stop seeding entirely if admin fails?
        # For now, just print error and continue with other data.
        pass 

    # --- Seed Basic Data First --- 
    # Seed Locations
    for loc in MOCK_LOCATIONS:
        cursor.execute(
            "INSERT OR IGNORE INTO locations (location_id, name, address, latitude, longitude) VALUES (?, ?, ?, ?, ?)",
            (loc['location_id'], loc['name'], loc['address'], loc.get('latitude'), loc.get('longitude'))
        )
    # Seed Treatment Categories
    for cat in MOCK_TREATMENT_CATEGORIES:
        cursor.execute(
            "INSERT OR IGNORE INTO treatment_categories (category_id, name, description) VALUES (?, ?, ?)",
            (cat['category_id'], cat['name'], cat['description'])
        )
    # Seed Services
    for service in MOCK_SERVICES:
        cursor.execute(
            "INSERT OR IGNORE INTO services (service_id, category_id, name, standard_price, standard_cost) VALUES (?, ?, ?, ?, ?)",
            (service['service_id'], service['category_id'], service['name'], service['standard_price'], service['standard_cost'])
        )
    # Seed Products
    for product in MOCK_PRODUCTS:
        cursor.execute(
            "INSERT OR IGNORE INTO products (product_id, name, sku, retail_price, category_id) VALUES (?, ?, ?, ?, ?)",
            (product['product_id'], product['name'], product['sku'], product['retail_price'], product.get('category_id'))
        )
    # Seed Employees
    for emp in MOCK_EMPLOYEES:
        cursor.execute(
            "INSERT OR IGNORE INTO employees (employee_id, first_name, last_name, role, location_id) VALUES (?, ?, ?, ?, ?)",
            (emp['employee_id'], emp['first_name'], emp['last_name'], emp['role'], emp['location_id'])
        )
    db.commit() # Commit basic data before generating transactions

    # --- Simulate Transactions for Q1 2024 --- 
    print("Seeding transactions...")
    num_transactions_to_simulate = 1500 # Adjust as needed
    num_customers_to_simulate = 300   # Number of potential customers
    new_customer_probability = 0.1    # Chance a transaction is from a new customer

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31, 23, 59, 59)
    time_delta_seconds = (end_date - start_date).total_seconds()

    # Fetch IDs needed for simulation
    cursor.execute("SELECT location_id FROM locations")
    location_ids = [row['location_id'] for row in cursor.fetchall()]
    cursor.execute("SELECT employee_id, location_id FROM employees WHERE role != 'Front Desk'") # Exclude front desk from performing transactions
    employee_data = cursor.fetchall()
    employees_by_location = {}
    for row in employee_data:
        loc_id = row['location_id']
        if loc_id not in employees_by_location:
            employees_by_location[loc_id] = []
        employees_by_location[loc_id].append(row['employee_id'])

    cursor.execute("SELECT product_id, retail_price FROM products")
    products = {row['product_id']: row['retail_price'] for row in cursor.fetchall()}
    cursor.execute("SELECT service_id, standard_price FROM services")
    services = {row['service_id']: row['standard_price'] for row in cursor.fetchall()}

    # Simulate Customers with Staircase Density
    print(f"Simulating customers with defined density zones...")
    customer_pool = []
    # Define density zones and points per zone
    density_zones = [
        # Downtown Napa (~ -122.28, 38.30) - High Density
        {'coord': [-122.28, 38.30], 'count': 50},
        {'coord': [-122.27, 38.305], 'count': 30},
        {'coord': [-122.29, 38.295], 'count': 20},
        # Napa Outskirts - Mid Density
        {'coord': [-122.25, 38.28], 'count': 15},
        {'coord': [-122.24, 38.27], 'count': 10},
        # Vacaville (~ -121.96, 38.35) - Lower Density
        {'coord': [-121.96, 38.35], 'count': 10},
        {'coord': [-121.95, 38.36], 'count': 5},
        {'coord': [-121.97, 38.34], 'count': 3},
        # Sparse Outliers (Single count)
        {'coord': [-122.10, 38.40], 'count': 1},
        {'coord': [-122.40, 38.15], 'count': 1},
        {'coord': [-121.80, 38.50], 'count': 1}
    ]

    total_simulated = sum(zone['count'] for zone in density_zones)
    print(f"Total customers to simulate based on zones: {total_simulated}")

    for zone in density_zones:
        lon, lat = zone['coord']
        count = zone['count']
        for _ in range(count):
            # Generate creation date (can reuse previous logic or simplify)
            creation_seconds = random.uniform(0, time_delta_seconds) 
            created_at = start_date + timedelta(seconds=creation_seconds)
            created_at = max(datetime(2023, 1, 1), created_at) 
            
            # Add tiny jitter to avoid all points being identical (optional)
            jitter_lat = random.uniform(-0.001, 0.001)
            jitter_lon = random.uniform(-0.001, 0.001)
            sim_lat = lat + jitter_lat
            sim_lon = lon + jitter_lon

            # Insert customer with specific coordinates
            cursor.execute(
                "INSERT INTO customers (created_at, latitude, longitude) VALUES (?, ?, ?)", 
                (created_at, sim_lat, sim_lon)
            )
            customer_pool.append(cursor.lastrowid)
            
    db.commit()
    print(f"Inserted {len(customer_pool)} customers based on density zones.")

    # --- Simulate Bookings for Q1 2024 ---
    print("Simulating bookings...")
    num_bookings_to_simulate = 2500 # More bookings than transactions assumed
    booking_statuses = ['Completed'] * 75 + ['Cancelled'] * 15 + ['No Show'] * 8 + ['Booked'] * 2 # Weighted distribution
    
    # Use existing IDs
    # Ensure customer_pool has data from previous step
    if not location_ids or not services or not customer_pool:
        print("Error: Missing base data (locations, services, customers) for booking simulation.")
        return
        
    all_service_ids = list(services.keys())
    all_employee_ids = [e['employee_id'] for e in employee_data] if employee_data else []

    bookings_seeded = 0
    for i in range(num_bookings_to_simulate):
        cust_id = random.choice(customer_pool)
        loc_id = random.choice(location_ids)
        serv_id = random.choice(all_service_ids) if all_service_ids else None
        emp_id = random.choice(all_employee_ids) if all_employee_ids else None # Optional employee assignment
        status = random.choice(booking_statuses)

        # Simulate booking time and appointment time within Q1 2024
        booking_seconds = random.uniform(0, time_delta_seconds * 0.9) # Bookings happen earlier usually
        booking_time = start_date + timedelta(seconds=booking_seconds)
        
        # Appointment time is after booking time, within Q1
        min_appt_offset_seconds = timedelta(hours=1).total_seconds()
        max_appt_offset_seconds = timedelta(days=14).total_seconds()
        appt_offset = random.uniform(min_appt_offset_seconds, max_appt_offset_seconds)
        appointment_time = booking_time + timedelta(seconds=appt_offset)
        
        # Ensure appointment is within Q1 bounds
        appointment_time = min(end_date, appointment_time)
        appointment_time = max(start_date, appointment_time)
        # Ensure appointment time is after booking time if clamped
        appointment_time = max(booking_time + timedelta(minutes=5), appointment_time) 

        try:
            cursor.execute(
                "INSERT INTO bookings (customer_id, location_id, service_id, employee_id, booking_time, appointment_time, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cust_id, loc_id, serv_id, emp_id, booking_time, appointment_time, status)
            )
            bookings_seeded += 1
        except sqlite3.Error as e:
            print(f"Database error during booking seeding: {e}")
            db.rollback() # Rollback this booking attempt
            
    db.commit() # Commit bookings
    print(f"Seeded {bookings_seeded} bookings.")

    # Keep track of the first transaction time for each customer during seeding
    customer_first_transaction = {}

    transactions_seeded = 0
    for i in range(num_transactions_to_simulate):
        # Choose random location
        loc_id = random.choice(location_ids)
        
        # Choose random employee from that location (if available)
        possible_employees = employees_by_location.get(loc_id)
        if not possible_employees:
            # If no specific employee at location, maybe assign randomly or skip?
            # For now, let's pick any employee if location specific fails
            if employee_data:
                 emp_id = random.choice([e['employee_id'] for e in employee_data])
            else: 
                 emp_id = None # Or handle error
        else:
             emp_id = random.choice(possible_employees)

        # Choose random timestamp within Q1 2024
        random_seconds = random.uniform(0, time_delta_seconds)
        transaction_time = start_date + timedelta(seconds=random_seconds)

        # Assign Customer
        cust_id = None
        if random.random() < new_customer_probability:
            # Create a new customer for this transaction (within Q1)
            cursor.execute("INSERT INTO customers (created_at) VALUES (?)", (transaction_time,))
            cust_id = cursor.lastrowid
            customer_pool.append(cust_id) # Add to pool for future selection
        else:
            # Choose existing customer
            cust_id = random.choice(customer_pool)
        
        # Record first transaction time for this customer if not already seen
        if cust_id not in customer_first_transaction:
             customer_first_transaction[cust_id] = transaction_time
        else:
             customer_first_transaction[cust_id] = min(customer_first_transaction[cust_id], transaction_time)

        # Simulate 1 to 3 items per transaction
        num_items = random.randint(1, 3)
        transaction_items = []
        transaction_total = 0.0

        for _ in range(num_items):
            item_type = random.choice(['product', 'service'])
            if item_type == 'product' and products:
                prod_id = random.choice(list(products.keys()))
                quantity = random.randint(1, 3)
                unit_price = products[prod_id]
                net_price = unit_price * quantity
                transaction_items.append(('product', prod_id, None, quantity, unit_price, net_price))
                transaction_total += net_price
            elif item_type == 'service' and services:
                serv_id = random.choice(list(services.keys()))
                # Most services quantity 1, maybe Botox units higher?
                quantity = random.randint(1, 5) if serv_id == 101 else 1 # Example: Botox units
                unit_price = services[serv_id]
                net_price = unit_price * quantity
                transaction_items.append(('service', None, serv_id, quantity, unit_price, net_price))
                transaction_total += net_price

        if not transaction_items: # Skip if no items could be added
            continue

        try:
            # Insert transaction header
            cursor.execute(
                "INSERT INTO transactions (customer_id, employee_id, location_id, transaction_time, total_amount) VALUES (?, ?, ?, ?, ?)",
                (cust_id, emp_id, loc_id, transaction_time, round(transaction_total, 2))
            )
            transaction_id = cursor.lastrowid # Get the ID of the inserted transaction

            # Insert transaction items
            for item in transaction_items:
                item_type, prod_id, serv_id, quantity, unit_price, net_price = item
                cursor.execute(
                    "INSERT INTO transaction_items (transaction_id, item_type, product_id, service_id, quantity, unit_price, net_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (transaction_id, item_type, prod_id, serv_id, quantity, round(unit_price, 2), round(net_price, 2))
                )
            transactions_seeded += 1
        except sqlite3.Error as e:
            print(f"Database error during transaction seeding: {e}")
            db.rollback() # Rollback this transaction attempt
            # Decide whether to break or continue
            # continue 
        # Commit after each transaction or batch commits?
        # Committing after each is simpler for simulation but slower.
        # db.commit() # Commit each transaction individually

    # Update customer created_at based on first transaction if it's earlier
    print("Updating customer created_at based on first transaction times...")
    for cust_id, first_trans_time in customer_first_transaction.items():
         cursor.execute("UPDATE customers SET created_at = MIN(created_at, ?) WHERE customer_id = ?", (first_trans_time, cust_id))

    db.commit() # Final commit after loop and updates
    print(f"Finished seeding transactions.") # Keep the original finish message

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seed the database with mock data."""
    seed_db()
    click.echo('Database seeded.')

app.cli.add_command(seed_db_command) # Register the seed-db command

# --- Mock Data (Replace with real data loading later) ---

MOCK_LOCATIONS = [
    # Approximate coordinates for Napa and Vacaville
    {'location_id': 1, 'name': 'Napa', 'address': '123 Wine St', 'latitude': 38.2975, 'longitude': -122.2869},
    {'location_id': 2, 'name': 'Vacaville', 'address': '456 Outlet Dr', 'latitude': 38.3566, 'longitude': -121.9611}
]

MOCK_TREATMENT_CATEGORIES = [
    {"category_id": 1, "name": "Injectables", "description": "Botox, Fillers, etc."},
    {"category_id": 2, "name": "Laser Treatments", "description": "Hair removal, IPL, etc."},
    {"category_id": 3, "name": "Facial Treatments", "description": "Hydrafacials, Peels, etc."},
    {"category_id": 4, "name": "Body Contouring", "description": "Fat reduction, muscle toning."},
    {"category_id": 5, "name": "Wellness & IV Therapy", "description": "Vitamin drips, shots."},
    {"category_id": 6, "name": "Weight Loss", "description": "Semaglutide, Tirzepatide, etc."}
]

MOCK_SERVICES = [
    {"service_id": 101, "category_id": 1, "name": "Botox Injection (per unit)", "standard_price": 15.00, "standard_cost": 5.50},
    {"service_id": 102, "category_id": 1, "name": "Juvederm Ultra XC (1ml)", "standard_price": 650.00, "standard_cost": 280.00},
    {"service_id": 201, "category_id": 2, "name": "Laser Hair Removal - Small Area", "standard_price": 150.00, "standard_cost": 40.00},
    {"service_id": 301, "category_id": 3, "name": "Signature Hydrafacial", "standard_price": 199.00, "standard_cost": 65.00},
    {"service_id": 401, "category_id": 4, "name": "CoolSculpting Cycle", "standard_price": 750.00, "standard_cost": 250.00},
    {"service_id": 501, "category_id": 5, "name": "Immunity IV Drip", "standard_price": 175.00, "standard_cost": 55.00},
    {"service_id": 601, "category_id": 6, "name": "Semaglutide Consultation", "standard_price": 100.00, "standard_cost": 15.00}
]

MOCK_PRODUCTS = [
    {"product_id": 1, "name": "Tirzepatide 1x Month", "sku": "TIRZ01", "retail_price": 750.00, "category_id": 6},
    {"product_id": 2, "name": "Tinted Defense SPF", "sku": "SKN001", "retail_price": 55.00, "category_id": 3},
    {"product_id": 3, "name": "Semaglutide x1 Month Supply", "sku": "SEMA01", "retail_price": 450.00, "category_id": 6},
    {"product_id": 4, "name": "Lipid Cloud", "sku": "SKN005", "retail_price": 88.00, "category_id": 3},
    {"product_id": 10, "name": "Botox Vial", "sku": "INJ01", "retail_price": 500.00, "category_id": 1 },
]

MOCK_EMPLOYEES = [
    {"employee_id": 1, "first_name": "Jane", "last_name": "Doe", "role": "Nurse Injector", "location_id": 1},
    {"employee_id": 2, "first_name": "John", "last_name": "Smith", "role": "Aesthetician", "location_id": 2},
    {"employee_id": 3, "first_name": "Alice", "last_name": "Brown", "role": "Nurse Injector", "location_id": 2},
    {"employee_id": 4, "first_name": "Bob", "last_name": "White", "role": "Front Desk", "location_id": 1},
]

# --- End Mock Data ---


# Configuration (can be moved to a config file later)
# DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'Product Sales.csv') # Example path

@app.route('/')
def index():
    """Basic health check endpoint."""
    return jsonify({"status": "ok", "message": "Rella Analytics Backend is running!"})

# --- DATA / KPI Endpoints ---

def _build_filter_clause(location_id, start_date_str, end_date_str, date_column='transaction_time'):
    """Helper function to build WHERE clause and params for filters."""
    where_clauses = []
    params = []

    if location_id:
        where_clauses.append(f"t.location_id = ?")
        params.append(location_id)

    start_datetime = None
    end_datetime = None

    if start_date_str:
        try:
            start_datetime = datetime.strptime(start_date_str + " 00:00:00", '%Y-%m-%d %H:%M:%S')
            # where_clauses.append(f"t.{date_column} >= ?")
            # params.append(start_datetime)
        except ValueError:
            print(f"Warning: Invalid start_date format: {start_date_str}")
            pass # Ignore invalid date

    if end_date_str:
        try:
            # Include the entire end day
            end_datetime = datetime.strptime(end_date_str + " 23:59:59", '%Y-%m-%d %H:%M:%S')
            # where_clauses.append(f"t.{date_column} <= ?")
            # params.append(end_datetime)
        except ValueError:
            print(f"Warning: Invalid end_date format: {end_date_str}")
            pass # Ignore invalid date

    # Handle date range filtering correctly for SQLite's datetime handling
    if start_datetime and end_datetime:
        where_clauses.append(f"t.{date_column} BETWEEN ? AND ?")
        params.extend([start_datetime, end_datetime])
    elif start_datetime:
        where_clauses.append(f"t.{date_column} >= ?")
        params.append(start_datetime)
    elif end_datetime:
        where_clauses.append(f"t.{date_column} <= ?")
        params.append(end_datetime)
        
    where_clause_sql = " AND ".join(where_clauses) if where_clauses else "1=1" # Always true if no filters
    return where_clause_sql, params

@app.route('/api/v1/kpis', methods=['GET'])
@login_required
def get_kpis():
    """Retrieves key performance indicators from database transactions."""
    db = get_db()
    location_id = request.args.get('location_id', default=None, type=int)
    start_date_str = request.args.get('start_date', default=None, type=str)
    end_date_str = request.args.get('end_date', default=None, type=str)

    where_clause, params = _build_filter_clause(location_id, start_date_str, end_date_str)

    # --- Calculate Core KPIs --- 
    query_core = f"""
        SELECT 
            SUM(total_amount) as total_sales,
            COUNT(transaction_id) as num_transactions
        FROM transactions t
        WHERE {where_clause}
    """
    core_kpis = db.execute(query_core, params).fetchone()

    total_net_sales = core_kpis['total_sales'] if core_kpis and core_kpis['total_sales'] else 0
    num_transactions = core_kpis['num_transactions'] if core_kpis and core_kpis['num_transactions'] else 0
    avg_transaction_value = (total_net_sales / num_transactions) if num_transactions > 0 else 0

    # --- Calculate Top Selling Items (requires joining) --- 
    # Top Product
    query_top_product = f"""
        SELECT p.name, SUM(ti.net_price) as total_product_sales
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        JOIN products p ON ti.product_id = p.product_id
        WHERE ti.item_type = 'product' AND {where_clause}
        GROUP BY ti.product_id, p.name
        ORDER BY total_product_sales DESC
        LIMIT 1
    """
    top_product_row = db.execute(query_top_product, params).fetchone()
    top_selling_product = top_product_row['name'] if top_product_row else "N/A"
    top_product_sales = top_product_row['total_product_sales'] if top_product_row else 0

    # Top Service
    query_top_service = f"""
        SELECT s.name, SUM(ti.net_price) as total_service_sales -- Or COUNT(ti.item_id) for quantity
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        JOIN services s ON ti.service_id = s.service_id
        WHERE ti.item_type = 'service' AND {where_clause}
        GROUP BY ti.service_id, s.name
        ORDER BY total_service_sales DESC
        LIMIT 1
    """
    top_service_row = db.execute(query_top_service, params).fetchone()
    top_selling_service = top_service_row['name'] if top_service_row else "N/A"
    top_service_sales = top_service_row['total_service_sales'] if top_service_row else 0


    # --- Calculate New Customers --- 
    # Count distinct customers whose *creation* time falls within the filter period
    # We need to parse dates here specifically for the customer query
    new_cust_params = []
    new_cust_where_clauses = []

    start_datetime_cust = None
    end_datetime_cust = None
    if start_date_str:
        try: 
            start_datetime_cust = datetime.strptime(start_date_str + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        except ValueError: pass
    if end_date_str:
        try: 
            end_datetime_cust = datetime.strptime(end_date_str + " 23:59:59", '%Y-%m-%d %H:%M:%S')
        except ValueError: pass

    if start_datetime_cust and end_datetime_cust:
        new_cust_where_clauses.append("c.created_at BETWEEN ? AND ?")
        new_cust_params.extend([start_datetime_cust, end_datetime_cust])
    elif start_datetime_cust:
        new_cust_where_clauses.append("c.created_at >= ?")
        new_cust_params.append(start_datetime_cust)
    elif end_datetime_cust:
        new_cust_where_clauses.append("c.created_at <= ?")
        new_cust_params.append(end_datetime_cust)
    else: # If no date filter, maybe default to Q1 or handle as needed?
          # For now, let's assume no date filter means all time for new customers count
          # Or default to Q1 2024 for consistency with other mocks?
          # Let's default to Q1 2024 if no dates provided for this KPI
          q1_start = datetime(2024, 1, 1, 0, 0, 0)
          q1_end = datetime(2024, 3, 31, 23, 59, 59)
          new_cust_where_clauses.append("c.created_at BETWEEN ? AND ?")
          new_cust_params.extend([q1_start, q1_end])

    # We also need to consider the location filter - a new customer is new *to that location* 
    # if their first transaction at that location falls in the period.
    # OR simply: count customers created in period who had *any* transaction matching filters?
    # Let's use the second, simpler definition for now: Customer created in period AND had a transaction matching filters.
    if location_id:
        new_cust_where_clauses.append("t.location_id = ?")
        new_cust_params.append(location_id)
    
    new_cust_where_clause = " AND ".join(new_cust_where_clauses)

    query_new_cust = f"""
        SELECT COUNT(DISTINCT t.customer_id)
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE {new_cust_where_clause}
    """
    new_cust_row = db.execute(query_new_cust, new_cust_params).fetchone()
    new_customers = new_cust_row[0] if new_cust_row else 0

    # --- Calculate Booking Conversion Rate --- 
    # Rate = Completed / (Completed + Cancelled + No Show)
    # Uses appointment_time for filtering, not booking_time
    booking_where_clause, booking_params = _build_filter_clause(location_id, start_date_str, end_date_str, date_column='appointment_time')
    
    query_booking_stats = f"""
        SELECT 
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status IN ('Completed', 'Cancelled', 'No Show') THEN 1 ELSE 0 END) as total_relevant
        FROM bookings t -- Alias as t to match _build_filter_clause expectations
        WHERE {booking_where_clause}
    """
    booking_stats_row = db.execute(query_booking_stats, booking_params).fetchone()
    
    completed_bookings = booking_stats_row['completed'] if booking_stats_row and booking_stats_row['completed'] else 0
    total_relevant_bookings = booking_stats_row['total_relevant'] if booking_stats_row and booking_stats_row['total_relevant'] else 0
    
    booking_conversion_rate = (completed_bookings / total_relevant_bookings) if total_relevant_bookings > 0 else 0.0

    # Placeholders for KPIs not yet implemented
    # booking_conversion_rate = 0.0 # Requires booking data -- Now implemented

    kpis = {
        "total_net_sales": round(total_net_sales, 2),
        "avg_transaction_value": round(avg_transaction_value, 2),
        "new_customers_qtd": new_customers, # Placeholder
        "booking_conversion_rate": booking_conversion_rate, # Placeholder
        "top_selling_service": top_selling_service,
        "top_selling_service_value": round(top_service_sales, 2),
        "top_selling_product": top_selling_product,
        "top_selling_product_value": round(top_product_sales, 2),
        "calculation_note": f"Based on simulated transaction data. Filters Applied: Location={location_id or 'All'}, Start={start_date_str or 'N/A'}, End={end_date_str or 'N/A'}"
    }
    return jsonify(kpis)

@app.route('/api/v1/sales/summary', methods=['GET'])
@login_required
def get_sales_summary():
    """Placeholder endpoint to return basic sales summary.
       TODO: Implement actual data loading and analysis from DB.
    """
    # Existing placeholder data - replace with actual analysis from CSV/DB
    summary_data = {
        "total_sales_all_locations": 636915.73, # From initial CSV inspection
        "locations": [
            {
                "name": "Napa",
                "total_sales": 112111.66, # From basic analysis
                "top_product_sales": "Semaglutide x3 Month Supply",
                "top_product_quantity": "Dysport"
            },
            {
                "name": "Vacaville",
                "total_sales": 524804.07, # From basic analysis
                "top_product_sales": "Botox",
                "top_product_quantity": "Dysport"
            }
        ],
        "data_source": "Aggregated Quarterly CSV (Product Sales.csv)",
        "limitations": "Data lacks timestamps and transaction IDs. Predictive modeling not yet implemented."
    }
    return jsonify(summary_data)

@app.route('/api/v1/sales/by_category', methods=['GET'])
@login_required
def get_sales_by_category():
    """Retrieves net sales broken down by treatment category from database."""
    db = get_db()
    location_id = request.args.get('location_id', default=None, type=int)
    start_date_str = request.args.get('start_date', default=None, type=str)
    end_date_str = request.args.get('end_date', default=None, type=str)

    where_clause, params = _build_filter_clause(location_id, start_date_str, end_date_str)

    # Query to get sales per category
    query = f"""
        SELECT 
            tc.name, 
            SUM(ti.net_price) as value
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        -- Join based on item type to get category
        LEFT JOIN services s ON ti.service_id = s.service_id AND ti.item_type = 'service'
        LEFT JOIN products p ON ti.product_id = p.product_id AND ti.item_type = 'product'
        LEFT JOIN treatment_categories tc ON tc.category_id = COALESCE(s.category_id, p.category_id)
        WHERE ({where_clause}) AND tc.name IS NOT NULL -- Ensure item has a category
        GROUP BY tc.category_id, tc.name
        ORDER BY tc.name
    """
    
    sales_data = db.execute(query, params).fetchall()

    # Get all category names to ensure all are represented, even with 0 sales
    all_categories_cursor = db.execute('SELECT name FROM treatment_categories ORDER BY name')
    all_category_names = {row['name'] for row in all_categories_cursor.fetchall()}
    
    sales_by_cat_dict = {row['name']: round(row['value'], 2) for row in sales_data}
    
    # Build final result including categories with zero sales
    result = [
        {"name": cat_name, "value": sales_by_cat_dict.get(cat_name, 0.0)}
        for cat_name in sorted(list(all_category_names))
    ]
    
    return jsonify(result)

@app.route('/api/v1/sales/over_time', methods=['GET'])
@login_required
def get_sales_over_time():
    """Retrieves net sales aggregated by date from database."""
    db = get_db()
    location_id = request.args.get('location_id', default=None, type=int)
    start_date_str = request.args.get('start_date', default=None, type=str)
    end_date_str = request.args.get('end_date', default=None, type=str)

    where_clause, params = _build_filter_clause(location_id, start_date_str, end_date_str)

    # Query to get sales per day
    # Using DATE() function for grouping in SQLite
    query = f"""
        SELECT 
            DATE(t.transaction_time) as date,
            SUM(t.total_amount) as sales
        FROM transactions t
        WHERE {where_clause}
        GROUP BY DATE(t.transaction_time)
        ORDER BY DATE(t.transaction_time)
    """
    
    sales_data = db.execute(query, params).fetchall()
    
    result = [dict(row) for row in sales_data]
    
    # TODO (Optional): Fill in missing dates with 0 sales if required by frontend chart
    # This can be complex in pure SQL (especially SQLite) or handled in Python
    
    return jsonify(result)

@app.route('/api/v1/sales/forecast', methods=['GET'])
@login_required
def get_sales_forecast():
    """Generates a sales forecast using SARIMA based on historical simulated data."""
    db = get_db()
    location_id = request.args.get('location_id', default=None, type=int)
    start_date_str = request.args.get('start_date', default=None, type=str)
    end_date_str = request.args.get('end_date', default=None, type=str)
    forecast_days = request.args.get('days', default=30, type=int) # How many days to forecast

    # Use the same filter logic as /sales/over_time to get historical data
    where_clause, params = _build_filter_clause(location_id, start_date_str, end_date_str)

    query = f"""
        SELECT 
            DATE(t.transaction_time) as date,
            SUM(t.total_amount) as sales
        FROM transactions t
        WHERE {where_clause}
        GROUP BY DATE(t.transaction_time)
        ORDER BY DATE(t.transaction_time)
    """
    
    try:
        sales_data_cursor = db.execute(query, params)
        sales_data = sales_data_cursor.fetchall()
        
        if not sales_data:
            return jsonify({"error": "No historical data found for the selected filters.", "historical": [], "forecast": []}), 404
            
        # Convert to pandas DataFrame
        df = pd.DataFrame(sales_data, columns=['date', 'sales'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Ensure daily frequency, fill missing values (e.g., with 0 or forward fill)
        # Determine the date range from the query results
        min_date = df.index.min()
        max_date = df.index.max()
        if pd.isna(min_date) or pd.isna(max_date):
             raise ValueError("Could not determine date range from data.")

        all_days = pd.date_range(start=min_date, end=max_date, freq='D') 
        df = df.reindex(all_days).fillna(0) # Fill non-transaction days with 0 sales
        
        # Basic data check for forecasting
        if len(df) < 14: # Need sufficient data for weekly seasonality
            return jsonify({"error": "Insufficient historical data for forecasting (need at least 14 days).", "historical": df.reset_index().to_dict('records'), "forecast": []}), 400

        # --- Fit SARIMA Model --- 
        # Parameters (p,d,q)(P,D,Q,m) - These are common defaults, might need tuning
        # (1,1,1) for non-seasonal part
        # (1,1,0,7) for seasonal part (m=7 for weekly seasonality)
        # Use simple_differencing=False for potentially better convergence with some data
        try:
            model = SARIMAX(df['sales'], 
                            order=(1, 1, 1),
                            seasonal_order=(1, 1, 0, 7),
                            enforce_stationarity=False,
                            enforce_invertibility=False,
                            simple_differencing=False)
            results = model.fit(disp=False) # disp=False suppresses convergence output
        except Exception as model_ex:
             print(f"SARIMA fitting error: {model_ex}")
             # Fallback to simpler model? Or just return error?
             # For now, return error
             return jsonify({"error": f"Failed to fit forecasting model: {model_ex}", "historical": df.reset_index().to_dict('records'), "forecast": []}), 500

        # --- Generate Forecast --- 
        forecast_result = results.get_forecast(steps=forecast_days)
        forecast_df = forecast_result.summary_frame(alpha=0.05) # 95% confidence interval
        forecast_df.index.name = 'date' # Rename index
        
        # Prepare output
        historical_output = df.reset_index().rename(columns={'index': 'date'}).to_dict('records')
        forecast_output = forecast_df.reset_index().rename(columns={'index': 'date'}).to_dict('records')

        # Ensure date format is string YYYY-MM-DD for JSON
        for row in historical_output:
            row['date'] = row['date'].strftime('%Y-%m-%d')
        for row in forecast_output:
            row['date'] = row['date'].strftime('%Y-%m-%d')
            
        return jsonify({
            "historical": historical_output,
            "forecast": forecast_output,
            "note": "Forecast is illustrative, based on SARIMA model fitted to simulated data."
        })

    except Exception as e:
        print(f"Error during forecasting: {e}") # Log the error server-side
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

# --- Utility Endpoints ---

@app.route('/api/v1/locations', methods=['GET'])
@login_required
def get_locations():
    """Retrieves list of available locations from the database, including total sales."""
    db = get_db()
    # Query to get locations and their total sales
    query = """
        SELECT 
            l.location_id, 
            l.name, 
            l.address, 
            l.latitude, 
            l.longitude,
            COALESCE(SUM(t.total_amount), 0) as total_sales
        FROM locations l
        LEFT JOIN transactions t ON l.location_id = t.location_id
        GROUP BY l.location_id, l.name, l.address, l.latitude, l.longitude
        ORDER BY l.name
    """
    locations_cursor = db.execute(query)
    locations = [dict(row) for row in locations_cursor.fetchall()]
    return jsonify(locations)

@app.route('/api/v1/treatment_categories', methods=['GET'])
@login_required
def get_treatment_categories():
    """Retrieves list of treatment categories from the database."""
    db = get_db()
    categories_cursor = db.execute('SELECT category_id, name, description FROM treatment_categories ORDER BY name')
    categories = [dict(row) for row in categories_cursor.fetchall()]
    return jsonify(categories)
    # OLD MOCK: return jsonify(MOCK_TREATMENT_CATEGORIES)

@app.route('/api/v1/services', methods=['GET'])
@login_required
def get_services():
    """Retrieves list of services from the database (optionally filter by category)."""
    db = get_db()
    category_id = request.args.get('category_id', type=int)

    query = 'SELECT service_id, category_id, name, standard_price FROM services'
    params = []
    if category_id:
        query += ' WHERE category_id = ?'
        params.append(category_id)
    query += ' ORDER BY name'

    services_cursor = db.execute(query, params)
    services = [dict(row) for row in services_cursor.fetchall()]
    return jsonify(services)
    # OLD MOCK:
    # if category_id:
    #     filtered_services = [s for s in MOCK_SERVICES if s['category_id'] == category_id]
    #     return jsonify(filtered_services)
    # else:
    #     return jsonify(MOCK_SERVICES)

@app.route('/api/v1/products', methods=['GET'])
@login_required
def get_products():
    """Retrieves list of products from the database."""
    db = get_db()
    products_cursor = db.execute('SELECT product_id, name, sku, retail_price, category_id FROM products ORDER BY name')
    products = [dict(row) for row in products_cursor.fetchall()]
    return jsonify(products)
    # OLD MOCK: return jsonify(MOCK_PRODUCTS)

@app.route('/api/v1/employees', methods=['GET'])
@login_required
def get_employees():
    """Retrieves list of active employees from the database (optionally filter by location)."""
    db = get_db()
    location_id = request.args.get('location_id', type=int)

    query = 'SELECT employee_id, first_name, last_name, role, location_id FROM employees WHERE is_active = 1' # Only fetch active employees
    params = []
    if location_id:
        query += ' AND location_id = ?'
        params.append(location_id)
    query += ' ORDER BY last_name, first_name'

    employees_cursor = db.execute(query, params)
    employees = [dict(row) for row in employees_cursor.fetchall()]
    return jsonify(employees)
    # OLD MOCK:
    # if location_id:
    #     filtered_employees = [e for e in MOCK_EMPLOYEES if e['location_id'] == location_id]
    #     return jsonify(filtered_employees)
    # else:
    #     return jsonify(MOCK_EMPLOYEES)

# New endpoint to fetch customer coordinates
@app.route('/api/v1/customers/locations', methods=['GET'])
@login_required
def get_customer_locations():
    """Retrieves latitude and longitude for all customers.
       NOTE: Currently uses simulated coordinates from seeding.
             Future implementation may involve fetching real addresses 
             and potentially geocoding them (consider performance/cost).
    """
    db = get_db()
    try:
        # Fetch only customers with valid coordinates
        cursor = db.execute(
            "SELECT longitude, latitude FROM customers WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        )
        # Return as a list of [longitude, latitude] pairs, suitable for HexagonLayer
        customer_coords = [ [row['longitude'], row['latitude']] for row in cursor.fetchall() ]
        return jsonify(customer_coords)
    except Exception as e:
        print(f"Error fetching customer locations: {e}")
        return jsonify({"error": "Failed to retrieve customer location data."}), 500

# Add more specific data endpoints here later (e.g., /api/v1/sales/over_time)

# --- Configuration for Uploads ---
# Define allowed file extensions (optional but good practice)
ALLOWED_EXTENSIONS = {'csv'}
# Define required columns for transaction upload validation
REQUIRED_TRANSACTION_COLUMNS = [
    'transaction_time', 
    'location_name', 
    'item_type', 
    'item_identifier', 
    'quantity', 
    'net_price'
    # Add optional columns like 'customer_id', 'employee_id' if needed for validation stage
]

# Helper function to check allowed extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Data Upload Endpoints ---

@app.route('/api/v1/data/upload/validate_transactions', methods=['POST'])
@login_required
def validate_transaction_upload():
    """Validates an uploaded transaction CSV file structure."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        # filename = secure_filename(file.filename) # Use if saving file
        try:
            # Read CSV using pandas - handle potential parsing errors
            df = pd.read_csv(file.stream)
            
            # Validate columns
            missing_cols = [col for col in REQUIRED_TRANSACTION_COLUMNS if col not in df.columns]
            extra_cols = [col for col in df.columns if col not in REQUIRED_TRANSACTION_COLUMNS] # Optional info
            
            if missing_cols:
                return jsonify({
                    "validation_status": "error",
                    "message": f"Missing required columns: {', '.join(missing_cols)}",
                    "required_columns": REQUIRED_TRANSACTION_COLUMNS,
                    "found_columns": list(df.columns)
                }), 400
            else:
                # Basic structure is valid
                return jsonify({
                    "validation_status": "success",
                    "message": f"File structure validated successfully. Found {len(df)} rows.",
                    "required_columns": REQUIRED_TRANSACTION_COLUMNS,
                    "found_columns": list(df.columns)
                    # "extra_columns_found": extra_cols # Optional
                }), 200
                
        except pd.errors.EmptyDataError:
             return jsonify({"validation_status": "error", "message": "Uploaded file is empty."}), 400
        except pd.errors.ParserError:
             return jsonify({"validation_status": "error", "message": "Failed to parse CSV file. Ensure it is a valid CSV."}), 400
        except Exception as e:
            print(f"Error processing uploaded file: {e}")
            return jsonify({"validation_status": "error", "message": f"An unexpected error occurred during validation: {e}"}), 500
            
    else:
        return jsonify({"error": "Invalid file type. Only CSV files are allowed."}), 400

@app.route('/api/v1/data/upload/process_transactions', methods=['POST'])
@login_required
def process_transaction_upload():
    """Processes a validated transaction CSV: Clears old data and inserts new."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or missing file"}), 400
        
    db = get_db()
    cursor = db.cursor()

    try:
        df = pd.read_csv(file.stream)
        
        # Re-validate columns just in case
        missing_cols = [col for col in REQUIRED_TRANSACTION_COLUMNS if col not in df.columns]
        if missing_cols:
            return jsonify({"status": "error", "message": f"Processing failed: Missing required columns: {', '.join(missing_cols)}"}), 400

        # --- Pre-fetch necessary data for mapping --- 
        locations_map = {row['name']: row['location_id'] for row in cursor.execute("SELECT location_id, name FROM locations").fetchall()}
        # Assuming item_identifier is SKU for product, Name for service
        products_map = {row['sku']: {'id': row['product_id'], 'price': row['retail_price']} for row in cursor.execute("SELECT product_id, sku, retail_price FROM products WHERE sku IS NOT NULL").fetchall()}
        services_map = {row['name']: {'id': row['service_id'], 'price': row['standard_price']} for row in cursor.execute("SELECT service_id, name, standard_price FROM services").fetchall()}
        # Optional: Fetch customer/employee IDs if present in CSV for mapping
        # customers_map = {str(row['customer_id']): row['customer_id'] for row in cursor.execute("SELECT customer_id FROM customers").fetchall()}
        # employees_map = {str(row['employee_id']): row['employee_id'] for row in cursor.execute("SELECT employee_id FROM employees").fetchall()}

        # --- Clear existing transaction data --- 
        # ** CRITICAL & DESTRUCTIVE STEP **
        print("Clearing existing transaction data...")
        cursor.execute("DELETE FROM transaction_items")
        cursor.execute("DELETE FROM transactions")
        # Optionally clear bookings/customers if they are derived solely from transactions?
        # For now, only clearing transaction data.
        print("Existing transaction data cleared.")

        # --- Process and Insert New Data --- 
        inserted_transactions = 0
        inserted_items = 0
        errors = []

        print(f"Processing {len(df)} rows from uploaded file...")
        # Group by potential transaction (e.g., same time, location, customer?) - Difficult without a Transaction ID in source
        # Assuming each row is a distinct line item belonging to a potentially new transaction for simplicity now.
        # A more robust solution would require a transaction identifier in the CSV.
        
        # For now: Treat each row as a potential line item and create a transaction for it.
        # This is NOT ideal but works as a basic import. 
        for index, row in df.iterrows():
            try:
                # 1. Validate/Map required fields
                loc_name = row['location_name']
                loc_id = locations_map.get(loc_name)
                if not loc_id:
                    errors.append(f"Row {index+2}: Unknown location_name '{loc_name}'")
                    continue
                    
                try:
                    trans_time = pd.to_datetime(row['transaction_time']).to_pydatetime()
                except Exception:
                    errors.append(f"Row {index+2}: Invalid transaction_time format '{row['transaction_time']}'")
                    continue

                item_type = str(row['item_type']).lower()
                item_id_str = str(row['item_identifier'])
                product_id = None
                service_id = None
                unit_price_db = 0 # Get price from DB for consistency if needed
                
                if item_type == 'product':
                    product_info = products_map.get(item_id_str)
                    if not product_info:
                        errors.append(f"Row {index+2}: Unknown product SKU '{item_id_str}'")
                        continue
                    product_id = product_info['id']
                    unit_price_db = product_info['price']
                elif item_type == 'service':
                    service_info = services_map.get(item_id_str)
                    if not service_info:
                        # Try case-insensitive match as fallback?
                         service_info = next((v for k, v in services_map.items() if k.lower() == item_id_str.lower()), None)
                         if not service_info:
                             errors.append(f"Row {index+2}: Unknown service name '{item_id_str}'")
                             continue
                    service_id = service_info['id']
                    unit_price_db = service_info['price']
                else:
                    errors.append(f"Row {index+2}: Invalid item_type '{item_type}'")
                    continue

                try:
                    quantity = int(row['quantity'])
                    net_price = float(row['net_price'])
                    # Optional: Validate net_price against unit_price * quantity?
                except ValueError as ve:
                     errors.append(f"Row {index+2}: Invalid quantity or net_price ({ve})")
                     continue
                     
                # Optional: Map customer/employee IDs here if included
                customer_id = None # Placeholder - Add logic if customer_id in CSV
                employee_id = None # Placeholder - Add logic if employee_id in CSV

                # 2. Create Transaction Header (Simplified: one per item)
                # In reality, group items into transactions first.
                # For this simple import, create transaction then item.
                transaction_total = net_price # Since we treat each line as a transaction
                cursor.execute(
                    "INSERT INTO transactions (customer_id, employee_id, location_id, transaction_time, total_amount) VALUES (?, ?, ?, ?, ?)",
                    (customer_id, employee_id, loc_id, trans_time, transaction_total)
                )
                transaction_id = cursor.lastrowid
                inserted_transactions += 1
                
                # 3. Insert Transaction Item
                cursor.execute(
                    "INSERT INTO transaction_items (transaction_id, item_type, product_id, service_id, quantity, unit_price, net_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (transaction_id, item_type, product_id, service_id, quantity, (net_price / quantity if quantity else 0), net_price) # Calculate unit price
                )
                inserted_items += 1

            except Exception as row_error:
                errors.append(f"Row {index+2}: Unexpected error - {row_error}")
                # Decide whether to continue or stop processing
                # continue

        # --- Finalize --- 
        if errors:
            # If there were errors, rollback changes and report
            db.rollback()
            print(f"Processing finished with {len(errors)} errors. Database rolled back.")
            error_summary = "\n".join(errors[:20]) # Show first 20 errors
            if len(errors) > 20:
                 error_summary += f"\n... and {len(errors) - 20} more errors."
            return jsonify({
                "status": "error", 
                "message": f"Processing failed due to {len(errors)} errors. Database changes rolled back.",
                "errors": error_summary
                }), 400
        else:
            # Commit changes if no errors
            db.commit()
            print(f"Processing successful. Inserted {inserted_transactions} transactions and {inserted_items} items.")
            return jsonify({
                "status": "success", 
                "message": f"Successfully processed file. Inserted {inserted_transactions} transactions and {inserted_items} items."
                }), 200

    except Exception as e:
        db.rollback() # Rollback on any unexpected error during processing
        print(f"Error processing uploaded file: {e}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred during processing: {e}"}), 500

# --- Helper function to get item name mapping ---
def _get_item_name_map(db):
    item_map = {}
    # Fetch products with SKU or Name
    products = db.execute("SELECT product_id, COALESCE(sku, name) as identifier FROM products WHERE identifier IS NOT NULL").fetchall()
    for p in products:
        item_map[f"P_{p['product_id']}"] = p['identifier'] # Prefix to distinguish type
    # Fetch services by Name
    services = db.execute("SELECT service_id, name FROM services").fetchall()
    for s in services:
        item_map[f"S_{s['service_id']}"] = s['name'] # Prefix to distinguish type
    return item_map

# --- DEBUG ROUTE --- (Temporary)
# @app.route('/debug/list_routes')
# def list_routes():
#    import urllib
#    output = []
#    for rule in app.url_map.iter_rules():
#        # Filter out static routes and internal Werkzeug routes
#        if "static" not in rule.endpoint and "_debug_toolbar" not in rule.endpoint:
#             methods = ','.join(sorted(list(rule.methods)))
#             line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, str(rule)))
#             output.append(line)
#    output.sort()
#    # Return as JSON for easier parsing if needed, or plain text
#    # return "<pre>" + "\n".join(output) + "</pre>"
#    return jsonify({"registered_routes": output})
# --- END DEBUG ROUTE ---

# --- Auth Functions & Routes ---
# Replace with DB check later
# HARDCODED_USERNAME = 'admin'
# HARDCODED_PASSWORD = 'password'

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    print(f"--- LOGIN ATTEMPT ---") # DEBUG
    print(f"Received Username: {username}") # DEBUG
    print(f"Received Password: {password is not None}") # DEBUG - Just check if password exists, don't print it

    if not username or not password:
        print("Login Error: Missing username or password") # DEBUG
        return jsonify({"message": "Username and password required"}), 400

    db = get_db()
    user_data = db.execute(
        'SELECT user_id, username, password_hash FROM users WHERE username = ?',
        (username,)
    ).fetchone()
    
    print(f"DB User Data Found: {dict(user_data) if user_data else None}") # DEBUG

    if user_data:
        password_match = check_password_hash(user_data['password_hash'], password)
        print(f"Password Check Result: {password_match}") # DEBUG
        if password_match:
            # Password matches
            user = User(id=user_data['user_id'], username=user_data['username']) 
            login_user(user) # Use Flask-Login function
            print(f"Login Success for user: {username}") # DEBUG
            return jsonify({"success": True, "message": "Login successful"}), 200
        else:
            # Invalid password
            print(f"Login Error: Invalid password for user: {username}") # DEBUG
            return jsonify({"message": "Invalid username or password"}), 401
    else:
        # Invalid username
        print(f"Login Error: User not found: {username}") # DEBUG
        return jsonify({"message": "Invalid username or password"}), 401

@app.route('/api/v1/auth/logout', methods=['POST'])
# @login_required # Protect logout route - REMOVED as @login_required decorator uses flask_login one
def logout():
    logout_user() # Use Flask-Login function
    # session.clear() # logout_user handles session
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

@app.route('/api/v1/auth/status', methods=['GET'])
def auth_status():
    # Use Flask-Login's current_user
    if current_user.is_authenticated:
    # if 'user_id' in session: # Old method
        return jsonify({"isLoggedIn": True, "user_id": current_user.get_id()}), 200
        # return jsonify({"isLoggedIn": True, "user_id": session['user_id']}), 200 # Old method
    else:
        return jsonify({"isLoggedIn": False}), 200

# --- NEW: Profit Calculation Endpoint ---
@app.route('/api/v1/profit/by_category', methods=['GET'])
@login_required
def get_profit_by_category():
    """Calculates total profit (revenue - cost) for each service category."""
    db = get_db()
    filters = {
        'location_id': request.args.get('location_id'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date')
    }

    # Build the query to calculate profit per category
    query = """
        SELECT 
            tc.name, 
            tc.category_id,
            SUM(ti.net_price) as total_revenue,
            SUM(COALESCE(s.standard_cost, 0) * ti.quantity) as total_cost,
            SUM(ti.net_price - (COALESCE(s.standard_cost, 0) * ti.quantity)) as total_profit
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        JOIN services s ON ti.service_id = s.service_id
        JOIN treatment_categories tc ON s.category_id = tc.category_id
        WHERE ti.item_type = 'service' -- Only consider services for this calculation
    """
    params = []

    # Add filters
    if filters['location_id'] and filters['location_id'] != 'all':
        query += " AND t.location_id = ?"
        params.append(filters['location_id'])
    if filters['start_date']:
        query += " AND t.transaction_time >= ?"
        params.append(filters['start_date'] + ' 00:00:00') # Start of day
    if filters['end_date']:
        query += " AND t.transaction_time <= ?"
        params.append(filters['end_date'] + ' 23:59:59') # End of day

    query += " GROUP BY tc.category_id, tc.name ORDER BY total_profit DESC"

    try:
        cursor = db.execute(query, params)
        # Prepare data in the format expected by the pie chart: { name: 'X', profit: Y }
        profit_data = [
            {'name': row['name'], 'profit': round(row['total_profit'] or 0, 2)} 
            for row in cursor.fetchall()
        ]
        return jsonify(profit_data)
    except sqlite3.Error as e:
        print(f"Error fetching profit by category: {e}")
        return jsonify({"error": "Failed to calculate profit data"}), 500
# --- End Profit Endpoint ---

# --- NEW: Add Command to Test Boulevard Connection --- 
@click.command('test-boulevard')
@with_appcontext
def test_boulevard_command():
    """Tests connection to Boulevard API by fetching locations."""
    click.echo("Attempting to connect to Boulevard API...")
    locations_data = boulevard_client.get_boulevard_locations()
    
    if locations_data:
        click.echo("Successfully connected and fetched data:")
        # Print the first few items or summary
        if isinstance(locations_data, list):
            click.echo(f"Found {len(locations_data)} items. First item:")
            if locations_data:
                click.echo(locations_data[0]) # Print first item as example
            else:
                click.echo("Response was an empty list.")
        else:
             click.echo(locations_data) # Print whatever was returned
    else:
        click.echo("Failed to fetch data from Boulevard. Check logs for errors.")

app.cli.add_command(test_boulevard_command)
if __name__ == '__main__':
    # Note: Use a production WSGI server like Gunicorn or Waitress for deployment
    # app.run(debug=True, host='0.0.0.0', port=5001) # Ensure correct port if running directly
    pass # Typically run via 'flask run' which handles port/host 