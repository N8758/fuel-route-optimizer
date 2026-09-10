import math

from routes.models import FuelStation


# Maximum distance a station can be away from the route.
ROUTE_BUFFER_MILES = 15


def haversine_distance(
    latitude1,
    longitude1,
    latitude2,
    longitude2,
):
    """
    Calculate straight-line distance between
    two latitude/longitude points in miles.
    """

    earth_radius_miles = 3958.8

    lat1 = math.radians(latitude1)
    lat2 = math.radians(latitude2)

    delta_lat = math.radians(
        latitude2 - latitude1
    )

    delta_lon = math.radians(
        longitude2 - longitude1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius_miles * c


def calculate_route_bounding_box(
    route_coordinates,
    buffer_miles=ROUTE_BUFFER_MILES,
):
    """
    Calculate a bounding box around the route.

    OSRM GeoJSON coordinates use:

        [longitude, latitude]
    """

    if not route_coordinates:
        return None

    valid_coordinates = []

    for coordinate in route_coordinates:

        if not isinstance(coordinate, (list, tuple)):
            continue

        if len(coordinate) < 2:
            continue

        try:
            longitude = float(coordinate[0])
            latitude = float(coordinate[1])
        except (TypeError, ValueError):
            continue

        valid_coordinates.append(
            (longitude, latitude)
        )

    if not valid_coordinates:
        return None

    longitudes = [
        coordinate[0]
        for coordinate in valid_coordinates
    ]

    latitudes = [
        coordinate[1]
        for coordinate in valid_coordinates
    ]

    min_latitude = min(latitudes)
    max_latitude = max(latitudes)

    min_longitude = min(longitudes)
    max_longitude = max(longitudes)

    latitude_buffer = (
        buffer_miles / 69.0
    )

    average_latitude = (
        min_latitude + max_latitude
    ) / 2

    longitude_degree_miles = (
        69.0
        * math.cos(
            math.radians(
                average_latitude
            )
        )
    )

    longitude_degree_miles = max(
        longitude_degree_miles,
        1.0,
    )

    longitude_buffer = (
        buffer_miles
        / longitude_degree_miles
    )

    return {
        "min_latitude": (
            min_latitude - latitude_buffer
        ),
        "max_latitude": (
            max_latitude + latitude_buffer
        ),
        "min_longitude": (
            min_longitude - longitude_buffer
        ),
        "max_longitude": (
            max_longitude + longitude_buffer
        ),
    }


def get_stations_near_route(
    route_coordinates,
    buffer_miles=ROUTE_BUFFER_MILES,
    limit=500,
):
    """
    Find fuel stations close to the OSRM route.

    This function does not call any routing API.

    It:
    1. Finds stations inside the route bounding box.
    2. Checks their actual distance from route points.
    3. Keeps stations within the configured buffer.
    4. Calculates their approximate position along
       the route.
    """

    if not route_coordinates:
        return []

    # --------------------------------------------------
    # 1. Clean and validate route coordinates
    # --------------------------------------------------

    valid_coordinates = []

    for coordinate in route_coordinates:

        if not isinstance(coordinate, (list, tuple)):
            continue

        if len(coordinate) < 2:
            continue

        try:
            longitude = float(coordinate[0])
            latitude = float(coordinate[1])
        except (TypeError, ValueError):
            continue

        valid_coordinates.append(
            [longitude, latitude]
        )

    if not valid_coordinates:
        return []

    # --------------------------------------------------
    # 2. Calculate route bounding box
    # --------------------------------------------------

    bounding_box = calculate_route_bounding_box(
        route_coordinates=valid_coordinates,
        buffer_miles=buffer_miles,
    )

    if not bounding_box:
        return []

    # --------------------------------------------------
    # 3. Database filtering
    # --------------------------------------------------

    queryset = FuelStation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        latitude__gte=bounding_box[
            "min_latitude"
        ],
        latitude__lte=bounding_box[
            "max_latitude"
        ],
        longitude__gte=bounding_box[
            "min_longitude"
        ],
        longitude__lte=bounding_box[
            "max_longitude"
        ],
    )

    # IMPORTANT:
    #
    # Do NOT apply [:500] before checking the actual
    # distance to the route.
    #
    # Otherwise, we might accidentally ignore a
    # nearby station just because it is more expensive.
    #
    stations = list(
        queryset.order_by(
            "retail_price"
        )[:limit]
    )

    if not stations:
        return []

    # --------------------------------------------------
    # 4. Convert route coordinates
    # --------------------------------------------------

    route_points = []

    for coordinate in valid_coordinates:

        route_points.append(
            (
                coordinate[1],  # latitude
                coordinate[0],  # longitude
            )
        )

    if not route_points:
        return []

    # --------------------------------------------------
    # 5. Find stations close to route
    # --------------------------------------------------

    candidates = []

    for station in stations:

        if (
            station.latitude is None
            or station.longitude is None
        ):
            continue

        station_latitude = float(
            station.latitude
        )

        station_longitude = float(
            station.longitude
        )

        closest_distance = float("inf")
        closest_route_index = None

        for index, route_point in enumerate(
            route_points
        ):

            distance = haversine_distance(
                station_latitude,
                station_longitude,
                route_point[0],
                route_point[1],
            )

            if distance < closest_distance:

                closest_distance = distance
                closest_route_index = index

        if closest_route_index is None:
            continue

        if closest_distance > buffer_miles:
            continue

        station_data = station_to_dict(
            station
        )

        station_data[
            "distance_to_route_miles"
        ] = round(
            closest_distance,
            2,
        )

        station_data[
            "_route_index"
        ] = closest_route_index

        candidates.append(
            station_data
        )

    if not candidates:
        return []

    # --------------------------------------------------
    # 6. Calculate cumulative route distances
    # --------------------------------------------------

    cumulative_distances = (
        calculate_cumulative_route_distances(
            valid_coordinates
        )
    )

    if not cumulative_distances:
        return []

    # --------------------------------------------------
    # 7. Calculate station distance from start
    # --------------------------------------------------

    for station in candidates:

        route_index = station.get(
            "_route_index"
        )

        if route_index is None:
            continue

        if route_index < 0:
            route_index = 0

        if route_index >= len(
            cumulative_distances
        ):
            route_index = (
                len(cumulative_distances) - 1
            )

        station[
            "distance_from_start"
        ] = round(
            cumulative_distances[
                route_index
            ],
            2,
        )

        station.pop(
            "_route_index",
            None,
        )

    # --------------------------------------------------
    # 8. Sort by route position
    # --------------------------------------------------

    candidates.sort(
        key=lambda station: (
            station.get(
                "distance_from_start",
                float("inf"),
            ),
            station.get(
                "distance_to_route_miles",
                float("inf"),
            ),
            station.get(
                "price_per_gallon",
                float("inf"),
            ),
        )
    )

    return candidates


def calculate_cumulative_route_distances(
    route_coordinates,
):
    """
    Calculate cumulative distance from the beginning
    of the route for every route point.
    """

    if not route_coordinates:
        return []

    distances = [0.0]

    total_distance = 0.0

    for index in range(
        1,
        len(route_coordinates),
    ):

        previous = route_coordinates[
            index - 1
        ]

        current = route_coordinates[
            index
        ]

        if len(previous) < 2:
            continue

        if len(current) < 2:
            continue

        try:
            previous_longitude = float(
                previous[0]
            )

            previous_latitude = float(
                previous[1]
            )

            current_longitude = float(
                current[0]
            )

            current_latitude = float(
                current[1]
            )

        except (TypeError, ValueError):
            continue

        segment_distance = haversine_distance(
            previous_latitude,
            previous_longitude,
            current_latitude,
            current_longitude,
        )

        total_distance += segment_distance

        distances.append(
            total_distance
        )

    return distances


def station_to_dict(station):
    """
    Convert FuelStation model instance
    into a dictionary for the API response.
    """

    return {
        "id": station.id,

        "truckstop_id": (
            station.truckstop_id
        ),

        "name": (
            station.truckstop_name
        ),

        "address": station.address,

        "city": station.city,

        "state": station.state,

        "rack_id": station.rack_id,

        "price_per_gallon": float(
            station.retail_price
        ),

        "latitude": (
            float(station.latitude)
            if station.latitude is not None
            else None
        ),

        "longitude": (
            float(station.longitude)
            if station.longitude is not None
            else None
        ),
    }


def get_fuel_stations(
    states=None,
    limit=100,
):
    """
    Get fuel stations from the database.
    """

    queryset = FuelStation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    )

    if states:
        queryset = queryset.filter(
            state__in=states
        )

    queryset = queryset.order_by(
        "retail_price"
    )

    stations = queryset[:limit]

    return list(stations)


def get_cheapest_stations(
    states=None,
    limit=20,
):
    """
    Return the cheapest fuel stations from
    the selected states that have coordinates.
    """

    return get_fuel_stations(
        states=states,
        limit=limit,
    )