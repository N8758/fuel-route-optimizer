from django.urls import path

from routes.views import (
    HealthCheckView,
    RouteOptimizationView,
)


urlpatterns = [
    path(
        "optimize/",
        RouteOptimizationView.as_view(),
        name="route-optimize",
    ),
    path(
        "health/",
        HealthCheckView.as_view(),
        name="health-check",
    ),
]