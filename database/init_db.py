'''
This is the module that initializes the database. 
It creates the tables and populates them with initial data if necessary with toy data.

input: None
output: None
'''

import sqlite3
import os
# from database import db_utils

#database file path (relative to project root)
DB_FILE = 'data/ev_charging_map.db' #if this file doesn't exist, it will be created

def create_tables():
    #Create the tables if they don't exist
    #Stud 
    return

def populate_tables():
    #Populate the tables with initial data if necessary
    return

def init_db():
    if not os.path.exists(DB_FILE):
        print("Database file not found. Creating new database...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        conn.commit()
        conn.close()


if __name__ == "__main__":
    init_db()
    create_tables()
    populate_tables()