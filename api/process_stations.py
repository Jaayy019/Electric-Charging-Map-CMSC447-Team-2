"""
process_stations.py

Takes the raw JSON returned by the API and normalizes
it into clean, flat dicts that the frontend can directly use.
"""

def process_stations(data):
    """
    Common port_type values returned are generally:
    - "Type 1 (J1772)"   
    - "CCS (Type 1)"       
    - "Tesla (Roadster)" 
    - "Nema 5-15"        
    - "Nema 14-50"       
    """
    stations = []
    for station in data:
        #Api returns a list of connections for each station, but if doesnt have any connections, we accept
        #An empty list of connections instead of crashing
        conns = station.get("Connections", [])
        addr = station.get("AddressInfo") or {}

        #Loop through each connector and process the connection type if it exists and skipp nulls.
        #For each valid connector we grab the readable name, while also removing duplicates by wrapping in a set.
        port_types = list({
            c.get("ConnectionType", {}).get("Title", "Unknown")
            for c in conns if c.get("ConnectionType")
        })

        #Appending the processed station to the list
        stations.append({
            "id":         station.get("ID"),
            "name":       addr.get("Title"),
            "lat":        addr.get("Latitude"),
            "lng":        addr.get("Longitude"),
            "address":    addr.get("AddressLine1"),
            "city":       addr.get("Town"),
            "state":      addr.get("StateOrProvince"),
            "port_types": port_types,
            #Number of charging points available at the station if they provide it otherwise count how many connectors are listed.
            #Since station operators don't always report it. Honestly might be pointless?
            "num_points": station.get("NumberOfPoints") or len(conns),
            "is_operational": (station.get("StatusType") or {}).get("IsOperational"),
        })

    return stations