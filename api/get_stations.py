"""
get_stations.py

Queries the Open Charge Map API for EV charging station data.
API key is required.
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("OCM_API_KEY")
BASE_URL = "https://api.openchargemap.io/v3/poi/"

def get_stations(latitude, longitude, distance=50, limit=100):
    """
    Fetching EV charging station data from the Open Charge Map API.
    Args:
        distance: The distance to search for charging stations, default is 50 miles.
        limit: The maximum number of charging stations to return, default is 100.
        Can be changed / adjusted later if needed.
    """
    params = {
        "key": API_KEY,
        "output": "json",
        "latitude": latitude,
        "longitude": longitude,
        "distance": distance,
        "maxresults": limit,
    }
    
    #Returns the raw JSON response. Wrapped in try/except so the
    #App doesn't crash if the API is down.
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stations: {e}")
        return []
