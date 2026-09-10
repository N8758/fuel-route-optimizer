import os

import requests
from django.core.exceptions import ValidationError
from dotenv import load_dotenv


load_dotenv()


OSRM_BASE_URL = os.getenv(
    "OSRM_BASE_URL",
    "https://router.project-osrm.org",
)


def get_route(start: dict, finish: dict) -> dict:
    """
    Get a driving route between two coordinates using OSRM.

    start:
        {
            "latitude": 40.7128,
            "longitude": -74.0060
        }

    finish:
        {
            "latitude": 41.8781,
            "longitude": -87.6298
        }
    """

    start_latitude = start["latitude"]
    start_longitude = start["longitude"]

    finish_latitude = finish["latitude"]
    finish_longitude = finish["longitude"]

    coordinates = (
        f"{start_longitude},{start_latitude};"
        f"{finish_longitude},{finish_latitude}"
    )

    url = f"{OSRM_BASE_URL}/route/v1/driving/{coordinates}"

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise ValidationError(
            f"Routing service is unavailable: {error}"
        )

    try:
        data = response.json()
    except ValueError:
        raise ValidationError(
            "Routing service returned an invalid response."
        )

    if data.get("code") != "Ok":
        raise ValidationError(
            data.get(
                "message",
                "Could not calculate the route."
            )
        )

    routes = data.get("routes", [])

    if not routes:
        raise ValidationError(
            "No driving route was found."
        )

    route = routes[0]

    distance_miles = route["distance"] / 1609.344
    duration_minutes = route["duration"] / 60

    return {
        "distance_miles": round(distance_miles, 2),
        "duration_minutes": round(duration_minutes, 2),
        "geometry": route.get("geometry"),
    }