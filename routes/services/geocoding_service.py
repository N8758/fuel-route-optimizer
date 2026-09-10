import os

import requests
from django.core.exceptions import ValidationError
from dotenv import load_dotenv


load_dotenv()


NOMINATIM_BASE_URL = os.getenv(
    "NOMINATIM_BASE_URL",
    "https://nominatim.openstreetmap.org"
)

NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    "fuel-route-optimizer/1.0"
)


def geocode_location(location: str) -> dict:
    """
    Convert a human-readable US location into coordinates.

    Example:
        "New York, NY"

    Returns:
        {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "display_name": "New York, New York, United States"
        }
    """

    if not location or not location.strip():
        raise ValidationError("Location cannot be empty.")

    params = {
        "q": location.strip(),
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "us",
    }

    headers = {
        "User-Agent": NOMINATIM_USER_AGENT,
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/search",
            params=params,
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise ValidationError(
            f"Geocoding service is unavailable: {error}"
        )

    try:
        results = response.json()
    except ValueError:
        raise ValidationError(
            "Geocoding service returned an invalid response."
        )

    if not results:
        raise ValidationError(
            f"Could not find location: {location}"
        )

    result = results[0]

    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError):
        raise ValidationError(
            f"Invalid coordinates returned for: {location}"
        )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "display_name": result.get(
            "display_name",
            location
        ),
    }