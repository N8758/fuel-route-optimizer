MAX_RANGE_MILES = 500
FUEL_EFFICIENCY_MPG = 10
MAX_FUEL_GALLONS = (
    MAX_RANGE_MILES / FUEL_EFFICIENCY_MPG
)


def calculate_fuel_required(
    distance_miles,
):
    """
    Calculate the total gallons required
    to drive the given distance.
    """

    if distance_miles < 0:
        raise ValueError(
            "Distance cannot be negative."
        )

    return (
        distance_miles
        / FUEL_EFFICIENCY_MPG
    )


def calculate_fuel_cost(
    gallons,
    price_per_gallon,
):
    """
    Calculate fuel cost.
    """

    if gallons < 0:
        raise ValueError(
            "Fuel gallons cannot be negative."
        )

    if price_per_gallon < 0:
        raise ValueError(
            "Fuel price cannot be negative."
        )

    return (
        gallons
        * price_per_gallon
    )


def calculate_stop_distance(
    previous_distance,
    station_distance,
):
    """
    Calculate distance between the previous
    route position and a fuel station.
    """

    distance = (
        station_distance
        - previous_distance
    )

    if distance < 0:
        raise ValueError(
            "Station distance cannot be before "
            "the previous route position."
        )

    return distance


def find_next_cheaper_station(
    current_index,
    stations,
    current_price,
    current_distance,
):
    """
    Find the first cheaper station ahead that
    can be reached within the vehicle's maximum
    500-mile range.

    Returns the station index or None.
    """

    for index in range(
        current_index + 1,
        len(stations),
    ):

        station = stations[index]

        station_distance = float(
            station[
                "distance_from_start"
            ]
        )

        distance = (
            station_distance
            - current_distance
        )

        # Stations beyond the maximum tank range
        # cannot be considered as the next cheaper
        # station.
        if distance > MAX_RANGE_MILES:
            break

        price = float(
            station[
                "price_per_gallon"
            ]
        )

        if price < current_price:
            return index

    return None


def prepare_stations(
    route_distance,
    candidate_stations,
):
    """
    Clean, validate and sort candidate stations.
    """

    stations = []

    for station in candidate_stations:

        if (
            "distance_from_start"
            not in station
        ):
            continue

        if (
            "price_per_gallon"
            not in station
        ):
            continue

        try:

            distance = float(
                station[
                    "distance_from_start"
                ]
            )

            price = float(
                station[
                    "price_per_gallon"
                ]
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        if distance < 0:
            continue

        if distance > route_distance:
            continue

        if price <= 0:
            continue

        station_copy = dict(
            station
        )

        station_copy[
            "distance_from_start"
        ] = distance

        station_copy[
            "price_per_gallon"
        ] = price

        stations.append(
            station_copy
        )

    stations.sort(
        key=lambda station: (
            station[
                "distance_from_start"
            ],
            station[
                "price_per_gallon"
            ],
        )
    )

    # Remove stations that have essentially
    # the same route position.
    unique_stations = []

    seen_positions = set()

    for station in stations:

        position = round(
            station[
                "distance_from_start"
            ],
            4,
        )

        if position in seen_positions:
            continue

        seen_positions.add(
            position
        )

        unique_stations.append(
            station
        )

    return unique_stations


def select_fuel_stops(
    route_distance,
    candidate_stations,
):
    """
    Select cost-effective fuel stops.

    Vehicle assumptions:

        Maximum range: 500 miles
        Fuel efficiency: 10 MPG
        Maximum tank: 50 gallons
        Starting fuel: FULL TANK

    The vehicle starts with 50 gallons.

    The algorithm tries to:

        1. Avoid unnecessary fuel purchases.
        2. Buy enough fuel to reach a cheaper station
           when one exists within 500 miles.
        3. Otherwise buy enough fuel to safely reach
           the next 500-mile range or destination.
    """

    if route_distance < 0:
        raise ValueError(
            "Route distance cannot be negative."
        )

    if route_distance == 0:
        return []

    stations = prepare_stations(
        route_distance=route_distance,
        candidate_stations=candidate_stations,
    )

    # --------------------------------------------------
    # Routes <= 500 miles
    # --------------------------------------------------
    #
    # The vehicle starts with a full 50-gallon tank,
    # so no additional fuel purchase is required.
    #
    if route_distance <= MAX_RANGE_MILES:

        return []

    # --------------------------------------------------
    # A long route requires fuel stations.
    # --------------------------------------------------

    if not stations:

        raise ValueError(
            "No fuel stations are available "
            "near this route."
        )

    # --------------------------------------------------
    # The first station must be reachable with
    # the starting full tank.
    # --------------------------------------------------

    first_station_distance = float(
        stations[0][
            "distance_from_start"
        ]
    )

    if (
        first_station_distance
        > MAX_RANGE_MILES
    ):

        raise ValueError(
            "No fuel station is reachable within "
            "the vehicle's 500-mile range from "
            "the starting point."
        )

    # --------------------------------------------------
    # Initial vehicle state
    # --------------------------------------------------

    current_distance = 0.0

    # Vehicle starts with a full tank.
    current_fuel = MAX_FUEL_GALLONS

    station_index = 0

    selected_stops = []

    # --------------------------------------------------
    # Main optimization loop
    # --------------------------------------------------

    while current_distance < route_distance:

        # ----------------------------------------------
        # Can we reach the destination with the
        # fuel currently in the tank?
        # ----------------------------------------------

        remaining_distance = (
            route_distance
            - current_distance
        )

        available_range = (
            current_fuel
            * FUEL_EFFICIENCY_MPG
        )

        if remaining_distance <= available_range:

            break

        # ----------------------------------------------
        # Find the next station reachable with the
        # fuel currently in the tank.
        # ----------------------------------------------

        reachable_index = None

        for index in range(
            station_index,
            len(stations),
        ):

            station = stations[index]

            station_distance = float(
                station[
                    "distance_from_start"
                ]
            )

            distance_to_station = (
                station_distance
                - current_distance
            )

            if distance_to_station < 0:
                continue

            if (
                distance_to_station
                <= available_range
            ):

                reachable_index = index
                break

            # Stations are sorted by distance,
            # so once one is too far, later ones
            # will also be too far.
            break

        # ----------------------------------------------
        # No reachable station
        # ----------------------------------------------

        if reachable_index is None:

            raise ValueError(
                "No fuel station is reachable within "
                "the vehicle's available fuel range."
            )

        station = stations[
            reachable_index
        ]

        station_distance = float(
            station[
                "distance_from_start"
            ]
        )

        # ----------------------------------------------
        # Drive from current position to station.
        # ----------------------------------------------

        distance_to_station = (
            station_distance
            - current_distance
        )

        fuel_used = (
            distance_to_station
            / FUEL_EFFICIENCY_MPG
        )

        current_fuel -= fuel_used

        if current_fuel < 0:
            current_fuel = 0.0

        current_distance = (
            station_distance
        )

        station_index = (
            reachable_index + 1
        )

        current_price = float(
            station[
                "price_per_gallon"
            ]
        )

        # ----------------------------------------------
        # Check destination again.
        # ----------------------------------------------

        remaining_distance = (
            route_distance
            - current_distance
        )

        available_range = (
            current_fuel
            * FUEL_EFFICIENCY_MPG
        )

        if remaining_distance <= available_range:

            break

        # ----------------------------------------------
        # Find a cheaper station ahead.
        # ----------------------------------------------

        cheaper_index = (
            find_next_cheaper_station(
                current_index=(
                    reachable_index
                ),
                stations=stations,
                current_price=current_price,
                current_distance=(
                    current_distance
                ),
            )
        )

        # ----------------------------------------------
        # Decide how much fuel to purchase.
        # ----------------------------------------------

        if cheaper_index is not None:

            target_station = stations[
                cheaper_index
            ]

            target_distance = float(
                target_station[
                    "distance_from_start"
                ]
            )

        else:

            # No cheaper station within 500 miles.
            #
            # Fill enough to reach either:
            #
            #   1. Destination
            #   2. Maximum 500-mile range
            #

            target_distance = min(
                route_distance,
                current_distance
                + MAX_RANGE_MILES,
            )

        distance_needed = (
            target_distance
            - current_distance
        )

        fuel_needed = (
            distance_needed
            / FUEL_EFFICIENCY_MPG
        )

        # We only buy the amount we are missing.
        fuel_to_buy = (
            fuel_needed
            - current_fuel
        )

        if fuel_to_buy < 0:
            fuel_to_buy = 0.0

        # Never exceed tank capacity.
        available_capacity = (
            MAX_FUEL_GALLONS
            - current_fuel
        )

        fuel_to_buy = min(
            fuel_to_buy,
            available_capacity,
        )

        # ----------------------------------------------
        # Safety check.
        # ----------------------------------------------

        if (
            current_fuel
            + fuel_to_buy
        ) * FUEL_EFFICIENCY_MPG < (
            distance_needed
        ):

            fuel_to_buy = (
                MAX_FUEL_GALLONS
                - current_fuel
            )

        # ----------------------------------------------
        # Record fuel purchase.
        # ----------------------------------------------

        if fuel_to_buy > 0:

            stop = dict(
                station
            )

            stop[
                "fuel_purchased_gallons"
            ] = round(
                fuel_to_buy,
                2,
            )

            stop[
                "fuel_cost"
            ] = round(
                fuel_to_buy
                * current_price,
                2,
            )

            selected_stops.append(
                stop
            )

            current_fuel += (
                fuel_to_buy
            )

        # ----------------------------------------------
        # Final safety check.
        # ----------------------------------------------

        if current_fuel <= 0:

            raise ValueError(
                "Unable to obtain enough fuel "
                "to continue the route."
            )

    # --------------------------------------------------
    # Final destination validation
    # --------------------------------------------------

    remaining_distance = (
        route_distance
        - current_distance
    )

    available_range = (
        current_fuel
        * FUEL_EFFICIENCY_MPG
    )

    if remaining_distance > available_range:

        raise ValueError(
            "The selected fuel stops cannot "
            "complete the route within the "
            "vehicle's 500-mile range."
        )

    return selected_stops


def calculate_total_cost(
    route_distance,
    fuel_stops,
):
    """
    Calculate total fuel required and total money
    spent on additional fuel purchases.
    """

    if route_distance < 0:

        raise ValueError(
            "Route distance cannot be negative."
        )

    total_gallons_required = (
        calculate_fuel_required(
            route_distance
        )
    )

    total_purchased = 0.0
    total_cost = 0.0

    for station in fuel_stops:

        gallons = float(
            station.get(
                "fuel_purchased_gallons",
                0,
            )
        )

        price = float(
            station[
                "price_per_gallon"
            ]
        )

        if gallons < 0:

            raise ValueError(
                "Fuel purchased cannot be negative."
            )

        if price < 0:

            raise ValueError(
                "Fuel price cannot be negative."
            )

        total_purchased += gallons

        total_cost += (
            gallons
            * price
        )

    return {
        "total_gallons": round(
            total_gallons_required,
            2,
        ),

        "total_cost": round(
            total_cost,
            2,
        ),

        "total_purchased_gallons": round(
            total_purchased,
            2,
        ),
    }