import os # Import os
from dotenv import load_dotenv # Keep load_dotenv import here
import csv
import difflib

# Load environment variables from .env file FIRST
# Construct path relative to this file (app.py)
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '..', '.env')
load_dotenv(dotenv_path=dotenv_path) # Use explicit path

# Now import other things
from flask import Flask, jsonify, request, g, session, send_from_directory # Add session and send_from_directory
from flask_cors import CORS # Import CORS
import random
import sqlite3 # Import sqlite3
import click # Import click for CLI commands
from flask.cli import with_appcontext # Import for CLI commands
from datetime import date, timedelta, datetime, timezone
import pandas as pd # Placeholder for future data loading
from statsmodels.tsa.statespace.sarimax import SARIMAX
from werkzeug.utils import secure_filename # For file uploads
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from prophet import Prophet # Import Prophet
from dateutil.parser import isoparse # For parsing ISO 8601 dates
from collections import defaultdict
from backend.extensions import cache# Import cache object from extensions
import logging
from functools import wraps
from flask_caching import Cache

# Import the boulevard client functions
from . import boulevard_client
from backend.database import get_db
from backend.constants import BOULEVARD_CATEGORY_MAPPING

app = Flask(__name__, instance_relative_config=True) # Enable instance folder
CORS(app, 
    resources={r"/api/*": {
        "origins": [
            "http://localhost:5173",  # Vite default port
            "http://localhost:5174",  # Vite alternate port
            "http://localhost:3000",  # React default port (if needed)
            os.getenv('FRONTEND_URL', '')  # Production URL if defined
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }},
    supports_credentials=True
)
# --- End CORS Configuration ---

# Ensure all responses include CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# --- Flask App Configuration (Secrets, Session, etc.) ---
# Load environment variables (ensure this happens before config use)
basedir = os.path.abspath(os.path.dirname(__file__))
# dotenv_path = os.path.join(basedir, '..', '.env') # OLD: Looked in parent directory
dotenv_path = os.path.join(basedir, '.env') # NEW: Look in current directory (backend/)
load_dotenv(dotenv_path=dotenv_path)

app.config.from_mapping(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev'), # Get secret key from env or use default
    # SESSION_TYPE = 'filesystem' # Example if using Flask-Session
)

# Optional: Load further config from instance folder (e.g., instance/config.py)
# app.config.from_pyfile('config.py', silent=True)

# --- Session Configuration ---
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production' # True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Can be 'Strict' or 'None' (if using cross-site requests with HTTPS)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1) # Session lifetime
# --- End Session Configuration ---

# --- Caching Configuration --- 
app.config['CACHE_TYPE'] = 'SimpleCache'  # Use simple in-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300 # Default cache timeout 5 minutes (300 seconds)
# cache = Cache(app) # REMOVE direct instantiation
cache.init_app(app) # Initialize cache using the object from extensions
# --- End Caching Configuration ---

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# --- End Logging Configuration ---

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
# --- Helper Function for Currency Cleaning ---
def clean_currency(value):
    """Removes $, commas, and handles parentheses for negative numbers."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return value # Already numeric
    value = str(value).strip().replace('$', '').replace(',', '')
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    try:
        return float(value)
    except ValueError:
        return None # Return None if conversion fails

# ... (Place this function definition before the data loading functions)


# --- Placeholder Category Mapping ---
# TODO: Review and expand this mapping with actual service/product names from Boulevard
BOULEVARD_CATEGORY_MAPPING = {
    # Injectables (Services)
    "Botox / Dysport": "Injectables",
    "Dermal Fillers": "Injectables",
    "Kybella": "Injectables",
    "Botox/Dysport Return Clients": "Injectables",
    "NEW PATIENT BOTOX/DYSPORT": "Injectables",
    "Botox & Filler": "Injectables", # Added
    "Filler": "Injectables", # Added
    "Sculptra": "Injectables", # Added
    # Injectables (Products)
    "Botox": "Injectables",
    "Dysport": "Injectables",
    "Juvederm Ultra XC": "Injectables",
    "Juvederm Voluma XC": "Injectables",
    "Juvederm Vollure XC": "Injectables",
    "Restylane Contour": "Injectables",
    "Juvederm Ultra Plus 1ML": "Injectables", # Added
    "Juvederm Ultra XC .55mL": "Injectables", # Added
    "Juvederm Volbella XC": "Injectables", # Added
    "Juvederm Volux XC": "Injectables", # Added
    "Restylane Defyne": "Injectables", # Added
    "Restylane Eyelight": "Injectables", # Added
    "Restylane Kysse": "Injectables", # Added
    "Restylane L": "Injectables", # Added
    "Restylane Lyft": "Injectables", # Added
    "Restylane Refyne": "Injectables", # Added
    "PRP Injection": "Injectables", # Added (Likely for face/joints)
    # Facials
    "Signature Hydrafacial": "Facials",
    "Platinum Hydrafacial": "Facials",
    "Deluxe Hydrafacial": "Facials",
    "Microdermabrasion Basic Facial": "Facials",
    "Acne Facial": "Facials", # Added
    "Anti Aging Facial": "Facials", # Added
    "C02 Mask": "Facials", # Added (Assuming service, could be retail)
    "Dermaplaning Add On": "Facials", # Added
    "Express Facial": "Facials", # Added
    "Hands Hydrafacial": "Facials", # Added
    "Hydrafacial Special": "Facials", # Added
    "MicroPeel Sensitive": "Facials", # Added
    "Microdermabrasion Deluxe Facial": "Facials", # Added
    "Perk Eye Add-On (HydraFacial)": "Facials", # Added
    "Perk Lip Add-On (HydraFacial)": "Facials", # Added
    "Universal Peel": "Facials", # Added
    "Jelly mask": "Facials", # Added
    "TCA Peel": "Facials", # Added
    "MicroPeel Plus 20": "Facials", # Added
    "Hydrfacial Lip Perk": "Facials", # Added (Corrected typo?)
    "Hydrafacial Perk Eye": "Facials", # Added (Corrected typo?)
    # Laser
    "Laser Hair Removal - Medium Area": "Laser",
    "Laser Hair Removal - Upper/ Lower Face Area Package": "Laser",
    "Laser Hair Removal Large Area - a la carte": "Laser",
    "Erbium Hands Add-On": "Laser",
    "Spider Vein Removal": "Laser",
    "CO2 Skin Resurfacing": "Laser",
    "C02 Skin Resurfacing Special $750": "Laser",
    "C02 Skin Resurfacing Special $997": "Laser",
    "IPL Full Face - Package (3 Treatments)": "Laser",
    "Tattoo Removal": "Laser",
    "Erbium Special": "Laser",
    "Initial Laser Consult": "Laser",
    "C02 Décolleté Add On": "Laser", # Added
    "C02 For You Bundle": "Laser", # Added
    "C02 Neck Add On": "Laser", # Added
    "C02 Skin Resurfacing": "Laser", # Added
    "C02 Special": "Laser", # Added
    "IPL - Full Face": "Laser", # Added
    "IPL Neck Add-On": "Laser", # Added
    "IPL special": "Laser", # Added
    "Laser Hair Removal - Brazilian Area Package": "Laser", # Added
    "Laser Hair Removal - Large Area Package": "Laser", # Added
    "Laser Hair Removal - Medium Area Package": "Laser", # Added
    "Laser Hair Removal - Small Area Package": "Laser", # Added
    "Laser Hair Removal Medium Area - a la carte": "Laser", # Added
    "Laser Hair Removal Small Area - a la carte": "Laser", # Added
    "Skin Resurfacing Full Face - Erbium": "Laser", # Added
    # Skincare/Retail Products
    "Powder Defense": "Retail/Skincare",
    "Tox Membership": "Retail/Membership",
    "Filler 12x Month Membership": "Retail/Membership",
    "Brightening Even Skin Tone Pads": "Retail/Skincare",
    "Hydroquinone Powder": "Retail/Skincare",
    "AHA / BHA Exfoliating Polish": "Retail/Skincare", # Added
    "Aquaglow Hyaluronic Acid": "Retail/Skincare", # Added
    "Blemish + Age Defense": "Retail/Skincare", # Added
    "Bloom Membership": "Retail/Membership", # Added
    "C E Ferulic": "Retail/Skincare", # Added
    "Complexion Gly-Sal Pads": "Retail/Skincare", # Added
    "Discoloration Defense": "Retail/Skincare", # Added
    "Dual Active Phyto GF": "Retail/Skincare", # Added
    "Glycolic 10 Renew Overnight": "Retail/Skincare", # Added
    "Hydrate Membership": "Retail/Membership", # Added
    "Hydrating B5 Gel": "Retail/Skincare", # Added
    "Lipid Cloud": "Retail/Skincare", # Added
    "P-TIOX": "Retail/Skincare", # Added
    "Peptide Neck Cream": "Retail/Skincare", # Added
    "Phyto Balance": "Retail/Skincare", # Added
    "Plump It! SPF 30": "Retail/Skincare", # Added
    "Radiant Glow Lactic Acid": "Retail/Skincare", # Added (Could be service)
    "Sheer Defense": "Retail/Skincare", # Added
    "Silymarin CF": "Retail/Skincare", # Added
    "Simply Clean": "Retail/Skincare", # Added
    "Skincare Kit": "Retail/Skincare", # Added
    "Tinted Defense": "Retail/Skincare", # Added
    "Blemish Corrective Treatment Serum": "Retail/Skincare", # Added
    "Tox and Filler Membership": "Retail/Membership", # Added
    # Wellness/Weight Loss
    "Semaglutide - weekly injection": "Wellness/Weight Loss",
    "Semaglutide - monthly pickup/weigh in": "Wellness/Weight Loss",
    "Tirzepatide - weekly injection": "Wellness/Weight Loss",
    "1st Weight Loss Appt (AFTER CONSULT)": "Wellness/Weight Loss",
    "Semaglutide x1 Month Supply": "Wellness/Weight Loss",
    "Semaglutide x3 Month Supply": "Wellness/Weight Loss",
    "Lipo-C / MIC": "Wellness/Weight Loss",
    "Vitamin D": "Wellness/Weight Loss",
    "B-12 Injection": "Wellness/Weight Loss",
    "Semaglutide/Tirzepatide Phone Consultation": "Wellness/Weight Loss", # Consultation
    "Semaglutide x6 month Supply": "Wellness/Weight Loss", # Added
    "semaglutide single injection": "Wellness/Weight Loss", # Added
    "Tirzepatide 1x Month": "Wellness/Weight Loss", # Added
    "Tirzepatide 3X Months Supply": "Wellness/Weight Loss", # Added
    "Tirzepatide - monthly pickup": "Wellness/Weight Loss", # Added
    "Tirzepatide 1x Single Dose": "Wellness/Weight Loss", # Added
    # Wellness/IV Therapy (NEW CATEGORY)
    "B-Complex": "IV Therapy", # Moved
    "Beauty/Glow Blend": "IV Therapy", # Moved
    "Glutathione": "IV Therapy", # Moved 
    "Hangover Cure": "IV Therapy", # Moved
    "Immunity Blend": "IV Therapy", # Moved
    "Myers' Cocktail": "IV Therapy", # Moved
    "NAD + Therapy": "IV Therapy", # Moved
    "IV Special": "IV Therapy", # Moved from Other Services
    "Migraine/Pain Relief": "IV Therapy", # Added (Assuming IV)
    # Other Services
    "PRP Add-On": "Other Services",
    "RF Microneedling": "Other Services",
    "Hylenex": "Other Services",
    "PRP Hair Restoration": "Other Services",
    "Additional Syringe": "Other Services", # Added
    "Body Tone- Muscle Toning 1x treatment": "Other Services", # Added
    "BodySculpt' Contouring1x treatment": "Other Services", # Added
    "BodyTone Special": "Other Services", # Added
    "Pronox": "Other Services", # Added
    "RF Microneedling Face + Neck Package (3 Treatments)": "Other Services", # Added
    "RF Microneedling Face Package (3 Treatments)": "Other Services", # Added
    "RF Microneedling Full Face Package (3)": "Other Services", # Added
    "Shaving Fee": "Other Services", # Added
    "Skin Stylus Microneedling Package (3 Treatments)": "Other Services", # Added
    "Skin Stylus Neck Add on": "Other Services", # Added
    "Vaginal Rejuvenation": "Other Services", # Added
    # Consults/Followups (Often $0, maybe categorize differently?)
    "Initial Microneedling Consult": "Consultation/Followup",
    "C02- Follow up": "Consultation/Followup",
    "Neurotoxins (Botox/Dysport) /Filler/PRP/Sculptra Follow Up": "Consultation/Followup",
    "Initial Skin Health Consult": "Consultation/Followup",
    "New Patient Consult": "Consultation/Followup",
    "Initial Microneedling Consult": "Consultation/Followup", # Added
    "C02- Follow up": "Consultation/Followup", # Added
    # Membership/Account Adjustments (NEW CATEGORY)
    "Membership fee corrections": "Membership/Account Adjustment",
    "Account Credit Adjustment": "Membership/Account Adjustment",
    "Membership fee corrections": "Membership/Account Adjustment", # Added
    "Account Credit Adjustment": "Membership/Account Adjustment", # Added
    # Default/Uncategorized
    "DEFAULT_CATEGORY": "Uncategorized" # A default for items not in the map
}

# --- Database Configuration ---
# Ensure instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Define database path
DATABASE = os.path.join(app.instance_path, 'rella_analytics.sqlite')

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
    """Initializes the database based on schema.sql and seed_data.sql."""
    db = get_db()
    
    # Execute schema first
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    
    # Generate proper password hash for admin user
    admin_password = 'password'
    password_hash = generate_password_hash(admin_password)
    
    # Insert admin user with proper hash
    db.execute(
        'INSERT INTO users (username, password_hash) VALUES (?, ?)',
        ('admin', password_hash)
    )
    
    # Execute rest of seed data (excluding the admin user since we just created it)
    with app.open_resource('seed_data.sql') as f:
        seed_sql = f.read().decode('utf8')
        # Remove the admin user insert statement from seed data
        seed_sql = '\n'.join([line for line in seed_sql.split('\n') 
                             if not line.strip().startswith('INSERT INTO users')])
        db.executescript(seed_sql)
    
    db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

app.teardown_appcontext(close_db) # Register close_db to be called when app context ends
app.cli.add_command(init_db_command) # Register the init-db command

# --- Other Endpoints --- 
# ... (rest of your app.py file) ...

def _make_cache_key(*args, **kwargs):
    """Generate a cache key that includes query parameters."""
    key = request.path
    args = str(hash(frozenset(request.args.items())))
    return f"{key}|{args}"

@app.route('/api/v1/sales/by_category', methods=['GET'])
@login_required
@cache.cached(timeout=300, key_prefix=_make_cache_key)  # Cache for 5 minutes
def get_sales_by_category():
    """Retrieves sales data broken down by treatment category from Boulevard API."""
    try:
        # Get query parameters
        location_id = request.args.get('location_id', default='all', type=str)
        start_date_str = request.args.get('start_date', default=None, type=str)
        end_date_str = request.args.get('end_date', default=None, type=str)

        # --- Step 1: Get Location IDs to query ---
        target_location_ids = []
        if location_id == 'all':
            locations_response = boulevard_client.get_boulevard_locations()
            if locations_response and 'data' in locations_response and 'locations' in locations_response['data']:
                for edge in locations_response['data']['locations'].get('edges', []):
                    if edge and 'node' in edge and 'id' in edge['node']:
                        target_location_ids.append(edge['node']['id'])
            if not target_location_ids:
                print("Warning: Could not fetch location IDs for category breakdown.")
                return jsonify({"error": "Could not fetch location IDs."}), 500
        else:
            target_location_ids.append(location_id)

        # --- Step 2: Fetch Sales Data and Aggregate by Category ---
        sales_by_category = defaultdict(float)
        
        for loc_id in target_location_ids:
            # Use the Boulevard client to get sales data
            location_orders = boulevard_client.get_boulevard_kpi_data(
                location_id=loc_id,
                query_string=f"closedAt>={start_date_str}" if start_date_str else None
            )
            
            if not location_orders:
                continue

            for order in location_orders:
                if 'lineGroups' not in order:
                    continue

                for group in order['lineGroups']:
                    if 'lines' not in group:
                        continue

                    for line in group['lines']:
                        item_name = line.get('name')
                        if not item_name:
                            continue

                        # Get category from mapping
                        category = BOULEVARD_CATEGORY_MAPPING.get(
                            item_name, 
                            BOULEVARD_CATEGORY_MAPPING.get("DEFAULT_CATEGORY", "Uncategorized")
                        )

                        # Add sales amount to category
                        subtotal_cents = line.get('currentSubtotal', 0)
                        if isinstance(subtotal_cents, (int, float)):
                            sale_amount = subtotal_cents / 100.0
                            sales_by_category[category] += sale_amount

        # --- Step 3: Prepare Output ---
        # Get all possible categories from the mapping
        all_categories = set(BOULEVARD_CATEGORY_MAPPING.values())
        
        # Create result array with all categories (including those with 0 sales)
        result = []
        for category in sorted(all_categories):
            result.append({
                "name": category,
                "value": round(sales_by_category.get(category, 0.0), 2)
            })

        return jsonify(result)

    except Exception as e:
        print(f"Error generating category breakdown: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate category breakdown: {str(e)}"}), 500

@app.route('/api/v1/sales/over_time', methods=['GET'])
@login_required
@cache.cached(timeout=300, key_prefix=_make_cache_key)  # Cache for 5 minutes
def get_sales_over_time():
    """Retrieves time-series sales data from Boulevard API."""
    try:
        # Get query parameters
        location_id = request.args.get('location_id', default='all', type=str)
        start_date_str = request.args.get('start_date', default=None, type=str)
        end_date_str = request.args.get('end_date', default=None, type=str)
        interval = request.args.get('interval', default='day', type=str)

        if interval not in ['day', 'week', 'month']:
            return jsonify({"error": "Invalid interval. Must be 'day', 'week', or 'month'."}), 400

        # --- Step 1: Get Location IDs to query ---
        target_location_ids = []
        if location_id == 'all':
            locations_response = boulevard_client.get_boulevard_locations()
            if locations_response and 'data' in locations_response and 'locations' in locations_response['data']:
                for edge in locations_response['data']['locations'].get('edges', []):
                    if edge and 'node' in edge and 'id' in edge['node']:
                        target_location_ids.append(edge['node']['id'])
            if not target_location_ids:
                print("Warning: Could not fetch location IDs for time-series data.")
                return jsonify({"error": "Could not fetch location IDs."}), 500
        else:
            target_location_ids.append(location_id)

        # --- Step 2: Fetch Sales Data for Each Location ---
        # Use defaultdict to aggregate sales by date
        from collections import defaultdict
        sales_by_date = defaultdict(float)
        transaction_counts = defaultdict(int)

        for loc_id in target_location_ids:
            # Use the Boulevard client to get sales data
            location_orders = boulevard_client.get_boulevard_kpi_data(
                location_id=loc_id,
                query_string=f"closedAt>={start_date_str}" if start_date_str else None
            )
            
            if not location_orders:
                continue

            for order in location_orders:
                if 'closedAt' not in order or 'summary' not in order:
                    continue

                try:
                    # Parse the timestamp
                    closed_dt = datetime.fromisoformat(order['closedAt'].replace('Z', '+00:00'))
                    
                    # Get the appropriate date key based on interval
                    if interval == 'day':
                        date_key = closed_dt.date().isoformat()
                    elif interval == 'week':
                        # Get the Monday of the week
                        monday = closed_dt.date() - timedelta(days=closed_dt.weekday())
                        date_key = monday.isoformat()
                    else:  # month
                        date_key = f"{closed_dt.year}-{closed_dt.month:02d}-01"

                    # Add sales amount
                    subtotal_cents = order['summary'].get('currentSubtotal', 0)
                    if isinstance(subtotal_cents, (int, float)):
                        sale_amount = subtotal_cents / 100.0
                        sales_by_date[date_key] += sale_amount
                        transaction_counts[date_key] += 1

                except (ValueError, KeyError) as e:
                    print(f"Error processing order date: {e}")
                    continue

        # --- Step 3: Prepare Output ---
        # Convert defaultdict to sorted list of dicts
        time_series_data = []
        for date_key in sorted(sales_by_date.keys()):
            time_series_data.append({
                'date': date_key,
                'sales': round(sales_by_date[date_key], 2),
                'transactions': transaction_counts[date_key],
                'average_transaction': round(
                    sales_by_date[date_key] / transaction_counts[date_key]
                    if transaction_counts[date_key] > 0 else 0,
                    2
                )
            })

        # Fill in gaps in the time series if needed
        if time_series_data and interval in ['day', 'week', 'month']:
            start_date = datetime.fromisoformat(time_series_data[0]['date'])
            end_date = datetime.fromisoformat(time_series_data[-1]['date'])
            
            current_date = start_date
            filled_data = []
            
            while current_date <= end_date:
                date_key = current_date.date().isoformat()
                existing_data = next(
                    (item for item in time_series_data if item['date'] == date_key),
                    None
                )
                
                if existing_data:
                    filled_data.append(existing_data)
                else:
                    filled_data.append({
                        'date': date_key,
                        'sales': 0.0,
                        'transactions': 0,
                        'average_transaction': 0.0
                    })
                
                # Increment date based on interval
                if interval == 'day':
                    current_date += timedelta(days=1)
                elif interval == 'week':
                    current_date += timedelta(weeks=1)
                else:  # month
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1)

            time_series_data = filled_data

        return jsonify({
            'interval': interval,
            'data': time_series_data
        })

    except Exception as e:
        print(f"Error generating time-series data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate time-series data: {str(e)}"}), 500

@app.route('/api/v1/sales/forecast', methods=['GET'])
@login_required
def get_sales_forecast():
    """Generates a sales forecast using Prophet based on historical Boulevard orders."""
    # Get filters and forecast days from request
    requested_location_id = request.args.get('location_id', default='all', type=str)
    forecast_days = request.args.get('days', default=30, type=int)
    history_days = request.args.get('history', default=365, type=int) # How many days back to fetch

    try:
        # --- Step 1: Get Location IDs to query --- 
        target_location_ids = []
        if requested_location_id == 'all':
            locations_response = boulevard_client.get_boulevard_locations()
            if locations_response and 'data' in locations_response and 'locations' in locations_response['data']:
                for edge in locations_response['data']['locations'].get('edges', []):
                    if edge and 'node' in edge and 'id' in edge['node']:
                        target_location_ids.append(edge['node']['id'])
            if not target_location_ids:
                 print("Warning: Could not fetch location IDs for forecast.")
                 return jsonify({"error": "Could not fetch location IDs for forecast."}), 500
        else:
            target_location_ids.append(requested_location_id)
        
        # --- Step 2: Fetch Historical Orders for each location --- 
        all_historical_orders = []
        for loc_id in target_location_ids:
            orders_for_location = boulevard_client.get_historical_orders(location_id=loc_id, days_history=history_days)
            if orders_for_location:
                all_historical_orders.extend(orders_for_location)
        
        if not all_historical_orders:
            return jsonify({"error": "No historical order data found for the selected scope.", "historical": [], "forecast": []}), 404
            
        # --- Step 3: Process data and aggregate daily sales --- 
        daily_sales = {}
        for order in all_historical_orders:
            try:
                # Parse the ISO 8601 closedAt timestamp
                closed_dt = isoparse(order.get('closedAt'))
                # Ensure timezone-aware comparison or convert to consistent timezone (e.g., UTC)
                # For simplicity, we use the date part only
                day = closed_dt.date() # Group by date
                
                summary = order.get('summary')
                sale_amount = 0.0
                if summary and isinstance(summary, dict):
                    subtotal_cents = summary.get('currentSubtotal')
                    if isinstance(subtotal_cents, int):
                        sale_amount = subtotal_cents / 100.0
                
                # Aggregate sales per day
                daily_sales[day] = daily_sales.get(day, 0.0) + sale_amount
            except Exception as parse_ex:
                print(f"Warning: Could not process order {order.get('id')}: {parse_ex}")
                continue # Skip orders with processing errors

        if not daily_sales:
            return jsonify({"error": "Could not aggregate daily sales data.", "historical": [], "forecast": []}), 500
            
        # --- Step 4: Prepare DataFrame for Prophet --- 
        df = pd.DataFrame(list(daily_sales.items()), columns=['ds', 'y'])
        df = df.sort_values(by='ds')
        
        if len(df) < 2:
            return jsonify({"error": "Insufficient historical data points for forecasting (need at least 2 days).", "historical": df.to_dict('records'), "forecast": []}), 400

        # --- Step 5: Fit Prophet Model --- 
        model = Prophet() # Default settings are often quite good
        model.fit(df)
        
        # --- Step 6: Generate Forecast --- 
        future = model.make_future_dataframe(periods=forecast_days)
        forecast_result = model.predict(future)
        
        # --- Step 7: Prepare Output --- 
        # Prepare historical data output (original daily aggregated data)
        historical_output_df = df.copy()
        historical_output_df = historical_output_df.rename(columns={'ds': 'date', 'y': 'sales'}) # RENAME COLUMNS
        
        # Select relevant columns from forecast and RENAME
        forecast_output_df = forecast_result[['ds', 'yhat', 'yhat_lower', 'yhat_upper']] 
        forecast_output_df = forecast_output_df.rename(columns={
            'ds': 'date', 
            'yhat': 'mean', 
            'yhat_lower': 'mean_ci_lower', 
            'yhat_upper': 'mean_ci_upper'
        }) 
        
        # Convert DataFrames to list of dicts for JSON
        historical_output = historical_output_df.to_dict('records')
        forecast_output = forecast_output_df.to_dict('records')

        # Ensure date format is string YYYY-MM-DD for JSON
        for row in historical_output:
            if isinstance(row['date'], (datetime, pd.Timestamp)): # Check if it's a date object
                row['date'] = row['date'].strftime('%Y-%m-%d')
        for row in forecast_output:
            if isinstance(row['date'], (datetime, pd.Timestamp)): # Check if it's a date object
                row['date'] = row['date'].strftime('%Y-%m-%d')
            # Ensure forecast values are rounded reasonably
            for col in ['mean', 'mean_ci_lower', 'mean_ci_upper']:
                row[col] = round(row[col], 2) if col in row else None
            
        return jsonify({
            "historical": historical_output,
            "forecast": forecast_output,
            "note": f"Forecast generated using Prophet based on {len(df)} days of historical data from Boulevard API."
        })

    except Exception as e:
        print(f"Error during forecasting: {e}") # Log the error server-side
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return jsonify({"error": f"An unexpected error occurred during forecasting: {e}"}), 500

# --- Utility Endpoints ---

@app.route('/api/v1/locations', methods=['GET'])
@login_required
def get_locations():
    """Retrieves list of available locations from Boulevard API."""
    try:
        # Call the Boulevard client function
        boulevard_data = boulevard_client.get_boulevard_locations()
        
        # Check for errors from the API call
        if boulevard_data is None or 'errors' in boulevard_data or 'data' not in boulevard_data:
            error_detail = boulevard_data.get('errors', 'Unknown API error') if boulevard_data else 'No response'
            print(f"Error fetching locations from Boulevard: {error_detail}")
            return jsonify({"error": "Failed to fetch locations from source API.", "details": error_detail}), 502 # Bad Gateway
        
        # Extract location data from the nested structure
        locations = []
        if boulevard_data['data'] and 'locations' in boulevard_data['data'] and boulevard_data['data']['locations'] and 'edges' in boulevard_data['data']['locations']:
            for edge in boulevard_data['data']['locations']['edges']:
                if edge and 'node' in edge:
                    node = edge['node']
                    # Adapt this structure based on actual fields available/needed
                    locations.append({
                        "location_id": node.get('id'), # Using Boulevard ID
                        "name": node.get('name'),
                        "address": node.get('address'), # Add other fields if needed/available
                        "latitude": node.get('latitude'),
                        "longitude": node.get('longitude'),
                        # Add other fields as necessary, map to expected frontend keys
                        # e.g., "total_sales" would need a separate calculation or call
                    })
        
        return jsonify(locations)

    except Exception as e:
        print(f"Unexpected error in /api/v1/locations endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

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
                    (transaction_id, item_type, product_id, service_id, quantity, round(unit_price_db, 2), round(net_price, 2)) # Corrected variable name
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
            # Clear caches after successful upload
            clear_sales_caches()
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

# --- Utility Function (Consider moving to a utils file later) ---
# def _get_item_cost(item_id, item_type):
#    """Placeholder function to get cost using the global MOCK lists."""
#    # ... (Removed function body) ...


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
    # print(f"--- LOGIN ATTEMPT ---") # DEBUG REMOVED
    # print(f"Received Username: {username}") # DEBUG REMOVED
    # print(f"Received Password: {password is not None}") # DEBUG REMOVED

    if not username or not password:
        # print("Login Error: Missing username or password") # DEBUG REMOVED
        return jsonify({"message": "Username and password required"}), 400

    db = get_db()
    user_data = db.execute(
        'SELECT user_id, username, password_hash FROM users WHERE username = ?',
        (username,)
    ).fetchone()
    
    # print(f"DB User Data Found: {dict(user_data) if user_data else None}") # DEBUG REMOVED

    if user_data:
        password_match = check_password_hash(user_data['password_hash'], password)
        # print(f"Password Check Result: {password_match}") # DEBUG REMOVED
        if password_match:
            # Password matches
            user = User(id=user_data['user_id'], username=user_data['username']) 
            login_user(user) # Use Flask-Login function
            # print(f"Login Success for user: {username}") # DEBUG REMOVED
            return jsonify({"success": True, "message": "Login successful"}), 200
        else:
            # Invalid password
            # print(f"Login Error: Invalid password for user: {username}") # DEBUG REMOVED
            return jsonify({"message": "Invalid username or password"}), 401
    else:
        # Invalid username
        # print(f"Login Error: User not found: {username}") # DEBUG REMOVED
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
        return jsonify({"isLoggedIn": True, "user": {"id": current_user.id, "username": current_user.username}})
    else:
        return jsonify({"isLoggedIn": False})

# --- NEW Category Mapping Endpoint ---
@app.route('/api/category-mappings', methods=['GET'])
# @login_required # Consider if this needs auth
def get_category_mappings():
    """Returns the defined mapping from Boulevard service/product names to categories."""
    return jsonify(BOULEVARD_CATEGORY_MAPPING)
# --- END NEW Endpoint ---

# --- NEW: Profit Calculation Endpoint ---
@app.route('/api/v1/profit/by_category', methods=['GET'])
@login_required
def get_profit_by_category():
    """
    Calculates total profit (revenue - cost) for each item category based on DB data.
    
    *** LIMITATION ***: This endpoint currently calculates profit using placeholder costs 
    defined in the MOCK_PRODUCTS and MOCK_SERVICES lists within this file. 
    It uses the integer IDs stored in the database transaction_items table for lookup.
    It does NOT use the real-time API-fetched product costs or the URN-based service 
    cost mapping used by the /api/v1/kpis endpoint. This is due to the complexity 
    of mapping database integer IDs back to Boulevard URNs needed for those more 
    accurate cost sources without schema changes. 
    The profit figures here are therefore estimates based on potentially outdated mock data.
    """
    db = get_db()
    location_id_str = request.args.get('location_id', default='all', type=str)
    start_date_str = request.args.get('start_date', default=None, type=str)
    end_date_str = request.args.get('end_date', default=None, type=str)

    # --- Build Filters ---
    params = []
    where_clauses = ["1=1"] # Start with a clause that's always true

    # Location Filter
    if location_id_str != 'all':
        # Assuming location_id_str is the integer ID from the locations table for DB filtering
        try:
             loc_id_int = int(location_id_str)
             where_clauses.append("t.location_id = ?")
             params.append(loc_id_int)
        except ValueError:
             print(f"Warning: Invalid location_id received in get_profit_by_category: {location_id_str}")
             # Optionally return an error or just proceed without location filter
             # return jsonify({"error": "Invalid location ID format."}), 400
             pass 

    # Date Filters (Using SQLite date functions)
    if start_date_str:
        try:
            datetime.strptime(start_date_str, '%Y-%m-%d') # Validate format
            where_clauses.append("DATE(t.transaction_time) >= ?")
            params.append(start_date_str)
        except ValueError:
             print(f"Warning: Invalid start_date format in get_profit_by_category: {start_date_str}")
             pass # Ignore invalid date
             
    if end_date_str:
        try:
            datetime.strptime(end_date_str, '%Y-%m-%d') # Validate format
            where_clauses.append("DATE(t.transaction_time) <= ?")
            params.append(end_date_str)
        except ValueError:
             print(f"Warning: Invalid end_date format in get_profit_by_category: {end_date_str}")
             pass # Ignore invalid date

    where_sql = " AND ".join(where_clauses)

    # --- Query Transaction Items and Join with Categories ---
    query = f"""
        SELECT 
            ti.item_type,
            ti.product_id,
            ti.service_id,
            ti.quantity,
            ti.net_price,
            tc.name as category_name,
            tc.category_id -- Added category_id for grouping consistency
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        -- Join based on item type to get category
        LEFT JOIN services s ON ti.service_id = s.service_id AND ti.item_type = 'service'
        LEFT JOIN products p ON ti.product_id = p.product_id AND ti.item_type = 'product'
        LEFT JOIN treatment_categories tc ON tc.category_id = COALESCE(s.category_id, p.category_id)
        WHERE ({where_sql}) AND tc.category_id IS NOT NULL -- Only include items with a category
    """

    try:
        cursor = db.execute(query, params)
        items = cursor.fetchall()
        
        # --- Calculate Profit per Category using Real Inventory Costs (with fuzzy matching) ---
        profit_by_category = defaultdict(float)
        
        # Pre-fetch product and service names for ID lookup
        product_names = {row['product_id']: row['name'] for row in db.execute('SELECT product_id, name FROM products').fetchall()}
        service_names = {row['service_id']: row['name'] for row in db.execute('SELECT service_id, name FROM services').fetchall()}
        inventory_names = list(inventory_cost_map.keys())
        
        for item in items:
            item_cost = 0.0
            quantity = item['quantity'] if item['quantity'] else 0 # Handle null quantity? Default to 0
            net_price = item['net_price'] if item['net_price'] else 0.0
            category_name = item['category_name']
            
            def get_cost_by_name(name):
                if not name:
                    return 0.0
                if name in inventory_cost_map:
                    return inventory_cost_map[name]['avg_unit_cost']
                # Fuzzy match if exact not found
                close = difflib.get_close_matches(name, inventory_names, n=1, cutoff=0.8)
                if close:
                    print(f"[ProfitCalc] Fuzzy matched '{name}' to inventory '{close[0]}'")
                    return inventory_cost_map[close[0]]['avg_unit_cost']
                print(f"[ProfitCalc] No inventory cost found for '{name}' (even with fuzzy match)")
                return 0.0
            
            if item['item_type'] == 'product' and item['product_id']:
                prod_name = product_names.get(item['product_id'])
                item_cost = get_cost_by_name(prod_name)
            elif item['item_type'] == 'service' and item['service_id']:
                serv_name = service_names.get(item['service_id'])
                item_cost = get_cost_by_name(serv_name)
                
            item_profit = net_price - (quantity * item_cost)
            profit_by_category[category_name] += item_profit

        # --- Format Output ---
        # Get all category names to ensure all are represented, even with 0 profit
        all_categories_cursor = db.execute('SELECT name FROM treatment_categories ORDER BY name')
        all_category_names = {row['name'] for row in all_categories_cursor.fetchall()}

        # Build final result including categories with zero profit
        result_data = [
            {'name': cat_name, 'profit': round(profit_by_category.get(cat_name, 0.0), 2)}
            for cat_name in sorted(list(all_category_names))
        ]
        
        return jsonify(result_data)

    except sqlite3.Error as e:
        print(f"Database error fetching profit by category: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to calculate profit data due to database error."}), 500
    except Exception as e:
        print(f"Unexpected error calculating profit by category: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred while calculating profit data."}), 500

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

# --- END NEW Endpoint ---

# --- NEW: Categorized Boulevard Orders Endpoint ---
@app.route('/api/v1/boulevard/categorized-orders', methods=['GET'])
# @login_required # Temporarily disabled for testing category mapping
def get_categorized_orders():
    """Fetches historical orders from Boulevard, adds category mapping, and returns.
    Accepts optional query parameters: 
    - location_id (Boulevard Location ID, defaults to 'all')
    - days (Number of past days to fetch, defaults to 30)
    """
    print("Received request for categorized orders.")
    # Get filters from request arguments
    requested_location_id = request.args.get('location_id', default='all', type=str)
    days_history = request.args.get('days', default=30, type=int) # Default to 30 days history
    # TODO: Add support for start_date/end_date filtering if needed, 
    # requires modifying get_historical_orders or using get_boulevard_kpi_data
    
    print(f"Fetching categorized orders for location: {requested_location_id}, history: {days_history} days")

    try:
        # --- Step 1: Get Location IDs to query ---
        target_location_ids = []
        if requested_location_id == 'all':
            locations_response = boulevard_client.get_boulevard_locations()
            if locations_response and 'data' in locations_response and 'locations' in locations_response['data']:
                for edge in locations_response['data']['locations'].get('edges', []):
                    if edge and 'node' in edge and 'id' in edge['node']:
                        target_location_ids.append(edge['node']['id'])
            if not target_location_ids:
                 print("Warning: Could not fetch location IDs for categorized orders query.")
                 return jsonify({"error": "Could not fetch location IDs for aggregation."}), 500
        else:
            target_location_ids.append(requested_location_id) # Assume it's a valid Boulevard URN ID

        # --- Step 2: Fetch Historical Orders for each location ---
        all_fetched_orders = []
        for loc_id in target_location_ids:
            orders_for_location = boulevard_client.get_historical_orders(location_id=loc_id, days_history=days_history)
            if orders_for_location:
                all_fetched_orders.extend(orders_for_location)

        if not all_fetched_orders:
            return jsonify({"message": "No orders found for the specified scope and timeframe.", "orders": []}), 200
            
        # --- Step 3: Get Category Mapping (using the global dictionary) ---
        category_map = BOULEVARD_CATEGORY_MAPPING
        default_category = category_map.get("DEFAULT_CATEGORY", "Uncategorized")
        
        # --- Step 4: Process Orders - Add Category to Line Items --- 
        # It's safer to create a new list rather than modifying the original dicts in place
        categorized_orders = []
        for order in all_fetched_orders:
            # Create a copy to avoid modifying original if necessary, though modifying directly might be okay here
            processed_order = order.copy() 
            
            # Ensure lineGroups exists and is iterable
            if 'lineGroups' in processed_order and isinstance(processed_order['lineGroups'], list):
                # Iterate through line groups (can be multiple, e.g., different staff)
                for line_group in processed_order['lineGroups']:
                    # Ensure lines exists and is iterable
                    if 'lines' in line_group and isinstance(line_group['lines'], list):
                        processed_lines = []
                        for line in line_group['lines']:
                             processed_line = line.copy()
                             item_name = processed_line.get('name')
                             category = default_category # Default if no name or not found
                             if item_name:
                                 category = category_map.get(item_name, default_category)
                             processed_line['category'] = category
                             processed_lines.append(processed_line)
                        # Replace original lines with processed lines
                        line_group['lines'] = processed_lines
                        
            categorized_orders.append(processed_order)
            
        # --- Step 5: Return Categorized Data --- 
        return jsonify({"orders": categorized_orders}) 

    except ValueError as ve:
        # Catch potential configuration errors from auth generation
        print(f"Configuration error fetching categorized orders: {ve}")
        return jsonify({"error": f"Configuration Error: {ve}"}), 500
    except Exception as e:
        print(f"Error fetching categorized Boulevard orders: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An internal server error occurred: {e}"}), 500
# --- END Categorized Boulevard Orders Endpoint ---

# --- Service Names Known for Tip Override Workflow --- 
# Add exact names from Boulevard as needed
TIP_OVERRIDE_SERVICE_NAMES = [
    "NEW PATIENT BOTOX/DYSPORT", 
    # Add other service names here if they are used similarly
    # e.g., "Toxin Consult", "Neuromodulator Injection"
]
# --- End Service Names ---

def load_inventory_costs(csv_path='inventory_on_hand_20250426.csv'):
    """
    Loads inventory cost and retail price data from the provided CSV.
    Returns a dict mapping product name to {'avg_unit_cost': float, 'retail_price': float}.
    """
    inventory_map = {}
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')  # Use tab delimiter
            for row in reader:
                name = row.get('Product')
                if not name:
                    continue
                # Clean and parse cost/price fields
                def parse_money(val):
                    try:
                        return float(str(val).replace('$','').replace(',','').replace('(','-').replace(')',''))
                    except Exception:
                        return 0.0
                avg_unit_cost = parse_money(row.get('Avg Unit Cost', 0))
                retail_price = parse_money(row.get('Retail Price', 0))
                # Remove quotes from name if present
                name = name.strip().strip('"')
                inventory_map[name] = {
                    'avg_unit_cost': avg_unit_cost,
                    'retail_price': retail_price
                }
    except Exception as e:
        print(f"Error loading inventory CSV: {e}")
    return inventory_map

# Load inventory data at startup (can be reloaded as needed)
inventory_cost_map = load_inventory_costs('inventory_on_hand_20250426.csv')

def _make_cache_key(*args, **kwargs):
    """Generate a cache key that includes query parameters."""
    key = request.path
    args = str(hash(frozenset(request.args.items())))
    return f"{key}|{args}"

@app.route('/api/v1/kpis', methods=['GET'])
@login_required
@cache.cached(timeout=300, key_prefix=_make_cache_key)  # Cache for 5 minutes
def get_kpis():
    """Retrieves KPI data including profitability metrics from Boulevard API."""
    try:
        # Get date range from request
        end_date = request.args.get('end_date')
        start_date = request.args.get('start_date')
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')

        print(f"[KPI] Fetching orders for date range: {start_date} to {end_date}")
        # --- Step 1: Get Orders from Boulevard ---
        all_orders = get_orders_for_date_range(start_date, end_date)
        print(f"[KPI] Found {len(all_orders) if all_orders else 0} orders")
        
        if not all_orders:
            print("[KPI] No orders found, returning empty data")
            return jsonify({
                "total_sales": 0,
                "total_profit": 0,
                "profit_margin": 0,
                "items": [],
                "trends": [],
                "discounts": []
            })

        # --- Step 2: Calculate KPIs ---
        db = get_db()
        print("[KPI] Starting KPI calculation...")
        kpi_data = calculate_kpis(all_orders, db)
        
        if not kpi_data:
            print("[KPI] Failed to calculate KPI data")
            return jsonify({
                "error": "Failed to calculate KPI data"
            }), 500

        print(f"[KPI] KPI calculation successful:")
        print(f"  - Total Sales: {kpi_data.get('total_sales', 0)}")
        print(f"  - Total Profit: {kpi_data.get('total_profit', 0)}")
        print(f"  - Profit Margin: {kpi_data.get('profit_margin', 0)}%")
        print(f"  - Number of trends data points: {len(kpi_data.get('trends', []))}")
        print(f"  - Number of items: {len(kpi_data.get('items', []))}")
        print(f"  - Number of discounts: {len(kpi_data.get('discounts', []))}")
        
        if kpi_data.get('trends'):
            print(f"  - First trend date: {kpi_data['trends'][0]['date']}")
            print(f"  - Last trend date: {kpi_data['trends'][-1]['date']}")

        # Return the complete KPI data including trends and discounts
        return jsonify(kpi_data)

    except Exception as e:
        print(f"Error generating KPI data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate KPI data: {str(e)}"}), 500

def get_orders_for_date_range(start_date, end_date):
    """Fetches orders from Boulevard API for the specified date range."""
    try:
        print(f"[Orders] Getting orders for date range: {start_date} to {end_date}")
        # Get all location IDs first
        locations_response = boulevard_client.get_boulevard_locations()
        if not locations_response or 'data' not in locations_response or 'locations' not in locations_response['data']:
            print("[Orders] Could not fetch location IDs")
            print(f"[Orders] Response: {locations_response}")
            return []

        target_location_ids = []
        for edge in locations_response['data']['locations'].get('edges', []):
            if edge and 'node' in edge and 'id' in edge['node']:
                target_location_ids.append(edge['node']['id'])

        if not target_location_ids:
            print("[Orders] No location IDs found")
            return []

        print(f"[Orders] Found {len(target_location_ids)} locations")

        # Fetch orders for each location
        all_orders = []
        for loc_id in target_location_ids:
            try:
                # Convert date strings to datetime objects if they're strings
                if isinstance(start_date, str):
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = start_date
                
                if isinstance(end_date, str):
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = end_date

                # Format dates for Boulevard API
                query_string = f"closedAt >= '{start_dt.strftime('%Y-%m-%d')}T00:00:00Z'"
                if end_dt:
                    query_string += f" AND closedAt <= '{end_dt.strftime('%Y-%m-%d')}T23:59:59Z'"

                print(f"[Orders] Fetching orders for location {loc_id} with query: {query_string}")
                location_orders = boulevard_client.get_boulevard_kpi_data(
                    location_id=loc_id,
                    query_string=query_string
                )
                
                if location_orders:
                    print(f"[Orders] Found {len(location_orders)} orders for location {loc_id}")
                    all_orders.extend(location_orders)
                else:
                    print(f"[Orders] No orders found for location {loc_id}")

            except Exception as loc_error:
                print(f"[Orders] Error fetching orders for location {loc_id}: {loc_error}")
                continue

        # Sort orders by date
        if all_orders:
            all_orders.sort(key=lambda x: x.get('closedAt', ''))
            print(f"[Orders] Total orders found across all locations: {len(all_orders)}")
            if all_orders:
                print(f"[Orders] Date range of orders: {all_orders[0].get('closedAt')} to {all_orders[-1].get('closedAt')}")
        else:
            print("[Orders] No orders found across all locations")

        return all_orders

    except Exception as e:
        print(f"[Orders] Error fetching orders: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.route('/api/v1/sales/summary', methods=['GET'])
@login_required
@cache.cached(timeout=300, key_prefix=_make_cache_key)  # Cache for 5 minutes
def get_sales_summary():
    """Retrieves aggregated sales summary data from Boulevard API."""
    try:
        # Get query parameters
        location_id = request.args.get('location_id', default='all', type=str)
        start_date_str = request.args.get('start_date', default=None, type=str)
        end_date_str = request.args.get('end_date', default=None, type=str)

        # --- Step 1: Get Location IDs to query ---
        target_location_ids = []
        if location_id == 'all':
            locations_response = boulevard_client.get_boulevard_locations()
            if locations_response and 'data' in locations_response and 'locations' in locations_response['data']:
                for edge in locations_response['data']['locations'].get('edges', []):
                    if edge and 'node' in edge and 'id' in edge['node']:
                        target_location_ids.append(edge['node']['id'])
            if not target_location_ids:
                print("Warning: Could not fetch location IDs for sales summary.")
                return jsonify({"error": "Could not fetch location IDs."}), 500
        else:
            target_location_ids.append(location_id)

        # --- Step 2: Fetch Sales Data for Each Location ---
        summary_data = {
            'total_sales': 0.0,
            'total_transactions': 0,
            'avg_transaction_value': 0.0,
            'sales_by_type': {
                'services': 0.0,
                'products': 0.0,
                'other': 0.0
            },
            'sales_by_location': {},
            'top_items': []
        }

        item_sales = {}  # Track sales by item for top items calculation

        for loc_id in target_location_ids:
            # Use the Boulevard client to get sales data
            location_orders = boulevard_client.get_boulevard_kpi_data(
                location_id=loc_id,
                query_string=f"closedAt>={start_date_str}" if start_date_str else None
            )
            
            if not location_orders:
                continue

            location_total = 0.0
            
            for order in location_orders:
                if 'summary' in order and 'currentSubtotal' in order['summary']:
                    subtotal_cents = order['summary']['currentSubtotal']
                    if isinstance(subtotal_cents, (int, float)):
                        sale_amount = subtotal_cents / 100.0
                        summary_data['total_sales'] += sale_amount
                        location_total += sale_amount
                        summary_data['total_transactions'] += 1

                # Process line items for type breakdown and top items
                if 'lineGroups' in order:
                    for group in order['lineGroups']:
                        if 'lines' in group:
                            for line in group['lines']:
                                item_type = 'services' if line.get('__typename') == 'OrderServiceLine' else 'products'
                                subtotal_cents = line.get('currentSubtotal', 0)
                                line_amount = subtotal_cents / 100.0 if subtotal_cents else 0

                                # Add to type totals
                                summary_data['sales_by_type'][item_type] += line_amount

                                # Track individual item sales
                                item_name = line.get('name', 'Unknown Item')
                                if item_name not in item_sales:
                                    item_sales[item_name] = {
                                        'name': item_name,
                                        'type': item_type.rstrip('s'),  # Remove 's' for singular
                                        'total_sales': 0.0,
                                        'quantity': 0
                                    }
                                item_sales[item_name]['total_sales'] += line_amount
                                item_sales[item_name]['quantity'] += line.get('quantity', 0)

            # Add location total to summary
            if location_total > 0:
                location_name = "All Locations" if location_id == 'all' else f"Location {loc_id}"
                summary_data['sales_by_location'][location_name] = round(location_total, 2)

        # Calculate average transaction value
        if summary_data['total_transactions'] > 0:
            summary_data['avg_transaction_value'] = round(
                summary_data['total_sales'] / summary_data['total_transactions'], 
                2
            )

        # Get top 10 items by sales
        top_items = sorted(
            item_sales.values(), 
            key=lambda x: x['total_sales'], 
            reverse=True
        )[:10]
        
        # Round values in top items
        for item in top_items:
            item['total_sales'] = round(item['total_sales'], 2)
        
        summary_data['top_items'] = top_items

        # Round all monetary values
        summary_data['total_sales'] = round(summary_data['total_sales'], 2)
        for key in summary_data['sales_by_type']:
            summary_data['sales_by_type'][key] = round(summary_data['sales_by_type'][key], 2)

        return jsonify(summary_data)

    except Exception as e:
        print(f"Error generating sales summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate sales summary: {str(e)}"}), 500

@app.route('/api/v1/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """Clear all cached data. Requires authentication."""
    try:
        # Clear all caches
        cache.clear()
        return jsonify({"message": "Cache cleared successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to clear cache: {str(e)}"}), 500

def clear_sales_caches():
    """Clear all sales-related caches."""
    try:
        # Get all cache keys
        with app.app_context():
            # Clear specific patterns
            patterns = [
                'view//api/v1/kpis',
                'view//api/v1/sales/summary',
                'view//api/v1/sales/over_time',
                'view//api/v1/sales/by_category'
            ]
            for pattern in patterns:
                keys = cache.cache._cache.keys()  # Access underlying cache storage
                for key in keys:
                    if isinstance(key, str) and key.startswith(pattern):
                        cache.delete(key)
    except Exception as e:
        print(f"Error clearing sales caches: {e}")

@app.route('/', methods=['GET'])
def index():
    """Landing page with API information and available endpoints"""
    # Check if request wants JSON
    if request.headers.get('Accept') == 'application/json':
        return jsonify({"message": "Rella Analytics API is running"}), 200
        
    # Otherwise return HTML
    endpoints = [
        {
            'path': '/api/v1/kpis',
            'methods': ['GET'],
            'description': 'Get key performance indicators'
        },
        {
            'path': '/api/v1/sales/summary',
            'methods': ['GET'],
            'description': 'Get sales summary data'
        },
        {
            'path': '/api/v1/sales/by_category',
            'methods': ['GET'],
            'description': 'Get sales data by category'
        },
        {
            'path': '/api/v1/sales/over_time',
            'methods': ['GET'],
            'description': 'Get time-series sales data'
        },
        {
            'path': '/api/v1/sales/forecast',
            'methods': ['GET'],
            'description': 'Get sales forecast'
        },
        {
            'path': '/api/v1/locations',
            'methods': ['GET'],
            'description': 'Get available locations'
        },
        {
            'path': '/api/v1/boulevard/categorized-orders',
            'methods': ['GET'],
            'description': 'Get categorized Boulevard orders'
        },
        {
            'path': '/api/v1/auth/login',
            'methods': ['POST'],
            'description': 'Login endpoint'
        },
        {
            'path': '/api/v1/auth/logout',
            'methods': ['POST'],
            'description': 'Logout endpoint'
        }
    ]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rella Analytics API</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            .status {{
                display: inline-block;
                padding: 8px 15px;
                background: #2ecc71;
                color: white;
                border-radius: 20px;
                font-size: 14px;
            }}
            .endpoint {{
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .method {{
                display: inline-block;
                padding: 4px 8px;
                background: #3498db;
                color: white;
                border-radius: 4px;
                font-size: 12px;
                margin-right: 10px;
            }}
            .path {{
                font-family: monospace;
                font-size: 14px;
                color: #2c3e50;
            }}
            .description {{
                margin-top: 5px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Rella Analytics API <span class="status">Running</span></h1>
            
            <h2>Available Endpoints</h2>
            <div class="endpoints">
                {''.join(f"""
                    <div class="endpoint">
                        <div>
                            {''.join(f'<span class="method">{method}</span>' for method in ep['methods'])}
                            <span class="path">{ep['path']}</span>
                        </div>
                        <div class="description">{ep['description']}</div>
                    </div>
                """ for ep in endpoints)}
            </div>
            
            <h2>API Information</h2>
            <ul>
                <li>All endpoints require authentication except /api/v1/auth/login</li>
                <li>Data is cached for 5 minutes by default</li>
                <li>Use /api/v1/cache/clear to manually clear cached data</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/api/test-boulevard-connection', methods=['GET'])
def test_boulevard_connection():
    """Test endpoint to verify Boulevard API connection."""
    print("Starting Boulevard API connection test...")
    try:
        # Try to get locations as a simple test
        print("Attempting to get Boulevard locations...")
        response = boulevard_client.get_boulevard_locations()
        print(f"Got response: {response}")
        
        if response and 'data' in response and 'locations' in response['data']:
            locations = response['data']['locations'].get('edges', [])
            result = {
                'status': 'success',
                'message': f'Successfully connected to Boulevard API. Found {len(locations)} locations.',
                'locations': locations
            }
            print(f"Success! {result['message']}")
            return jsonify(result)
        else:
            error_detail = response.get('errors', ['Unknown error']) if response else ['No response']
            result = {
                'status': 'error',
                'message': 'Connected to API but received unexpected response format',
                'errors': error_detail
            }
            print(f"API format error: {result}")
            return jsonify(result), 400

    except ValueError as e:
        # This catches missing environment variables
        result = {
            'status': 'error',
            'message': str(e),
            'type': 'configuration_error'
        }
        print(f"Configuration error: {result}")
        return jsonify(result), 400
    except Exception as e:
        result = {
            'status': 'error',
            'message': f'Failed to connect to Boulevard API: {str(e)}',
            'type': 'connection_error'
        }
        print(f"Connection error: {result}")
        return jsonify(result), 500

def calculate_kpis(orders, db):
    """Calculate KPIs from Boulevard orders data."""
    try:
        if not orders:
            return {
                "total_sales": 0.0,
                "total_transactions": 0,
                "avg_transaction_value": 0.0,
                "total_profit": 0.0,
                "profit_margin": 0.0,
                "trends": [],
                "discounts": [],
                "items": []
            }

        # Initialize KPI tracking
        total_sales = 0.0
        total_profit = 0.0
        daily_metrics = defaultdict(lambda: {"sales": 0.0, "profit": 0.0, "transactions": 0})
        discount_tracking = defaultdict(lambda: {
            "name": "",
            "type": "",
            "total_amount": 0.0,
            "usage_count": 0,
            "profit_impact": 0.0,
            "average_discount": 0.0
        })

        # Track items for profitability analysis
        items_tracking = defaultdict(lambda: {
            "name": "",
            "type": "",
            "quantity": 0,
            "total_sales": 0.0,
            "total_cost": 0.0,
            "total_profit": 0.0,
            "profit_margin": 0.0
        })

        # Get inventory cost map from database
        inventory_cost_map = {}
        try:
            cursor = db.cursor()
            cursor.execute('SELECT name, avg_unit_cost FROM inventory_costs')
            for row in cursor.fetchall():
                inventory_cost_map[row[0]] = {
                    'avg_unit_cost': float(row[1]) if row[1] else 0.0
                }
        except Exception as db_error:
            print(f"Warning: Could not fetch inventory costs: {db_error}")

        # Process each order
        for order in orders:
            try:
                # Get order date for trends
                if not order.get('closedAt'):
                    print(f"Warning: Order missing closedAt timestamp: {order.get('id')}")
                    continue

                closed_at = datetime.fromisoformat(order['closedAt'].replace('Z', '+00:00'))
                order_date = closed_at.date()

                # Get order summary data
                summary = order.get('summary', {})
                subtotal_cents = summary.get('currentSubtotal', 0)
                if not isinstance(subtotal_cents, (int, float)):
                    print(f"Warning: Invalid subtotal for order {order.get('id')}: {subtotal_cents}")
                    continue

                # Calculate order total in dollars
                order_total = subtotal_cents / 100.0
                total_sales += order_total

                # Track daily metrics
                daily_metrics[order_date]["sales"] += order_total
                daily_metrics[order_date]["transactions"] += 1

                # Process line items for detailed analysis
                order_cost = 0.0
                if 'lineGroups' in order:
                    for group in order['lineGroups']:
                        if 'lines' not in group:
                            continue

                        for line in group['lines']:
                            line_subtotal_cents = line.get('currentSubtotal', 0)
                            line_amount = line_subtotal_cents / 100.0 if line_subtotal_cents else 0.0
                            
                            # Get item name and type
                            item_name = line.get('name', 'Unknown Item')
                            item_type = 'service' if line.get('__typename') == 'OrderServiceLine' else 'product'

                            # Calculate line item cost
                            # First try to get cost from inventory map
                            unit_cost = 0.0
                            if item_name in inventory_cost_map:
                                unit_cost = inventory_cost_map[item_name]['avg_unit_cost']
                            else:
                                # Fallback to default cost percentages
                                if item_type == 'product':
                                    unit_cost = line_amount * 0.4  # 40% cost for products
                                else:
                                    unit_cost = line_amount * 0.3  # 30% cost for services

                            quantity = line.get('quantity', 1)
                            line_cost = unit_cost * quantity
                            order_cost += line_cost

                            # Track item metrics
                            items_tracking[item_name].update({
                                "name": item_name,
                                "type": item_type,
                                "quantity": items_tracking[item_name]["quantity"] + quantity,
                                "total_sales": items_tracking[item_name]["total_sales"] + line_amount,
                                "total_cost": items_tracking[item_name]["total_cost"] + line_cost
                            })
                            # Calculate and update profit metrics for the item
                            item_profit = line_amount - line_cost
                            items_tracking[item_name]["total_profit"] = items_tracking[item_name]["total_sales"] - items_tracking[item_name]["total_cost"]
                            items_tracking[item_name]["profit_margin"] = (
                                (items_tracking[item_name]["total_profit"] / items_tracking[item_name]["total_sales"] * 100)
                                if items_tracking[item_name]["total_sales"] > 0 else 0
                            )

                            # Track discounts if present
                            discount_amount_cents = line.get('currentDiscountAmount', 0)
                            if discount_amount_cents:
                                discount_amount = discount_amount_cents / 100.0
                                discount_name = "Line Item Discount"  # Generic name since we don't have specific discount info
                                
                                # Update discount tracking
                                discount_tracking[discount_name].update({
                                    "name": discount_name,
                                    "type": item_type,
                                    "total_amount": discount_tracking[discount_name]["total_amount"] + discount_amount,
                                    "usage_count": discount_tracking[discount_name]["usage_count"] + 1,
                                    # Estimate profit impact (assuming discount directly reduces profit)
                                    "profit_impact": discount_tracking[discount_name]["profit_impact"] - (discount_amount * (0.6 if item_type == 'product' else 0.7))
                                })

                # Calculate order profit and add to totals
                order_profit = order_total - order_cost
                total_profit += order_profit
                daily_metrics[order_date]["profit"] += order_profit

            except Exception as order_error:
                print(f"Error processing order {order.get('id')}: {order_error}")
                continue

        # Calculate final KPIs
        total_transactions = len(orders)
        avg_transaction = total_sales / total_transactions if total_transactions > 0 else 0
        profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

        # Prepare trends data (sort by date)
        trends = []
        if daily_metrics:  # Only process if we have data
            # Get date range
            start_date = min(daily_metrics.keys())
            end_date = max(daily_metrics.keys())
            current_date = start_date

            # Fill in all dates in range
            while current_date <= end_date:
                metrics = daily_metrics[current_date]
                daily_sales = metrics["sales"]
                daily_profit = metrics["profit"]
                daily_margin = (daily_profit / daily_sales * 100) if daily_sales > 0 else 0
                
                trends.append({
                    "date": current_date.isoformat(),
                    "sales": round(daily_sales, 2),
                    "profit": round(daily_profit, 2),
                    "profit_margin": round(daily_margin, 2),
                    "transactions": metrics["transactions"]
                })
                current_date += timedelta(days=1)

        # Prepare items data
        items = []
        for item_data in items_tracking.values():
            items.append({
                "name": item_data["name"],
                "type": item_data["type"],
                "quantity": item_data["quantity"],
                "total_sales": round(item_data["total_sales"], 2),
                "total_cost": round(item_data["total_cost"], 2),
                "total_profit": round(item_data["total_profit"], 2),
                "profit_margin": round(item_data["profit_margin"], 2)
            })

        # Sort items by profit
        items.sort(key=lambda x: x["total_profit"], reverse=True)

        # Prepare discount data
        discounts = []
        for discount_data in discount_tracking.values():
            if discount_data["usage_count"] > 0:
                discount_data["average_discount"] = (
                    discount_data["total_amount"] / discount_data["usage_count"]
                )
                discounts.append({
                    "name": discount_data["name"],
                    "type": discount_data["type"],
                    "total_amount": round(discount_data["total_amount"], 2),
                    "usage_count": discount_data["usage_count"],
                    "profit_impact": round(discount_data["profit_impact"], 2),
                    "average_discount": round(discount_data["average_discount"], 2)
                })

        # Sort discounts by total amount
        discounts.sort(key=lambda x: x["total_amount"], reverse=True)

        return {
            "total_sales": round(total_sales, 2),
            "total_transactions": total_transactions,
            "avg_transaction_value": round(avg_transaction, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin": round(profit_margin, 2),
            "trends": trends,
            "discounts": discounts,
            "items": items
        }

    except Exception as e:
        print(f"Error calculating KPIs: {e}")
        import traceback
        traceback.print_exc()
        return None

# --- End KPI Calculation Function ---

if __name__ == '__main__':
    # Note: Use a production WSGI server like Gunicorn or Waitress for deployment
    # app.run(debug=True, host='0.0.0.0', port=5001) # Ensure correct port if running directly
    pass # Typically run via 'flask run' which handles port/host 