import sqlite3
import os
from pprint import pprint

def get_db():
    """Get database connection."""
    db_path = os.path.join('instance', 'rella_analytics.sqlite')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def check_table_contents():
    """Check contents of all tables."""
    db = get_db()
    cursor = db.cursor()
    
    # Get list of tables
    tables = cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """).fetchall()
    
    print("\nDatabase Contents:")
    print("==================")
    
    for table in tables:
        table_name = table['name']
        count = cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()['count']
        print(f"\n{table_name}: {count} rows")
        
        if count > 0:
            # Show first row as example
            row = cursor.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchone()
            print("Example row:")
            # Convert row to dict and truncate long values
            row_dict = {}
            for key in row.keys():
                value = row[key]
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                row_dict[key] = value
            pprint(row_dict)
            
            # For services and products, show a few more rows
            if table_name in ['services', 'products']:
                print("\nFirst 5 rows:")
                rows = cursor.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
                for row in rows:
                    row_dict = {}
                    for key in row.keys():
                        value = row[key]
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        row_dict[key] = value
                    pprint(row_dict)
    
    db.close()

if __name__ == '__main__':
    check_table_contents() 