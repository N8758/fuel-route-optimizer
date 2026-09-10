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

PAUSE_BETWEEN_REQUESTS = 1


class Command(BaseCommand):

    help = (
        "Geocode fuel station addresses using "
        "the U.S. Census Geocoder batch API."
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
        # 1. Get stations
        # --------------------------------------------------

        if force:

            stations = list(
                FuelStation.objects.all()
                .order_by("id")
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

        successful = 0

        failed = 0

        # --------------------------------------------------
        # 2. First pass
        #
        # Try the original station address.
        # --------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.NOTICE(
                "PASS 1: Trying exact station addresses..."
            )
        )

        failed_stations = []

        total_batches = (
            (total_stations + batch_size - 1)
            // batch_size
        )

        for batch_number, start_index in enumerate(
            range(
                0,
                total_stations,
                batch_size,
            ),
            start=1,
        ):

            batch = stations[
                start_index:
                start_index + batch_size
            ]

            self.stdout.write(
                self.style.NOTICE(
                    f"Processing batch "
                    f"{batch_number}/{total_batches} "
                    f"({len(batch)} stations)..."
                )
            )

            try:

                results = self.geocode_batch(
                    batch,
                    fallback=False,
                )

            except requests.RequestException as error:

                self.stdout.write(
                    self.style.ERROR(
                        "Census request failed: "
                        f"{error}"
                    )
                )

                failed_stations.extend(
                    batch
                )

                continue

            except Exception as error:

                self.stdout.write(
                    self.style.ERROR(
                        "Unexpected error: "
                        f"{error}"
                    )
                )

                failed_stations.extend(
                    batch
                )

                continue

            batch_successful = 0

            batch_failed = 0

            for station in batch:

                result = results.get(
                    str(station.id)
                )

                if not result:

                    failed_stations.append(
                        station
                    )

                    batch_failed += 1

                    continue

                if self.save_coordinates(
                    station,
                    result,
                ):

                    successful += 1

                    batch_successful += 1

                else:

                    failed_stations.append(
                        station
                    )

                    batch_failed += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Batch {batch_number} complete: "
                    f"{batch_successful} geocoded, "
                    f"{batch_failed} need fallback."
                )
            )

            time.sleep(
                PAUSE_BETWEEN_REQUESTS
            )

        # --------------------------------------------------
        # 3. Second pass
        #
        # For failed highway-style addresses,
        # try City + State.
        # --------------------------------------------------

        fallback_successful = 0

        if failed_stations:

            self.stdout.write("")
            self.stdout.write(
                self.style.NOTICE(
                    "PASS 2: Trying City + State fallback "
                    "for failed stations..."
                )
            )

            fallback_total = len(
                failed_stations
            )

            fallback_batches = (
                (
                    fallback_total
                    + batch_size
                    - 1
                )
                // batch_size
            )

            still_failed = []

            for batch_number, start_index in enumerate(
                range(
                    0,
                    fallback_total,
                    batch_size,
                ),
                start=1,
            ):

                batch = failed_stations[
                    start_index:
                    start_index + batch_size
                ]

                self.stdout.write(
                    self.style.NOTICE(
                        f"Fallback batch "
                        f"{batch_number}/"
                        f"{fallback_batches} "
                        f"({len(batch)} stations)..."
                    )
                )

                try:

                    results = self.geocode_batch(
                        batch,
                        fallback=True,
                    )

                except requests.RequestException as error:

                    self.stdout.write(
                        self.style.ERROR(
                            "Fallback Census request failed: "
                            f"{error}"
                        )
                    )

                    still_failed.extend(
                        batch
                    )

                    continue

                except Exception as error:

                    self.stdout.write(
                        self.style.ERROR(
                            "Unexpected fallback error: "
                            f"{error}"
                        )
                    )

                    still_failed.extend(
                        batch
                    )

                    continue

                batch_successful = 0

                batch_failed = 0

                for station in batch:

                    result = results.get(
                        str(station.id)
                    )

                    if not result:

                        still_failed.append(
                            station
                        )

                        batch_failed += 1

                        continue

                    if self.save_coordinates(
                        station,
                        result,
                    ):

                        successful += 1

                        fallback_successful += 1

                        batch_successful += 1

                    else:

                        still_failed.append(
                            station
                        )

                        batch_failed += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Fallback batch "
                        f"{batch_number} complete: "
                        f"{batch_successful} geocoded, "
                        f"{batch_failed} failed."
                    )
                )

                time.sleep(
                    PAUSE_BETWEEN_REQUESTS
                )

            failed = len(
                still_failed
            )

        else:

            failed = 0

        # --------------------------------------------------
        # 4. Final summary
        # --------------------------------------------------

        remaining = (
            FuelStation.objects.filter(
                latitude__isnull=True
            ).count()
        )

        total_with_coordinates = (
            FuelStation.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False,
            ).count()
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Geocoding process finished."
            )
        )

        self.stdout.write(
            f"Exact address matches: "
            f"{successful - fallback_successful}"
        )

        self.stdout.write(
            f"City/state fallback matches: "
            f"{fallback_successful}"
        )

        self.stdout.write(
            f"Total newly geocoded: "
            f"{successful}"
        )

        self.stdout.write(
            f"Still without coordinates: "
            f"{remaining}"
        )

        self.stdout.write(
            f"Total stations with coordinates: "
            f"{total_with_coordinates}"
        )

    # ======================================================
    # Census batch request
    # ======================================================

    def geocode_batch(
        self,
        stations,
        fallback=False,
    ):
        """
        Send a batch of addresses to Census.

        Normal mode:
            Uses station address + city + state.

        Fallback mode:
            Uses city + state only.

        The fallback is useful for CSV addresses such as:

            I-10, EXIT 858
            I-20, EXIT 235
            SR-375

        where the Census address matcher may not
        understand the highway/exit description.
        """

        csv_buffer = io.StringIO(
            newline=""
        )

        writer = csv.writer(
            csv_buffer
        )

        for station in stations:

            city = (
                station.city or ""
            ).strip()

            state = (
                station.state or ""
            ).strip()

            if fallback:

                # --------------------------------------------------
                # City/state fallback
                #
                # Put the city in the street field and
                # leave the city field empty.
                #
                # This lets Census interpret the input
                # as a city/state location.
                # --------------------------------------------------

                street_address = city

                census_city = ""

            else:

                street_address = (
                    station.address or ""
                ).strip()

                census_city = city

            zip_code = ""

            writer.writerow(
                [
                    station.id,
                    street_address,
                    census_city,
                    state,
                    zip_code,
                ]
            )

        csv_data = (
            csv_buffer.getvalue()
        )

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

        response = requests.post(
            CENSUS_GEOCODER_URL,
            files=files,
            data=data,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        if not response.text.strip():

            raise requests.RequestException(
                "Census Geocoder returned "
                "an empty response."
            )

        return self.parse_response(
            response.text
        )

    # ======================================================
    # Parse Census response
    # ======================================================

    def parse_response(
        self,
        response_text,
    ):
        """
        Parse Census batch response.

        Coordinates are in column 5:

            Longitude,Latitude
        """

        results = {}

        reader = csv.reader(
            io.StringIO(
                response_text
            )
        )

        for row in reader:

            if not row:
                continue

            if len(row) < 6:
                continue

            record_id = (
                row[0].strip()
            )

            if not record_id:
                continue

            match = (
                row[2].strip()
                if len(row) > 2
                else ""
            )

            if not match:
                continue

            if (
                match.lower()
                in {
                    "no_match",
                    "tie",
                }
            ):
                continue

            coordinates = (
                row[5].strip()
            )

            if not coordinates:
                continue

            coordinate_parts = [
                value.strip()
                for value in coordinates.split(
                    ","
                )
            ]

            if len(
                coordinate_parts
            ) != 2:
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

            if not (
                -90
                <= latitude
                <= 90
            ):
                continue

            if not (
                -180
                <= longitude
                <= 180
            ):
                continue

            results[
                record_id
            ] = {
                "latitude": latitude,
                "longitude": longitude,
            }

        return results

    # ======================================================
    # Save coordinates
    # ======================================================

    def save_coordinates(
        self,
        station,
        result,
    ):
        """
        Save latitude and longitude.
        """

        try:

            station.latitude = (
                result["latitude"]
            )

            station.longitude = (
                result["longitude"]
            )

            station.save(
                update_fields=[
                    "latitude",
                    "longitude",
                    "updated_at",
                ]
            )

            return True

        except Exception as error:

            self.stdout.write(
                self.style.WARNING(
                    f"Could not save coordinates "
                    f"for station {station.id}: "
                    f"{error}"
                )
            )

            return False