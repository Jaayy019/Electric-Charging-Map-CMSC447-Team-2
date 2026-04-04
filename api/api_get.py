import requests
from typing import Optional, Dict, Any, List
from models import ChargePointSummary, LocationInfo, ConnectionInfo
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_data_from_api(api_key, api_url, user_agent, params: Optional[Dict[str, Any]] = None):
    """
    Makes a GET request to the API with the provided API key.

    Args:
        api_key (str): Your API key
        api_url (str): The API endpoint URL
        user_agent (str): Custom user agent string for your app
        params (dict): Optional query parameters to pass to the API

    Returns:
        dict or list: The JSON response data if successful, error dict otherwise
    """

    headers = {"X-API-Key": api_key, "User-Agent": user_agent}

    try:
        response = requests.get(api_url, headers=headers, params=params)

        if response.status_code == 200:
            logger.info("API request successful")
            print("✓ API request successful")
            if params:
                print(f"  Query params: {params}")
            return response.json()
        else:
            error_msg = f"API returned status code {response.status_code}"
            logger.error(error_msg)
            print(f"✗ {error_msg}")
            return {"error": error_msg}

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        logger.error(f"Request failed: {error_msg}")
        print(f"✗ Request failed: {error_msg}")
        return {"error": error_msg}


def transform_single_charge_point(
    raw_point: Dict[str, Any],
) -> tuple[Optional[ChargePointSummary], Optional[str]]:
    """
    Transform a single raw charge point into simplified schema.

    Args:
        raw_point: Single charge point data from API

    Returns:
        tuple: (ChargePointSummary or None, error message or None)
    """
    try:
        # Extract location info
        address_info = raw_point.get("AddressInfo", {})
        location = LocationInfo(
            address=address_info.get("AddressLine1", ""),
            town=address_info.get("Town", ""),
            postcode=address_info.get("Postcode", ""),
            country=address_info.get("Country", {}).get("Title", ""),
            latitude=float(address_info.get("Latitude", 0.0)),
            longitude=float(address_info.get("Longitude", 0.0)),
            contact_email=address_info.get("ContactEmail"),
        )

        # Extract connection/port info
        connections = []
        for i, conn in enumerate(raw_point.get("Connections", [])):
            try:
                connection = ConnectionInfo(
                    id=conn.get("ID", 0),
                    port_type=conn.get("ConnectionType", {}).get("Title", "Unknown"),
                    power_kw=float(conn.get("PowerKW", 0.0)),
                    voltage=int(conn.get("Voltage", 0)),
                    amps=int(conn.get("Amps", 0)),
                    current_type=conn.get("CurrentType", {}).get("Title", "Unknown"),
                    status=conn.get("StatusType", {}).get("Title", "Unknown"),
                    quantity=int(conn.get("Quantity", 1)),
                )
                connections.append(connection)
            except Exception as e:
                logger.warning(f"Error processing connection {i}: {e}")
                continue

        # Extract usage type info
        usage_type = raw_point.get("UsageType", {})

        # Create simplified charge point
        charge_point = ChargePointSummary(
            id=raw_point.get("ID", 0),
            uuid=raw_point.get("UUID", ""),
            location=location,
            connections=connections,
            number_of_points=raw_point.get("NumberOfPoints", 0),
            price=raw_point.get("UsageCost"),
            availability=raw_point.get("StatusType", {}).get("Title", "Unknown"),
            membership_required=usage_type.get("IsMembershipRequired", False),
            access_key_required=usage_type.get("IsAccessKeyRequired", False),
            operator=raw_point.get("OperatorInfo", {}).get("Title", "Unknown"),
            last_verified=raw_point.get("DateLastVerified"),
        )

        return charge_point, None

    except Exception as e:
        error_msg = f"Transformation error: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return None, error_msg


def transform_to_simplified_schema(
    raw_data: Any,
) -> tuple[Optional[List[ChargePointSummary]], Optional[str]]:
    """
    Transform raw API data (list or single object) into simplified schema.

    Args:
        raw_data: Raw API response (list of charge points or single charge point)

    Returns:
        tuple: (List of ChargePointSummary or None, error message or None)
    """
    try:
        print("\n📊 Starting transformation...")

        # Handle if it's a list of charge points
        if isinstance(raw_data, list):
            print(f"📍 Processing {len(raw_data)} charge points...")
            charge_points = []

            for i, point in enumerate(raw_data):
                simplified_point, error = transform_single_charge_point(point)
                if simplified_point:
                    charge_points.append(simplified_point)
                    print(f"✓ Charge point {i + 1} processed (ID: {simplified_point.id})")
                else:
                    print(f"✗ Failed to process charge point {i + 1}: {error}")

            print(f"✓ Successfully transformed {len(charge_points)} charge points")
            return charge_points, None

        # Handle if it's a single object
        elif isinstance(raw_data, dict):
            print("📍 Processing single charge point...")
            simplified_point, error = transform_single_charge_point(raw_data)

            if simplified_point:
                print(f"✓ Charge point processed (ID: {simplified_point.id})")
                return [simplified_point], None
            else:
                return None, error

        else:
            return None, f"Unexpected data type: {type(raw_data)}"

    except Exception as e:
        error_msg = f"Transformation error: {str(e)}\n{traceback.format_exc()}"
        print(f"✗ {error_msg}")
        logger.error(error_msg)
        return None, error_msg
