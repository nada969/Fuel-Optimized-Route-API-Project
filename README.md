# Fuel-Optimized-Route-API-Project
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview
This project implements a Django-based RESTful API for optimizing driving routes within the USA. It calculates the optimal route between a start and end location, identifies cost-effective fuel stops based on provided fuel price data, and computes the total fuel cost. The API assumes a vehicle with a maximum range of 500 miles per tank and fuel efficiency of 10 miles per gallon. Routing is handled via a free third-party service (e.g., OpenRouteService or Geoapify) to minimize external calls and ensure quick responses.

## Features
* Input Handling: Accepts start and end locations (e.g., addresses or coordinates) within the USA.
* Route Calculation: Computes the driving route using a single call to a free mapping API.
* Fuel Stop Optimization: Identifies optimal (cost-effective) fuel stops every 500 miles or less along the route, based on proximity and fuel prices from an attached dataset.
* Cost Estimation: Calculates total fuel consumption (in gallons) and cost, assuming 10 mpg efficiency.
* Output: Returns route map data (e.g., polyline or GeoJSON), list of fuel stops, and total estimated fuel cost.
* Efficiency: Designed for quick responses with minimal external API dependencies.

## Assumptions and Constraints
* Vehicle Specs:
  * Maximum range: 500 miles per full tank.
  * Fuel efficiency: 10 miles per gallon.
* Locations: Both start and end must be within the USA.
* Fuel Data: Sourced from the provided Excel file (fuel-prices-for-be-assessment.xlsx). Prices are static; real-time updates are not implemented.
* Routing API: Uses a free service like OpenRouteService or Geoapify for distance, geometry, and mapping. Configure your API key in the environment.
* API Calls: Limited to 1 ideal call (for route fetching); up to 2-3 acceptable for edge cases.

## High-Level Architecture
The API follows a streamlined workflow to ensure performance:
1. User Input: Receive start and end locations via POST request (e.g., JSON payload).
2. Route Fetching: Make a single call to the routing API to get total distance and route geometry (e.g., polyline points).
3. Waypoint Analysis: Divide the route into segments of ≤ 500 miles.
4. Fuel Station Selection:
  * For each segment endpoint, find nearby stations from the fuel dataset (using geocoordinates).
  * Select the cheapest station based on retail price.
5. Cost Calculation:
  * Compute gallons needed: total_distance / 10.
  * Multiply by per-gallon prices at selected stops.
6. Response Generation:
  * Return route map data (e.g., for frontend rendering).
  * List of fuel stops with locations and prices.
  * Total estimated fuel cost.
This flow minimizes computations and external dependencies, leveraging Django’s ORM for efficient station queries (with potential GeoDjango extensions for spatial searches).

## Requirements
* Python 3.10+
* Django 5.0 (latest stable)
* Additional libraries: requests (for API calls), geopy or shapely (for geocoding/distance calculations), pandas or openpyxl (for loading fuel data).
* Database: PostgreSQL recommended (with PostGIS for spatial features).
* Free API Key: From OpenRouteService or Geoapify.

## Installation
1. Clone the repository:
git clone https://github.com/yourusername/fuel-route-optimizer.git
cd fuel-route-optimizer

1. Create a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
1. Install dependencies:
pip install -r requirements.txt
1. Set up environment variables (e.g., in .env):
SECRET_KEY=your_django_secret_key
ROUTING_API_KEY=your_openrouteservice_key
DATABASE_URL=postgres://user:pass@localhost/dbname
1. Load fuel data:
  * Run migrations: python manage.py migrate
  * Import Excel data: python manage.py import_fuel_data path/to/fuel-prices-for-be-assessment.xlsx

2. Start the server:
python manage.py runserver

## Usage
## API Endpoint
* POST /api/route/
  * Request Body (JSON):

{
  "start": "New York, NY",
  "end": "Los Angeles, CA"
}

  * Response (JSON):

{
  "route": {
    "distance_miles": 2790,
    "geometry": "GeoJSON or polyline data"
  },
  "fuel_stops": [
    {
      "location": "Station Name, City, State",
      "mile_marker": 450,
      "price_per_gallon": 3.50
    },
    // Additional stops...
  ],
  "total_cost": 975.50
}

## Example
Using curl:
curl -X POST http://localhost:8000/api/route/ \
-H "Content-Type: application/json" \
-d '{"start": "Chicago, IL", "end": "Miami, FL"}.'

## Development Notes
* Geocoding: Preprocess fuel station addresses to add latitude and longitude (using free tools like Nominatim or the US Census API).
* Optimization: Utilize caching (e.g., Redis) for frequently accessed routes to minimize API calls.
* Testing: Includes unit tests for cost calculations and integration tests for routing.
* Limitations: Static fuel prices; no real-time traffic or dynamic pricing.
  
## Contributing
Contributions are welcome! Please fork the repo, create a feature branch, and submit a pull request. Follow PEP 8 for Python code.
