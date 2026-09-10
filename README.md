Yes. 👍 Now we can create **18. `README.md`** for the project.

This README should explain the project, setup, API, architecture, database, fuel optimization logic, and how to run/test it. It should also be suitable for your Spotter assessment GitHub repository.

## `README.md`

Replace your complete `README.md` with this:

````markdown
# Fuel Route Optimizer

A Django REST API that calculates a driving route between two locations in the USA and recommends cost-effective fuel stops along the route.

The application uses OpenStreetMap/OSRM for driving routes and a provided fuel-price CSV dataset for fuel station pricing.

---

## Features

- Accepts start and finish locations in the USA.
- Geocodes locations into latitude/longitude.
- Calculates a driving route using OSRM.
- Uses the actual route geometry to find nearby fuel stations.
- Uses fuel prices from the provided CSV dataset.
- Supports multiple fuel stops.
- Vehicle maximum range: 500 miles.
- Fuel efficiency: 10 MPG.
- Maximum fuel capacity: 50 gallons.
- Calculates total fuel required.
- Calculates estimated additional fuel cost.
- Displays the route on an interactive OpenStreetMap map.
- Displays recommended fuel stations on the map.
- Provides a REST API endpoint for route optimization.
- Includes a simple browser-based frontend.
- Uses PostgreSQL through Supabase.
- Uses one OSRM routing request per optimization request.

---

## Technology Stack

### Backend

- Python
- Django 5.2.6
- Django REST Framework
- PostgreSQL
- Supabase

### External Services

- OSRM - driving route calculation
- OpenStreetMap - map tiles
- Nominatim - location geocoding
- U.S. Census Geocoder - fuel station address geocoding

### Frontend

- HTML
- CSS
- JavaScript
- Leaflet.js
- OpenStreetMap

---

## Project Structure

```text
fuel-route-optimizer/
│
├── manage.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── routes/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   ├── tests.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── routing_service.py
│   │   ├── geocoding_service.py
│   │   ├── fuel_service.py
│   │   ├── optimization_service.py
│   │   └── cost_service.py
│   │
│   └── management/
│       └── commands/
│           ├── __init__.py
│           ├── import_fuel_prices.py
│           └── geocode_fuel_stations.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
└── data/
    └── fuel-prices-for-be-assessment.csv
````

---

# How the Application Works

The application follows this flow:

```text
User
  |
  v
Start + Finish locations
  |
  v
Django REST API
  |
  +--> Geocode Start
  |
  +--> Geocode Finish
  |
  v
OSRM Driving Route
  |
  v
Route Geometry
  |
  v
Find Fuel Stations Near Route
  |
  v
Fuel Stop Optimization
  |
  v
Calculate Fuel Cost
  |
  v
JSON Response
  |
  +--> Route Map
  |
  +--> Fuel Stops
  |
  +--> Total Distance
  |
  +--> Total Fuel
  |
  +--> Total Cost
```

---

# Requirements

Make sure the following are installed:

* Python 3.11+
* PostgreSQL/Supabase database
* Git

The project was developed and tested with:

```text
Python 3.14
Django 5.2.6
```

---

# Installation

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Move into the project:

```bash
cd fuel-route-optimizer
```

---

## 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

---

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-django-secret-key

DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost

DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_SUPABASE_HOST:5432/postgres

OSRM_BASE_URL=https://router.project-osrm.org

NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org

NOMINATIM_USER_AGENT=fuel-route-optimizer/1.0
```

Do not commit the `.env` file to GitHub.

---

# Database Setup

This project uses PostgreSQL hosted by Supabase.

After configuring `DATABASE_URL`, run:

```powershell
python manage.py migrate
```

Check the Django configuration:

```powershell
python manage.py check
```

Expected result:

```text
System check identified no issues (0 silenced).
```

---

# Import Fuel Prices

The assessment provides a CSV containing fuel station information and retail fuel prices.

The CSV is located at:

```text
data/fuel-prices-for-be-assessment.csv
```

Import the data with:

```powershell
python manage.py import_fuel_prices
```

To clear existing fuel station records before importing:

```powershell
python manage.py import_fuel_prices --clear
```

The imported data contains approximately 8,151 fuel station records.

---

# Fuel Station Coordinates

The provided CSV contains addresses but does not provide latitude and longitude for every station.

The project includes a management command to geocode station addresses:

```powershell
python manage.py geocode_fuel_stations
```

The geocoding process uses the U.S. Census Geocoder.

Only successfully geocoded stations receive latitude and longitude.

The route optimization uses stations that have valid coordinates and are geographically close to the calculated driving route.

---

# Run the Application

Start Django:

```powershell
python manage.py runserver
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

Open that URL in a browser.

---

# API

## Optimize Route

### Endpoint

```text
POST /api/routes/optimize/
```

### Request

```json
{
    "start": "New York, NY",
    "finish": "Chicago, IL"
}
```

### Example cURL

```bash
curl -X POST http://127.0.0.1:8000/api/routes/optimize/ \
-H "Content-Type: application/json" \
-d "{\"start\":\"New York, NY\",\"finish\":\"Chicago, IL\"}"
```

---

# Example Response

```json
{
    "start": "New York, NY",
    "finish": "Chicago, IL",
    "distance_miles": 790.57,
    "duration_minutes": 891.0,
    "total_gallons": 79.06,
    "total_cost": 99.49,
    "fuel_stops": [
        {
            "id": 1,
            "truckstop_id": 123,
            "name": "Example Fuel Station",
            "address": "Example Highway",
            "city": "Example City",
            "state": "NY",
            "rack_id": 123,
            "price_per_gallon": 3.10,
            "latitude": 40.0,
            "longitude": -74.0,
            "distance_from_start": 120.0,
            "distance_to_route_miles": 2.1,
            "fuel_purchased_gallons": 20.0,
            "fuel_cost": 62.0
        }
    ],
    "geometry": {
        "type": "LineString",
        "coordinates": []
    }
}
```

The exact fuel stations and prices depend on the imported assessment dataset.

---

# API Health Check

The project also provides a simple health endpoint.

### Endpoint

```text
GET /api/routes/health/
```

Example:

```bash
curl http://127.0.0.1:8000/api/routes/health/
```

Response:

```json
{
    "status": "ok",
    "message": "Fuel Route Optimizer API is running."
}
```

---

# Fuel Optimization Logic

The vehicle assumptions used by the application are:

```text
Maximum range:       500 miles
Fuel efficiency:     10 MPG
Maximum tank size:   50 gallons
```

Therefore:

```text
500 miles / 10 MPG = 50 gallons
```

The application assumes that the vehicle starts the journey with a full tank.

For routes up to 500 miles, no additional fuel purchase is required.

For longer routes, the optimizer evaluates fuel stations along the route.

The algorithm attempts to:

1. Use the available fuel efficiently.
2. Reach a cheaper station when it is within the vehicle's available range.
3. Avoid unnecessary fuel purchases.
4. Purchase enough fuel to continue safely toward the destination.
5. Never exceed the 50-gallon tank capacity.
6. Ensure the destination remains reachable.

---

# Fuel Cost Calculation

Fuel consumption is calculated using:

```text
Fuel Required = Distance / MPG
```

For example:

```text
790.57 miles / 10 MPG
= 79.057 gallons
≈ 79.06 gallons
```

Fuel purchase cost is calculated using:

```text
Fuel Cost = Gallons Purchased × Price Per Gallon
```

The displayed estimated fuel cost represents the additional fuel purchased during the route.

---

# Route Station Selection

The application does not search for the cheapest fuel stations across the entire country.

Instead, it:

1. Calculates the driving route.
2. Uses the route's geographic bounding box.
3. Finds database stations inside that area.
4. Checks their distance from the route.
5. Keeps stations within a 15-mile route buffer.
6. Calculates their approximate position along the route.
7. Passes these stations to the optimization algorithm.

This keeps the fuel station search focused on stations that are relevant to the actual journey.

---

# Routing API Calls

The application is designed to minimize routing API calls.

For a route request:

```text
Start geocoding  -> Nominatim
Finish geocoding -> Nominatim
Driving route    -> OSRM
```

Only one OSRM route request is required for the main route.

Fuel station selection does not make additional routing API calls.

The existing route geometry returned by OSRM is reused to locate fuel stations.

---

# Frontend

The frontend is intentionally simple and lightweight.

It uses:

* HTML
* CSS
* Vanilla JavaScript
* Leaflet

The frontend sends a POST request to:

```text
/api/routes/optimize/
```

The response is then used to display:

* Route distance
* Route duration
* Fuel required
* Estimated fuel cost
* Recommended fuel stops
* Interactive route map
* Fuel station markers

---

# Map

The map uses Leaflet with OpenStreetMap tiles.

The OSRM GeoJSON route geometry is converted into Leaflet coordinates.

OSRM returns coordinates as:

```text
[longitude, latitude]
```

Leaflet uses:

```text
[latitude, longitude]
```

The frontend converts the coordinates before drawing the route.

---

# Error Handling

The API handles:

* Missing start location
* Missing finish location
* Invalid input
* Location not found
* Geocoding service errors
* Routing service errors
* Missing route geometry
* No suitable fuel stations
* Fuel range limitations
* Invalid fuel prices
* Unexpected server errors

Example:

```json
{
    "error": "Could not find location: Example"
}
```

---

# Performance Considerations

The application is designed to avoid unnecessary external API calls.

Important performance decisions include:

* One OSRM request per route.
* Route geometry is reused for fuel station selection.
* Database-level geographic filtering is used before detailed station calculations.
* Fuel stations are filtered by route proximity.
* Bulk database insertion is used when importing CSV data.
* PostgreSQL/Supabase is used instead of storing the full dataset in application memory.

---

# Database Model

The main database model is:

```text
FuelStation
```

Important fields include:

```text
truckstop_id
truckstop_name
address
city
state
rack_id
retail_price
latitude
longitude
```

Latitude and longitude are nullable because not every source address can be successfully geocoded.

---

# Testing

Run Django's test suite with:

```powershell
python manage.py test
```

Run system checks with:

```powershell
python manage.py check
```

For manual API testing, Postman can be used.

Example:

```text
POST http://127.0.0.1:8000/api/routes/optimize/
```

Body:

```json
{
    "start": "New York, NY",
    "finish": "Chicago, IL"
}
```

---

# Postman Testing

Recommended test cases:

### Test 1 - Normal route

```json
{
    "start": "New York, NY",
    "finish": "Chicago, IL"
}
```

Expected:

```text
200 OK
```

---

### Test 2 - Another route

```json
{
    "start": "Los Angeles, CA",
    "finish": "Las Vegas, NV"
}
```

---

### Test 3 - Missing start

```json
{
    "finish": "Chicago, IL"
}
```

Expected:

```text
400 Bad Request
```

---

### Test 4 - Missing finish

```json
{
    "start": "New York, NY"
}
```

Expected:

```text
400 Bad Request
```

---

### Test 5 - Invalid location

```json
{
    "start": "This Location Does Not Exist",
    "finish": "Chicago, IL"
}
```

Expected:

```text
400 Bad Request
```

---

# External Services

This project uses the following public services:

### OSRM

Used for driving route calculation.

```text
https://router.project-osrm.org
```

### OpenStreetMap

Used for map tiles.

```text
https://www.openstreetmap.org
```

### Nominatim

Used to convert user-provided locations into coordinates.

```text
https://nominatim.openstreetmap.org
```

### U.S. Census Geocoder

Used to geocode fuel station addresses.

```text
https://geocoding.geo.census.gov
```

---

# Important Assumptions

The assessment dataset contains fuel station addresses that are not always directly geocodable.

Therefore:

* Only stations with successfully resolved coordinates can be used for route proximity calculations.
* Fuel stations without coordinates are not used by the route optimizer.
* The vehicle starts with a full 50-gallon tank.
* Fuel efficiency is fixed at 10 MPG.
* Maximum vehicle range is 500 miles.
* A fuel station can be considered relevant when it is within approximately 15 miles of the calculated route.
* Fuel station distance along the route is an approximation based on the route geometry.

These assumptions keep the solution deterministic and avoid excessive routing API requests.

---

# Security

The following should never be committed to GitHub:

```text
.env
```

The `.gitignore` file includes:

```text
.env
venv/
__pycache__/
*.pyc
db.sqlite3
staticfiles/
```

Production deployments should also use:

```text
DEBUG=False
```

and a secure Django `SECRET_KEY`.

---

# Running in Development

The complete development workflow is:

```powershell
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python manage.py check

python manage.py migrate

python manage.py import_fuel_prices

python manage.py geocode_fuel_stations

python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

---

# API Endpoint Summary

| Method | Endpoint                | Purpose                        |
| ------ | ----------------------- | ------------------------------ |
| GET    | `/`                     | Frontend                       |
| POST   | `/api/routes/optimize/` | Calculate route and fuel stops |
| GET    | `/api/routes/health/`   | API health check               |

---

# Project Goal

The goal of this project is to provide a simple and efficient route optimization service that combines:

```text
Driving Route
      +
Fuel Station Data
      +
Fuel Prices
      +
Vehicle Constraints
      =
Cost-Effective Fuel Plan
```

The implementation prioritizes a small number of routing API calls, clear separation of backend services, and a simple user interface.

```

