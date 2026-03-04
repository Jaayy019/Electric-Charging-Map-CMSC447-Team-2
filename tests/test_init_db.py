import pytest 
import sqlite3
import os
from unittest.mock import patch
from pathlib import Path

from database import init_db

'''
This test file verifies the functionality of the init_db module, 
more specifically the create_tables function.
It uses pytest fixtures to create a temporary database for testing.
'''


@pytest.fixture
def test_db_path(tmp_path):
    #temporary db for testing
    test_db_file = tmp_path / 'test_ev_charging_map.db'
    
    with patch('database.init_db.DB_FILE', test_db_file):
        yield test_db_file #yield so the test can use this path


def test_create_tables_creates_stations_table(test_db_path):
    
    init_db.create_tables()
    assert test_db_path.exists(), "Database file should exist"
    
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    #Query master table to check if stations table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stations'")
    stations_table = cursor.fetchone()
    
    #Assert the table was found
    assert stations_table is not None, "The 'stations' table was not created."
    assert stations_table[0] == 'stations'
    
    #Check if the columns the stations table
    cursor.execute("PRAGMA table_info(stations)")
    columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    #List expected colums and types 
    expected_columns = {
        'station_id': 'INTEGER',
        'name': 'TEXT',
        'latitude': 'REAL',
        'longitude': 'REAL',
        'address': 'TEXT',
        'last_fetched': 'TEXT',
        'raw_json': 'TEXT'
    }

    #Should be the same 
    assert columns == expected_columns, "Table schema does not match expected schema"
    
    conn.close()

