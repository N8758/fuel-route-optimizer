import math

from routes.models import FuelStation


# Maximum distance a fuel station can be away from the route.
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

        if not isinstance(
            coordinate,
            (list, tuple),
        ):
            continue

        if len(coordinate) < 2:
            continue

        try:
            longitude = float(
                coordinate[0]
            )

            latitude = float(
                coordinate[1]
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        valid_coordinates.append(
            (
                longitude,
                latitude,
            )
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
        min_latitude
        + max_latitude
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
            min_latitude
            - latitude_buffer
        ),
        "max_latitude": (
            max_latitude
            + latitude_buffer
        ),
        "min_longitude": (
            min_longitude
            - longitude_buffer
        ),
        "max_longitude": (
            max_longitude
            + longitude_buffer
        ),
    }


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
            distances.append(
                total_distance
            )
            continue

        if len(current) < 2:
            distances.append(
                total_distance
            )
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

        except (
            TypeError,
            ValueError,
        ):
            distances.append(
                total_distance
            )
            continue

        segment_distance = (
            haversine_distance(
                previous_latitude,
                previous_longitude,
                current_latitude,
                current_longitude,
            )
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


def get_stations_near_route(
    route_coordinates,
    buffer_miles=ROUTE_BUFFER_MILES,
    limit=None,
):
    """
    Find fuel stations close to the OSRM route.

    Process:

    1. Clean route coordinates.
    2. Create a bounding box around the route.
    3. Get ALL geocoded stations inside that box.
    4. Calculate the actual distance from each
       station to the route.
    5. Keep stations within the route buffer.
    6. Calculate each station's approximate position
       along the route.
    7. Sort stations by their position on the route.

    This function does not call any routing API.
    """

    if not route_coordinates:
        return []

    # --------------------------------------------------
    # 1. Clean route coordinates
    # --------------------------------------------------

    valid_coordinates = []

    for coordinate in route_coordinates:

        if not isinstance(
            coordinate,
            (list, tuple),
        ):
            continue

        if len(coordinate) < 2:
            continue

        try:
            longitude = float(
                coordinate[0]
            )

            latitude = float(
                coordinate[1]
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        valid_coordinates.append(
            [
                longitude,
                latitude,
            ]
        )

    if len(valid_coordinates) < 2:
        return []

    # --------------------------------------------------
    # 2. Calculate route bounding box
    # --------------------------------------------------

    bounding_box = (
        calculate_route_bounding_box(
            route_coordinates=valid_coordinates,
            buffer_miles=buffer_miles,
        )
    )

    if not bounding_box:
        return []

    # --------------------------------------------------
    # 3. Get stations from database
    # --------------------------------------------------
    #
    # IMPORTANT:
    #
    # We do NOT sort by fuel price here.
    #
    # We first get every geocoded station inside
    # the route bounding box.
    #
    # This prevents a nearby but more expensive
    # station from being removed before we check
    # whether it is actually useful for the route.
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

    if limit is not None:
        queryset = queryset[:limit]

    stations = list(queryset)

    if not stations:
        return []

    # --------------------------------------------------
    # 4. Convert route points
    # --------------------------------------------------

    route_points = []

    for coordinate in valid_coordinates:

        route_points.append(
            (
                coordinate[1],
                coordinate[0],
            )
        )

    if not route_points:
        return []

    # --------------------------------------------------
    # 5. Calculate cumulative route distances
    # --------------------------------------------------

    cumulative_distances = (
        calculate_cumulative_route_distances(
            valid_coordinates
        )
    )

    if len(cumulative_distances) != len(
        valid_coordinates
    ):
        return []

    # --------------------------------------------------
    # 6. Find stations close to route
    # --------------------------------------------------

    candidates = []

    for station in stations:

        if (
            station.latitude is None
            or station.longitude is None
        ):
            continue

        try:
            station_latitude = float(
                station.latitude
            )

            station_longitude = float(
                station.longitude
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        closest_distance = float(
            "inf"
        )

        closest_route_index = None

        # Find the closest route point.
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

        # Station is too far from the route.
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
            "distance_from_start"
        ] = round(
            cumulative_distances[
                closest_route_index
            ],
            2,
        )

        candidates.append(
            station_data
        )

    if not candidates:
        return []

    # --------------------------------------------------
    # 7. Sort by position on route
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

    # --------------------------------------------------
    # 8. Remove stations that are essentially
    #    at the same route position.
    # --------------------------------------------------

    unique_stations = []

    seen_positions = set()

    for station in candidates:

        position = round(
            float(
                station[
                    "distance_from_start"
                ]
            ),
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


def get_fuel_stations(
    states=None,
    limit=100,
):
    """
    Get geocoded fuel stations from the database.
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