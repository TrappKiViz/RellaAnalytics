import sqlite3
import os

def get_db():
    """Get database connection."""
    db_path = os.path.join('instance', 'rella_analytics.sqlite')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def update_skus():
    """Update products with SKUs."""
    db = get_db()
    cursor = db.cursor()
    
    # Get all products
    products = cursor.execute("SELECT product_id, name FROM products").fetchall()
    
    # Keep track of used SKUs
    used_skus = set()
    
    # Update each product with a SKU based on its name
    for product in products:
        # Create base SKU from name: convert to uppercase, replace spaces with hyphens
        base_sku = product['name'].upper().replace(' ', '-')[:20]  # Limit length to 20 chars
        
        # Ensure unique SKU
        sku = base_sku
        counter = 1
        while sku in used_skus:
            # If duplicate found, append counter and try again
            suffix = f"-{counter}"
            sku = f"{base_sku[:20-len(suffix)]}{suffix}"
            counter += 1
        
        used_skus.add(sku)
        
        # Update the product
        cursor.execute(
            "UPDATE products SET sku = ? WHERE product_id = ?",
            (sku, product['product_id'])
        )
    
    db.commit()
    db.close()
    
    print("Updated SKUs for all products!")

if __name__ == '__main__':
    update_skus() 