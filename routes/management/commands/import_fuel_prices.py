import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from routes.models import FuelStation


class Command(BaseCommand):
    help = "Import fuel station prices from the assessment CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/fuel-prices-for-be-assessment.csv",
            help="Path to the fuel prices CSV file.",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing fuel station records before importing.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            raise CommandError(
                f"CSV file not found: {file_path}"
            )

        if options["clear"]:
            deleted_count, _ = FuelStation.objects.all().delete()

            self.stdout.write(
                self.style.WARNING(
                    f"Deleted {deleted_count} existing records."
                )
            )

        self.stdout.write(
            self.style.NOTICE(
                f"Reading CSV file: {file_path}"
            )
        )

        stations = []

        try:
            with file_path.open(
                mode="r",
                encoding="utf-8-sig",
                newline=""
            ) as csv_file:

                reader = csv.DictReader(csv_file)

                required_columns = {
                    "OPIS Truckstop ID",
                    "Truckstop Name",
                    "Address",
                    "City",
                    "State",
                    "Rack ID",
                    "Retail Price",
                }

                actual_columns = set(reader.fieldnames or [])

                missing_columns = required_columns - actual_columns

                if missing_columns:
                    raise CommandError(
                        "Missing CSV columns: "
                        + ", ".join(sorted(missing_columns))
                    )

                for row_number, row in enumerate(reader, start=2):
                    try:
                        truckstop_id = int(
                            row["OPIS Truckstop ID"]
                        )

                        rack_id = int(
                            row["Rack ID"]
                        )

                        retail_price = Decimal(
                            row["Retail Price"]
                        )

                        if retail_price <= 0:
                            raise ValueError(
                                "Retail price must be greater than zero."
                            )

                    except (
                        ValueError,
                        TypeError,
                        InvalidOperation,
                    ) as error:

                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipping row {row_number}: {error}"
                            )
                        )

                        continue

                    stations.append(
                        FuelStation(
                            truckstop_id=truckstop_id,
                            truckstop_name=row["Truckstop Name"].strip(),
                            address=row["Address"].strip(),
                            city=row["City"].strip(),
                            state=row["State"].strip(),
                            rack_id=rack_id,
                            retail_price=retail_price,
                        )
                    )

        except UnicodeDecodeError as error:
            raise CommandError(
                f"Could not read CSV file: {error}"
            )

        if not stations:
            raise CommandError(
                "No valid fuel station records found in the CSV."
            )

        self.stdout.write(
            self.style.NOTICE(
                f"Importing {len(stations)} fuel station records..."
            )
        )

        FuelStation.objects.bulk_create(
            stations,
            batch_size=500,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(stations)} fuel stations."
            )
        )