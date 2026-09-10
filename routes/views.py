import traceback

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import render

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from routes.serializers import (
    RouteRequestSerializer,
    RouteResponseSerializer,
)

from routes.services.geocoding_service import (
    geocode_location,
)

from routes.services.routing_service import (
    get_route,
)

from routes.services.fuel_service import (
    get_stations_near_route,
)

from routes.services.optimization_service import (
    select_fuel_stops,
    calculate_total_cost,
)


def home(request):
    """
    Display the Fuel Route Optimizer frontend.
    """

    return render(
        request,
        "index.html",
    )


class RouteOptimizationView(APIView):
    """
    Calculate a driving route and recommend
    cost-effective fuel stops.
    """

    def post(self, request):

        # ==================================================
        # 1. Validate request
        # ==================================================

        serializer = RouteRequestSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "error": "Invalid request.",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_location = (
            serializer.validated_data["start"]
        )

        finish_location = (
            serializer.validated_data["finish"]
        )

        try:

            # ==================================================
            # 2. Geocode start location
            # ==================================================

            start = geocode_location(
                start_location
            )

            # ==================================================
            # 3. Geocode finish location
            # ==================================================

            finish = geocode_location(
                finish_location
            )

            # ==================================================
            # 4. Calculate driving route
            #
            # One OSRM routing request.
            # ==================================================

            route = get_route(
                start=start,
                finish=finish,
            )

            route_distance = float(
                route["distance_miles"]
            )

            route_geometry = route.get(
                "geometry"
            )

            # ==================================================
            # 5. Validate route geometry
            # ==================================================

            if not route_geometry:

                raise DjangoValidationError(
                    "Routing service did not return "
                    "route geometry."
                )

            route_coordinates = (
                route_geometry.get(
                    "coordinates"
                )
            )

            if not route_coordinates:

                raise DjangoValidationError(
                    "Routing service returned an "
                    "empty route geometry."
                )

            # ==================================================
            # 6. Find fuel stations near the route
            # ==================================================

            candidate_stations = (
                get_stations_near_route(
                    route_coordinates=(
                        route_coordinates
                    ),
                    buffer_miles=15,
                    limit=500,
                )
            )

            # ==================================================
            # 7. Select cost-effective fuel stops
            # ==================================================

            fuel_stops = select_fuel_stops(
                route_distance=route_distance,
                candidate_stations=(
                    candidate_stations
                ),
            )

            # ==================================================
            # 8. Calculate total fuel cost
            # ==================================================

            cost = calculate_total_cost(
                route_distance=route_distance,
                fuel_stops=fuel_stops,
            )

            # ==================================================
            # 9. Build API response
            # ==================================================

            response_data = {
                "start": start_location,

                "finish": finish_location,

                "distance_miles": route[
                    "distance_miles"
                ],

                "duration_minutes": route[
                    "duration_minutes"
                ],

                "total_gallons": cost[
                    "total_gallons"
                ],

                "total_cost": cost[
                    "total_cost"
                ],

                "fuel_stops": fuel_stops,

                "geometry": route_geometry,
            }

            # ==================================================
            # 10. Validate response
            # ==================================================

            response_serializer = (
                RouteResponseSerializer(
                    data=response_data
                )
            )

            response_serializer.is_valid(
                raise_exception=True
            )

            # ==================================================
            # 11. Return response
            # ==================================================

            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK,
            )

        # ==================================================
        # Expected validation/service errors
        # ==================================================

        except DjangoValidationError as error:

            return Response(
                {
                    "error": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValueError as error:

            return Response(
                {
                    "error": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==================================================
        # Unexpected errors
        # ==================================================

        except Exception as error:

            # Print the complete traceback in the
            # Django terminal so we can identify the
            # exact file and line causing the problem.
            traceback.print_exc()

            return Response(
                {
                    "error": (
                        "An unexpected error occurred."
                    ),
                    "details": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HealthCheckView(APIView):
    """
    Simple endpoint used to verify that
    the Django API is running.
    """

    def get(self, request):

        return Response(
            {
                "status": "ok",
                "message": (
                    "Fuel Route Optimizer API "
                    "is running."
                ),
            },
            status=status.HTTP_200_OK,
        )