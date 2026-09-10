from decimal import Decimal


FUEL_EFFICIENCY_MPG = 10


def calculate_gallons(distance_miles):
    """
    Calculate the fuel required for a given distance.

    Vehicle fuel efficiency:
        10 miles per gallon
    """

    if distance_miles < 0:
        raise ValueError(
            "Distance cannot be negative."
        )

    return distance_miles / FUEL_EFFICIENCY_MPG


def calculate_segment_cost(
    distance_miles,
    price_per_gallon,
):
    """
    Calculate the fuel cost for one route segment.
    """

    if distance_miles < 0:
        raise ValueError(
            "Distance cannot be negative."
        )

    if price_per_gallon < 0:
        raise ValueError(
            "Fuel price cannot be negative."
        )

    gallons = calculate_gallons(
        distance_miles
    )

    return gallons * price_per_gallon


def calculate_route_cost(
    route_distance,
    fuel_stops,
):
    """
    Calculate the estimated total fuel cost
    for the complete route.

    Each fuel segment uses the price associated
    with the selected fuel stop.

    Expected fuel stop format:

    {
        "distance_from_start": 250,
        "price_per_gallon": 3.25
    }
    """

    if route_distance < 0:
        raise ValueError(
            "Route distance cannot be negative."
        )

    if route_distance == 0:
        return {
            "total_gallons": 0.0,
            "total_cost": 0.0,
        }

    if not fuel_stops:
        return {
            "total_gallons": round(
                calculate_gallons(route_distance),
                2,
            ),
            "total_cost": None,
        }

    total_cost = Decimal("0")
    previous_distance = 0.0

    for station in fuel_stops:
        station_distance = float(
            station["distance_from_start"]
        )

        price_per_gallon = Decimal(
            str(station["price_per_gallon"])
        )

        segment_distance = (
            station_distance
            - previous_distance
        )

        if segment_distance < 0:
            raise ValueError(
                "Fuel stops must be ordered by "
                "distance from the start."
            )

        segment_cost = calculate_segment_cost(
            segment_distance,
            float(price_per_gallon),
        )

        total_cost += Decimal(
            str(segment_cost)
        )

        previous_distance = station_distance

    # Final segment: last fuel stop -> destination
    final_segment_distance = (
        route_distance
        - previous_distance
    )

    if final_segment_distance < 0:
        raise ValueError(
            "Fuel stop cannot be beyond the route "
            "destination."
        )

    # Use the price of the last selected station
    # for the fuel needed to reach the destination.
    last_price = Decimal(
        str(fuel_stops[-1]["price_per_gallon"])
    )

    final_segment_cost = calculate_segment_cost(
        final_segment_distance,
        float(last_price),
    )

    total_cost += Decimal(
        str(final_segment_cost)
    )

    total_gallons = calculate_gallons(
        route_distance
    )

    return {
        "total_gallons": round(
            total_gallons,
            2,
        ),
        "total_cost": round(
            float(total_cost),
            2,
        ),
    }