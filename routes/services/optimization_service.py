MAX_RANGE_MILES = 500
FUEL_EFFICIENCY_MPG = 10
MAX_FUEL_GALLONS = (
    MAX_RANGE_MILES / FUEL_EFFICIENCY_MPG
)


def calculate_fuel_required(
    distance_miles,
):
    """
    Calculate total fuel required for the route.
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
    Calculate distance from the previous
    route position to a station.
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


def prepare_stations(
    route_distance,
    candidate_stations,
):
    """
    Clean and sort fuel stations.
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

    # Remove duplicate route positions.
    unique_stations = []

    seen_positions = set()

    for station in stations:

        position = round(
            station[
                "distance_from_start"
            ],
            2,
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


def find_best_reachable_station(
    stations,
    current_distance,
    available_range,
    start_index=0,
):
    """
    Find the cheapest reachable station ahead.

    If multiple stations have the same price,
    prefer the station farther along the route.
    """

    reachable_stations = []

    max_reachable_distance = (
        current_distance
        + available_range
    )

    for index in range(
        start_index,
        len(stations),
    ):

        station = stations[index]

        station_distance = float(
            station[
                "distance_from_start"
            ]
        )

        # Station is behind us.
        if station_distance <= current_distance:
            continue

        # Station cannot be reached.
        if (
            station_distance
            > max_reachable_distance
        ):
            break

        reachable_stations.append(
            (
                index,
                station,
            )
        )

    if not reachable_stations:
        return None

    # Cheapest station first.
    #
    # If prices are equal, select the station
    # farther along the route.
    reachable_stations.sort(
        key=lambda item: (
            float(
                item[1][
                    "price_per_gallon"
                ]
            ),
            -float(
                item[1][
                    "distance_from_start"
                ]
            ),
        )
    )

    return reachable_stations[0]


def find_next_cheaper_station(
    current_index,
    stations,
    current_price,
    current_distance,
    current_fuel,
):
    """
    Find the first cheaper station that can
    be reached with the fuel currently available.
    """

    available_range = (
        current_fuel
        * FUEL_EFFICIENCY_MPG
    )

    max_reachable_distance = (
        current_distance
        + available_range
    )

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

        if station_distance > max_reachable_distance:
            break

        station_price = float(
            station[
                "price_per_gallon"
            ]
        )

        if station_price < current_price:
            return index

    return None


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

    The algorithm:

        1. Uses the initial full tank first.
        2. Stops only when another fuel purchase
           is required.
        3. Looks at all reachable stations.
        4. Prefers cheaper stations.
        5. Buys only enough fuel needed to
           continue efficiently.
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
    # Route can be completed with starting tank.
    # --------------------------------------------------

    if route_distance <= MAX_RANGE_MILES:
        return []

    if not stations:
        raise ValueError(
            "No fuel stations are available "
            "near this route."
        )

    # --------------------------------------------------
    # Initial state.
    # --------------------------------------------------

    current_distance = 0.0

    current_fuel = MAX_FUEL_GALLONS

    current_station_index = -1

    selected_stops = []

    # --------------------------------------------------
    # Main optimization loop.
    # --------------------------------------------------

    while current_distance < route_distance:

        remaining_distance = (
            route_distance
            - current_distance
        )

        available_range = (
            current_fuel
            * FUEL_EFFICIENCY_MPG
        )

        # Destination is reachable.
        if remaining_distance <= available_range:
            break

        # --------------------------------------------------
        # Find every station reachable with current fuel.
        # --------------------------------------------------

        reachable = []

        max_reachable_distance = (
            current_distance
            + available_range
        )

        for index in range(
            current_station_index + 1,
            len(stations),
        ):

            station = stations[index]

            station_distance = float(
                station[
                    "distance_from_start"
                ]
            )

            if station_distance <= current_distance:
                continue

            if (
                station_distance
                > max_reachable_distance
            ):
                break

            reachable.append(
                (
                    index,
                    station,
                )
            )

        # --------------------------------------------------
        # No reachable station.
        # --------------------------------------------------

        if not reachable:
            raise ValueError(
                "No fuel station is reachable within "
                "the vehicle's available fuel range. "
                "The route does not have enough "
                "usable fuel-station coverage."
            )

        # --------------------------------------------------
        # Select a station.
        #
        # We choose the cheapest reachable station.
        # If prices are equal, choose the one farther
        # along the route.
        # --------------------------------------------------

        reachable.sort(
            key=lambda item: (
                float(
                    item[1][
                        "price_per_gallon"
                    ]
                ),
                -float(
                    item[1][
                        "distance_from_start"
                    ]
                ),
            )
        )

        station_index, station = (
            reachable[0]
        )

        station_distance = float(
            station[
                "distance_from_start"
            ]
        )

        station_price = float(
            station[
                "price_per_gallon"
            ]
        )

        # --------------------------------------------------
        # Drive to selected station.
        # --------------------------------------------------

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

        current_station_index = (
            station_index
        )

        # --------------------------------------------------
        # Check if destination is now reachable.
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Determine how much fuel to buy.
        # --------------------------------------------------

        # Find a cheaper station ahead that can
        # be reached with a full tank.
        cheaper_index = (
            find_next_cheaper_station(
                current_index=station_index,
                stations=stations,
                current_price=station_price,
                current_distance=current_distance,
                current_fuel=current_fuel,
            )
        )

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

            # No cheaper station nearby.
            #
            # Fill enough to reach either:
            #
            #   - destination
            #   - maximum 500-mile range
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

        # --------------------------------------------------
        # If fuel is still insufficient,
        # fill the tank.
        # --------------------------------------------------

        if (
            (
                current_fuel
                + fuel_to_buy
            )
            * FUEL_EFFICIENCY_MPG
            < distance_needed
        ):

            fuel_to_buy = (
                MAX_FUEL_GALLONS
                - current_fuel
            )

        # --------------------------------------------------
        # Record purchase.
        # --------------------------------------------------

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
                * station_price,
                2,
            )

            selected_stops.append(
                stop
            )

            current_fuel += (
                fuel_to_buy
            )

        # --------------------------------------------------
        # Safety check.
        # --------------------------------------------------

        if current_fuel <= 0:

            raise ValueError(
                "Unable to obtain enough fuel "
                "to continue the route."
            )

    # --------------------------------------------------
    # Final destination validation.
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
    Calculate:

        - total fuel required
        - total additional fuel purchased
        - total money spent on fuel purchases
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