import sys
import sqlite3
from pathlib import Path


'''
This is the module that initializes the database. 
It creates the tables and populates them with initial data if necessary with toy data.

input: None
output: None
'''


# Add project root to sys.path so it works when run directly from project root
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
DB_FILE = BASE_DIR / 'data' / 'ev_charging_map.db' #if this file doesn't exist, it will be created

def create_tables():
    #Create the necessary tables if they don't exist
    #stations (station_id, name, latitude, longitude, address, last_fetched, raw_json)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stations (
                station_id INTEGER PRIMARY KEY,
                name TEXT,
                latitude REAL,
                longitude REAL,
                address TEXT,
                last_fetched TEXT,
                raw_json TEXT
            )
        ''')
        print("Tables created successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred while creating tables: {e}")
    finally:
        conn.commit()
        conn.close()


def populate_tables():
    #Populate the tables with initial data if necessary
    return

def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        print("Database file not found. Creating new database...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        conn.commit()
        conn.close()


if __name__ == "__main__":
    init_db()
    create_tables()
    populate_tables()