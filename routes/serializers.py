from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    """
    Validate the start and finish locations.
    """

    start = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    finish = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )


class FuelStopSerializer(serializers.Serializer):
    """
    Represent one recommended fuel stop.
    """

    id = serializers.IntegerField()

    truckstop_id = serializers.IntegerField()

    name = serializers.CharField()

    address = serializers.CharField(
        allow_blank=True,
        allow_null=True,
    )

    city = serializers.CharField()

    state = serializers.CharField()

    rack_id = serializers.IntegerField(
        allow_null=True,
    )

    price_per_gallon = serializers.FloatField()

    latitude = serializers.FloatField(
        allow_null=True,
    )

    longitude = serializers.FloatField(
        allow_null=True,
    )

    distance_from_start = serializers.FloatField(
        required=False,
    )

    distance_to_route_miles = serializers.FloatField(
        required=False,
    )

    fuel_purchased_gallons = serializers.FloatField(
        required=False,
    )

    fuel_cost = serializers.FloatField(
        required=False,
    )


class RouteResponseSerializer(serializers.Serializer):
    """
    Structure the complete route optimization response.
    """

    start = serializers.CharField()

    finish = serializers.CharField()

    distance_miles = serializers.FloatField()

    duration_minutes = serializers.FloatField()

    total_gallons = serializers.FloatField()

    total_cost = serializers.FloatField(
        allow_null=True,
    )

    fuel_stops = FuelStopSerializer(
        many=True
    )

    geometry = serializers.JSONField(
        allow_null=True,
    )