import os
import sqlite3
from boulevard_client import make_boulevard_request
from app import BOULEVARD_CATEGORY_MAPPING

def get_boulevard_services():
    """Fetch all services from Boulevard."""
    query = """
    query GetServices {
      services(first: 100) {
        edges {
          node {
            id
            name
            defaultPrice
          }
        }
      }
    }
    """
    response = make_boulevard_request(query)
    if response and 'data' in response and 'services' in response['data']:
        return [edge['node'] for edge in response['data']['services']['edges']]
    return []

def get_boulevard_products():
    """Fetch all products from Boulevard."""
    query = """
    query GetProducts {
      products(first: 100) {
        edges {
          node {
            id
            name
            sku
            unitPrice
          }
        }
      }
    }
    """
    response = make_boulevard_request(query)
    if response and 'data' in response and 'products' in response['data']:
        return [edge['node'] for edge in response['data']['products']['edges']]
    return []

def get_category_id(db, item_name):
    """Get category ID for an item based on our mapping."""
    # Get the uncategorized category ID as fallback
    cursor = db.cursor()
    uncategorized_id = cursor.execute(
        "SELECT category_id FROM treatment_categories WHERE name = 'Uncategorized'"
    ).fetchone()[0]
    
    # Try to get the mapped category
    category_name = BOULEVARD_CATEGORY_MAPPING.get(item_name, "Uncategorized")
    result = cursor.execute(
        "SELECT category_id FROM treatment_categories WHERE name = ?",
        (category_name,)
    ).fetchone()
    
    return result[0] if result else uncategorized_id

def insert_services(db, services):
    """Insert Boulevard services into our database."""
    cursor = db.cursor()
    for service in services:
        try:
            name = service['name']
            price_cents = service.get('defaultPrice', 0)
            price = price_cents / 100.0 if price_cents else 0.0
            category_id = get_category_id(db, name)
            
            cursor.execute("""
                INSERT OR REPLACE INTO services 
                (name, standard_price, category_id)
                VALUES (?, ?, ?)
            """, (name, price, category_id))
            
        except Exception as e:
            print(f"Error inserting service {name}: {e}")
    db.commit()

def insert_products(db, products):
    """Insert Boulevard products into our database."""
    cursor = db.cursor()
    for product in products:
        try:
            name = product['name']
            sku = product.get('sku')
            price_cents = product.get('unitPrice', 0)
            price = price_cents / 100.0 if price_cents else 0.0
            category_id = get_category_id(db, name)
            
            cursor.execute("""
                INSERT OR REPLACE INTO products 
                (name, sku, retail_price, category_id)
                VALUES (?, ?, ?, ?)
            """, (name, sku, price, category_id))
            
        except Exception as e:
            print(f"Error inserting product {name}: {e}")
    db.commit()

def main():
    """Main function to fetch and insert Boulevard data."""
    print("Fetching data from Boulevard...")
    
    # Get the database path
    db_path = os.path.join('instance', 'rella_analytics.sqlite')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    try:
        # Fetch and insert services
        print("Fetching services...")
        services = get_boulevard_services()
        print(f"Found {len(services)} services")
        insert_services(conn, services)
        print("Services inserted successfully")
        
        # Fetch and insert products
        print("Fetching products...")
        products = get_boulevard_products()
        print(f"Found {len(products)} products")
        insert_products(conn, products)
        print("Products inserted successfully")
        
    except Exception as e:
        print(f"Error during data fetch: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    main() 