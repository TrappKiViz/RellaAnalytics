import pandas as pd
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from models.analytics_schema import Base, Transaction, Client, Staff, Appointment, MarketingMetrics, FinancialMetrics

def categorize_service(service_name):
    service_name = service_name.lower()
    if any(x in service_name for x in ['botox', 'dysport', 'tox']):
        return 'tox'
    elif any(x in service_name for x in ['filler', 'juvederm', 'voluma', 'vollure']):
        return 'filler'
    elif any(x in service_name for x in ['facial', 'hydrafacial']):
        return 'facials'
    elif any(x in service_name for x in ['laser', 'hair removal']):
        return 'lasers'
    elif any(x in service_name for x in ['weight', 'semaglutide', 'tirzepatide']):
        return 'weight_loss'
    else:
        return 'retail'

def process_sales_data(csv_path, db_url):
    # Create database engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Process clients
    clients = {}
    for _, row in df.iterrows():
        if pd.notna(row['Client Name']) and row['Client Name'] not in clients:
            client_id = str(uuid.uuid4())
            clients[row['Client Name']] = {
                'id': client_id,
                'name': row['Client Name'],
                'first_visit_date': row['Sale Date'],
                'last_visit_date': row['Sale Date'],
                'total_visits': 1
            }
        elif pd.notna(row['Client Name']):
            clients[row['Client Name']]['total_visits'] += 1
            if row['Sale Date'] > clients[row['Client Name']]['last_visit_date']:
                clients[row['Client Name']]['last_visit_date'] = row['Sale Date']
    
    # Process staff
    staff = {}
    for _, row in df.iterrows():
        if pd.notna(row['Staff Name']) and row['Staff Name'] not in staff:
            staff_id = str(uuid.uuid4())
            staff[row['Staff Name']] = {
                'id': staff_id,
                'name': row['Staff Name'],
                'role': 'provider'  # Default role
            }
    
    # Process transactions
    transactions = []
    for _, row in df.iterrows():
        if pd.notna(row['Sale id']) and row['Sale id'] != 'All':
            service_category = categorize_service(row['Service Name'] if pd.notna(row['Service Name']) else row['Product Name'] if pd.notna(row['Product Name']) else '')
            
            transaction = {
                'id': row['Sale id'],
                'date': datetime.strptime(row['Sale Date'], '%m/%d/%Y'),
                'location_name': row['Location Name'],
                'client_id': clients[row['Client Name']]['id'] if pd.notna(row['Client Name']) else None,
                'staff_id': staff[row['Staff Name']]['id'] if pd.notna(row['Staff Name']) else None,
                'gross_sales': float(row['Gross Sales']) if pd.notna(row['Gross Sales']) else 0,
                'discount_amount': float(row['Discount Amount']) if pd.notna(row['Discount Amount']) else 0,
                'refund_amount': float(row['Refunds']) if pd.notna(row['Refunds']) else 0,
                'net_sales': float(row['Net Sales']) if pd.notna(row['Net Sales']) else 0,
                'sales_tax': float(row['Sales Tax']) if pd.notna(row['Sales Tax']) else 0,
                'service_category': service_category,
                'is_new_patient': row['Service Name'] == 'NEW PATIENT BOTOX/DYSPORT' if pd.notna(row['Service Name']) else False
            }
            transactions.append(transaction)
    
    # Insert data into database
    with engine.connect() as conn:
        # Insert clients
        conn.execute(Client.__table__.insert(), [client for client in clients.values()])
        
        # Insert staff
        conn.execute(Staff.__table__.insert(), [s for s in staff.values()])
        
        # Insert transactions
        conn.execute(Transaction.__table__.insert(), transactions)
        
        conn.commit()

def process_appointments(csv_path, db_url):
    """
    Process appointment data from CSV
    Note: This is a placeholder - actual implementation would depend on appointment data format
    """
    pass

def process_marketing_metrics(csv_path, db_url):
    """
    Process marketing metrics from CSV
    Note: This is a placeholder - actual implementation would depend on marketing data format
    """
    pass

def process_financial_metrics(csv_path, db_url):
    """
    Process financial metrics from CSV
    Note: This is a placeholder - actual implementation would depend on financial data format
    """
    pass

if __name__ == '__main__':
    # Database connection URL
    db_url = 'sqlite:///rella_analytics.db'  # Replace with your actual database URL
    
    # Process main sales data
    process_sales_data('Detailed Line Item.csv', db_url)
    
    # Process other data sources when available
    # process_appointments('appointments.csv', db_url)
    # process_marketing_metrics('marketing.csv', db_url)
    # process_financial_metrics('financial.csv', db_url) 