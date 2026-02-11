# Fuel-Optimized-Route-API-Project

A Django REST API that:
  - Accepts a start and finish location (within USA).
  - Retrieves the route geometry.
  - Calculates optimal fuel stops based on lowest fuel prices.

Assumes:
- Vehicle range = 500 miles
- Fuel efficiency = 10 miles per gallon

Returns:
- Route map data (JSON)
- Fuel stop locations
- Total fuel cost for the trip

Features
- Route calculation using free routing API (OpenRouteService or Geoapify)
- Fuel optimization based on price data
- Multiple fuel stops if route exceeds 500 miles
- Total fuel cost calculation
- RESTful API built with Django REST Framework
- JSON response ready for map rendering (Leaflet, MapLibre, etc.)

Database Design: ... 
The database stores fuel prices, trips, and fuel stops.

<img width="824" height="637" alt="DB" src="https://github.com/user-attachments/assets/a558c367-f325-4f87-b494-6b02587794d1" />

Tables:
- FuelPrice – Stores fuel price per state
- Trip – Stores start/end locations, distance, total fuel cost
- FuelStop – Stores each stop along the trip, fuel filled, cost
