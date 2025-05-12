import sqlite3
from flask import g, current_app
import os

# Define the database path using Flask's config

def get_db():
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE')
        if not db_path:
            # Fallback: use instance path
            db_path = getattr(current_app, 'instance_path', None)
            if db_path:
                db_path = os.path.join(db_path, 'rella_analytics.sqlite')
            else:
                db_path = 'rella_analytics.sqlite'
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close() 