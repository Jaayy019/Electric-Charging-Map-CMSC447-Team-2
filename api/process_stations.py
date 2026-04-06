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
        # API returns connections per station; missing list is treated as empty (no crash).
        conns = station.get("Connections", [])
        addr = station.get("AddressInfo") or {}

        # Valid connectors only; readable titles, deduped with a set.
        port_types = list(
            {
                c.get("ConnectionType", {}).get("Title", "Unknown")
                for c in conns
                if c.get("ConnectionType")
            }
        )

        # Appending the processed station to the list
        stations.append(
            {
                "id": station.get("ID"),
                "name": addr.get("Title"),
                "lat": addr.get("Latitude"),
                "lng": addr.get("Longitude"),
                "address": addr.get("AddressLine1"),
                "city": addr.get("Town"),
                "state": addr.get("StateOrProvince"),
                "port_types": port_types,
                # Reported point count, else connector count (operators often omit the former).
                "num_points": station.get("NumberOfPoints") or len(conns),
                "is_operational": (station.get("StatusType") or {}).get("IsOperational"),
            }
        )

    return stations
