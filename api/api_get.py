"""
Open Charge Map fetch + transform to our schema.

TODO (api-query / backend): geo accuracy, batching, OCM error taxonomy,
optional response caching.
"""

import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models import ChargePointSummary, LocationInfo, ConnectionInfo
import logging
import traceback


def _to_naive_utc_datetime(value: Optional[object]) -> Optional[datetime]:
    """Store in Postgres TIMESTAMP WITHOUT TIME ZONE as UTC, naive (asyncpg requirement)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    if isinstance(value, str):
        s = value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(s)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    return None


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
            if params:
                safe = {k: v for k, v in params.items() if str(k).lower() != "key"}
                logger.debug("Query params: %s", safe)
            return response.json()
        else:
            error_msg = f"API returned status code {response.status_code}"
            logger.error(error_msg)
            return {"error": error_msg}

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        logger.error("Request failed: %s", error_msg)
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
            last_verified=_to_naive_utc_datetime(raw_point.get("DateLastVerified")),
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
        logger.debug("Starting transformation")

        # Handle if it's a list of charge points
        if isinstance(raw_data, list):
            logger.debug("Processing %s charge points", len(raw_data))
            charge_points = []

            for i, point in enumerate(raw_data):
                simplified_point, error = transform_single_charge_point(point)
                if simplified_point:
                    charge_points.append(simplified_point)
                    logger.debug(
                        "Charge point %s processed (ID: %s)",
                        i + 1,
                        simplified_point.id,
                    )
                else:
                    logger.debug("Failed to process charge point %s: %s", i + 1, error)

            logger.debug("Transformed %s charge points", len(charge_points))
            return charge_points, None

        # Handle if it's a single object
        elif isinstance(raw_data, dict):
            logger.debug("Processing single charge point")
            simplified_point, error = transform_single_charge_point(raw_data)

            if simplified_point:
                logger.debug("Charge point processed (ID: %s)", simplified_point.id)
                return [simplified_point], None
            else:
                return None, error

        else:
            return None, f"Unexpected data type: {type(raw_data)}"

    except Exception as e:
        error_msg = f"Transformation error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return None, error_msg
