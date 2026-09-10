import csv
import io
import time

import requests

from django.core.management.base import BaseCommand

from routes.models import FuelStation


CENSUS_GEOCODER_URL = (
    "https://geocoding.geo.census.gov/"
    "geocoder/locations/addressbatch"
)

CENSUS_BENCHMARK = "4"

BATCH_SIZE = 1000

REQUEST_TIMEOUT = 120


class Command(BaseCommand):
    help = (
        "Geocode fuel station addresses using the "
        "U.S. Census Geocoder batch API."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=BATCH_SIZE,
            help=(
                "Number of fuel stations to send "
                "in each Census batch."
            ),
        )

        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Geocode all fuel stations again, "
                "including stations that already "
                "have coordinates."
            ),
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        force = options["force"]

        if batch_size <= 0:
            self.stdout.write(
                self.style.ERROR(
                    "Batch size must be greater than zero."
                )
            )
            return

        # --------------------------------------------------
        # 1. Get stations that need geocoding
        # --------------------------------------------------

        if force:
            stations = list(
                FuelStation.objects.all().order_by("id")
            )
        else:
            stations = list(
                FuelStation.objects.filter(
                    latitude__isnull=True
                ).order_by("id")
            )

        total_stations = len(stations)

        if total_stations == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "No fuel stations need geocoding."
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Found {total_stations} fuel stations "
                "to geocode."
            )
        )

        # --------------------------------------------------
        # 2. Counters
        # --------------------------------------------------

        successful = 0
        failed = 0

        # --------------------------------------------------
        # 3. Calculate number of batches
        # --------------------------------------------------

        total_batches = (
            (total_stations + batch_size - 1)
            // batch_size
        )

        # --------------------------------------------------
        # 4. Process batches
        # --------------------------------------------------

        for batch_number, start_index in enumerate(
            range(
                0,
                total_stations,
                batch_size,
            ),
            start=1,
        ):
            batch = stations[
                start_index:start_index + batch_size
            ]

            self.stdout.write("")
            self.stdout.write(
                self.style.NOTICE(
                    f"Processing batch "
                    f"{batch_number}/{total_batches} "
                    f"({len(batch)} stations)..."
                )
            )

            try:
                results = self.geocode_batch(
                    batch
                )

            except requests.RequestException as error:
                self.stdout.write(
                    self.style.ERROR(
                        "Census Geocoder request failed: "
                        f"{error}"
                    )
                )

                failed += len(batch)

                continue

            except Exception as error:
                self.stdout.write(
                    self.style.ERROR(
                        "Unexpected error while processing "
                        f"batch {batch_number}: {error}"
                    )
                )

                failed += len(batch)

                continue

            # --------------------------------------------------
            # 5. Save coordinates
            # --------------------------------------------------

            batch_successful = 0
            batch_failed = 0

            for station in batch:

                result = results.get(
                    str(station.id)
                )

                if not result:
                    batch_failed += 1
                    failed += 1
                    continue

                latitude = result["latitude"]
                longitude = result["longitude"]

                try:
                    station.latitude = latitude
                    station.longitude = longitude

                    station.save(
                        update_fields=[
                            "latitude",
                            "longitude",
                            "updated_at",
                        ]
                    )

                    batch_successful += 1
                    successful += 1

                except Exception as error:
                    batch_failed += 1
                    failed += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not save coordinates "
                            f"for station {station.id}: "
                            f"{error}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Batch {batch_number} complete: "
                    f"{batch_successful} geocoded, "
                    f"{batch_failed} failed."
                )
            )

            # Small pause between requests.
            if (
                start_index + batch_size
                < total_stations
            ):
                time.sleep(1)

        # --------------------------------------------------
        # 6. Final summary
        # --------------------------------------------------

        remaining = FuelStation.objects.filter(
            latitude__isnull=True
        ).count()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Geocoding process finished."
            )
        )

        self.stdout.write(
            f"Successfully geocoded: {successful}"
        )

        self.stdout.write(
            f"Failed/no match: {failed}"
        )

        self.stdout.write(
            f"Still without coordinates: {remaining}"
        )

    # ======================================================
    # Census batch request
    # ======================================================

    def geocode_batch(self, stations):
        """
        Send one batch of fuel station addresses
        to the U.S. Census Geocoder.

        Input format:

            Unique ID,
            Street address,
            City,
            State,
            ZIP
        """

        csv_buffer = io.StringIO(
            newline=""
        )

        writer = csv.writer(
            csv_buffer
        )

        for station in stations:

            street_address = (
                station.address or ""
            ).strip()

            city = (
                station.city or ""
            ).strip()

            state = (
                station.state or ""
            ).strip()

            # ZIP is not available as a separate
            # column in the assessment CSV.
            zip_code = ""

            writer.writerow(
                [
                    station.id,
                    street_address,
                    city,
                    state,
                    zip_code,
                ]
            )

        csv_data = csv_buffer.getvalue()

        files = {
            "addressFile": (
                "fuel_stations.csv",
                csv_data.encode("utf-8"),
                "text/csv",
            )
        }

        data = {
            "benchmark": CENSUS_BENCHMARK,
        }

        self.stdout.write(
            "Sending addresses to Census Geocoder..."
        )

        response = requests.post(
            CENSUS_GEOCODER_URL,
            files=files,
            data=data,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        if not response.text.strip():
            raise requests.RequestException(
                "Census Geocoder returned an empty response."
            )

        return self.parse_response(
            response.text
        )

    # ======================================================
    # Parse Census response
    # ======================================================

    def parse_response(self, response_text):
        """
        Parse the Census batch response.

        Successful Census response looks approximately
        like this:

        ID,
        Input Address,
        Match,
        Match Type,
        Output Address,
        "Longitude,Latitude",
        TigerLine ID,
        Side,
        State,
        County,
        Tract,
        Block

        Example:

        "1",
        "123 MAIN ST, AUSTIN, TX",
        "Match",
        "Exact",
        "123 MAIN ST, AUSTIN, TX",
        "-97.7431,30.2672",
        ...

        Important:
        Longitude and latitude are together in column 5.
        """

        results = {}

        reader = csv.reader(
            io.StringIO(response_text)
        )

        for row in reader:

            if not row:
                continue

            # --------------------------------------------------
            # A successful response normally has at least
            # 6 columns.
            # --------------------------------------------------

            if len(row) < 6:
                continue

            record_id = row[0].strip()

            if not record_id:
                continue

            match = (
                row[2].strip()
                if len(row) > 2
                else ""
            )

            # --------------------------------------------------
            # No match
            # --------------------------------------------------

            if not match:
                continue

            if match.lower() == "no_match":
                continue

            if match.lower() == "tie":
                continue

            # --------------------------------------------------
            # Coordinates are in ONE column:
            #
            # "-76.9274,38.8460"
            # --------------------------------------------------

            coordinates = row[5].strip()

            if not coordinates:
                continue

            coordinate_parts = [
                value.strip()
                for value in coordinates.split(",")
            ]

            if len(coordinate_parts) != 2:
                continue

            try:
                longitude = float(
                    coordinate_parts[0]
                )

                latitude = float(
                    coordinate_parts[1]
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            # --------------------------------------------------
            # Validate coordinates
            # --------------------------------------------------

            if not (
                -90 <= latitude <= 90
            ):
                continue

            if not (
                -180 <= longitude <= 180
            ):
                continue

            results[record_id] = {
                "latitude": latitude,
                "longitude": longitude,
            }

        return results