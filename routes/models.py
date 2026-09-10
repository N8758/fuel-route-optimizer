from django.db import models


class FuelStation(models.Model):
    truckstop_id = models.BigIntegerField(
        db_index=True
    )

    truckstop_name = models.CharField(
        max_length=255
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        db_index=True
    )

    state = models.CharField(
        max_length=50,
        db_index=True
    )

    rack_id = models.BigIntegerField(
        blank=True,
        null=True
    )

    retail_price = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        db_index=True
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "fuel_stations"
        ordering = ["retail_price"]

    def __str__(self):
        return f"{self.truckstop_name} - ${self.retail_price}"