# Fuel-Optimized-Route-API-Project
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

##Overview
This project implements a Django-based RESTful API for optimizing driving routes within the USA. It calculates the optimal route between a start and end location, identifies cost-effective fuel stops based on provided fuel price data, and computes the total fuel cost. The API assumes a vehicle with a maximum range of 500 miles per tank and fuel efficiency of 10 miles per gallon. Routing is handled via a free third-party service (e.g., OpenRouteService or Geoapify) to minimize external calls and ensure quick responses.
