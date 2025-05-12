import csv
import random
import sqlite3
import os
from datetime import datetime, timedelta

def get_db():
    """Get database connection."""
    db_path = os.path.join('instance', 'rella_analytics.sqlite')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_services_and_products():
    """Get all services and products from the database."""
    db = get_db()
    cursor = db.cursor()
    
    services = []
    products = []
    
    # Get services
    for row in cursor.execute("SELECT name, standard_price FROM services").fetchall():
        services.append({
            'name': row['name'],
            'price': row['standard_price']
        })
    
    # Get products
    for row in cursor.execute("SELECT sku, name, retail_price FROM products WHERE sku IS NOT NULL").fetchall():
        products.append({
            'sku': row['sku'],
            'name': row['name'],
            'price': row['retail_price']
        })
    
    db.close()
    return services, products

def generate_transactions(num_transactions=1000):
    """Generate sample transaction data."""
    # Get services and products
    services, products = get_services_and_products()
    
    # Get locations
    locations = ["Rella Aesthetics - Napa", "Rella Aesthetics"]
    
    # Generate transactions over the last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    transactions = []
    for _ in range(num_transactions):
        # Random date between start and end
        transaction_time = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        
        # Random location
        location = random.choice(locations)
        
        # Random item (70% chance of service, 30% chance of product)
        if random.random() < 0.7:
            item = random.choice(services)
            item_type = 'service'
            item_identifier = item['name']
        else:
            item = random.choice(products)
            item_type = 'product'
            item_identifier = item['sku']
        
        # Random quantity (usually 1 for services, 1-3 for products)
        quantity = 1 if item_type == 'service' else random.randint(1, 3)
        
        # Calculate net price (sometimes with a small discount)
        base_price = item['price']
        discount = random.random() < 0.2  # 20% chance of discount
        discount_amount = base_price * random.uniform(0.05, 0.15) if discount else 0
        net_price = (base_price - discount_amount) * quantity
        
        transactions.append({
            'transaction_time': transaction_time.strftime('%Y-%m-%d %H:%M:%S'),
            'location_name': location,
            'item_type': item_type,
            'item_identifier': item_identifier,
            'quantity': quantity,
            'net_price': round(net_price, 2)
        })
    
    return transactions

def write_transactions_to_csv(transactions, filename='sample_transactions.csv'):
    """Write transactions to a CSV file."""
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'transaction_time',
            'location_name',
            'item_type',
            'item_identifier',
            'quantity',
            'net_price'
        ])
        writer.writeheader()
        writer.writerows(transactions)

def main():
    """Generate sample transaction data and write to CSV."""
    print("Generating sample transactions...")
    transactions = generate_transactions(1000)  # Generate 1000 transactions
    
    print("Writing transactions to CSV...")
    write_transactions_to_csv(transactions)
    
    print("Done! Sample transactions have been written to sample_transactions.csv")

if __name__ == '__main__':
    main() 