import sqlite3
import os

def seed_database():
    """Seeds the database with initial data."""
    # Get the database path
    db_path = os.path.join('instance', 'rella_analytics.sqlite')
    
    # Read the SQL file
    with open('seed_data.sql', 'r') as f:
        sql_script = f.read()
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Execute the SQL script
        cursor.executescript(sql_script)
        conn.commit()
        print("Successfully seeded the database!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    seed_database() 