import openrouteservice
from django.conf import settings
from math import radians, sin, cos, sqrt, atan2
from decimal import Decimal
from .models import FuelStation


class RouteService:
    """Service for calculating routes using OpenRouteService"""
    
    def __init__(self):
        api_key = settings.OPENROUTESERVICE_API_KEY
        if not api_key:
            raise ValueError(
                "OPENROUTESERVICE_API_KEY not configured. "
                "Please add it to your .env file"
            )
        self.client = openrouteservice.Client(key=api_key)
    
    def geocode_location(self, location):
        """
        Geocode a location string to coordinates
        
        Args:
            location: String like "New York, NY" or "Los Angeles, CA"
            
        Returns:
            dict: {'lat': float, 'lon': float, 'display_name': str}
        """
        try:
            # Use ORS geocoding
            result = self.client.pelias_search(text=location, size=1)
            
            if not result['features']:
                raise ValueError(f"Location not found: {location}")
            
            feature = result['features'][0]
            coords = feature['geometry']['coordinates']  # [lon, lat]
            
            return {
                'lon': coords[0],
                'lat': coords[1],
                'display_name': feature['properties'].get('label', location)
            }
        except Exception as e:
            raise ValueError(f"Geocoding error for '{location}': {str(e)}")
    
    def calculate_route(self, start_location, end_location):
        """
        Calculate route between two locations
        
        Args:
            start_location: String or dict with lat/lon
            end_location: String or dict with lat/lon
            
        Returns:
            dict with route information
        """
        # Geocode if strings provided
        if isinstance(start_location, str):
            start = self.geocode_location(start_location)
        else:
            start = start_location
        
        if isinstance(end_location, str):
            end = self.geocode_location(end_location)
        else:
            end = end_location
        
        # Calculate route using ORS
        coords = [
            [start['lon'], start['lat']],
            [end['lon'], end['lat']]
        ]
        
        try:
            route = self.client.directions(
                coordinates=coords,
                profile='driving-car',
                format='geojson',
                units='mi',  # miles
                instructions=False
            )
            
            feature = route['features'][0]
            properties = feature['properties']
            geometry = feature['geometry']
            
            # Convert meters to miles (ORS returns meters despite units parameter)
            distance_miles = properties['summary'][0]['distance'] * 0.000621371
            
            return {
                'start': start,
                'end': end,
                'distance_miles': distance_miles,
                'duration_seconds': properties['summary'][0]['duration'],
                'geometry': geometry,  # GeoJSON LineString
                'bbox': route['bbox']  # Bounding box
            }
        except Exception as e:
            raise ValueError(f"Route calculation error: {str(e)}")
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two points using Haversine formula
        Returns distance in miles
        """
        R = 3959  # Earth's radius in miles
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance
    
    def find_optimal_fuel_stops(self, route_data, fuel_efficiency_mpg=10.0, tank_range_miles=500.0):
        """
        Find optimal fuel stops along the route
        
        Args:
            route_data: Route information from calculate_route()
            fuel_efficiency_mpg: Vehicle fuel efficiency (default: 10 MPG)
            tank_range_miles: Maximum distance on full tank (default: 500 miles)
            
        Returns:
            List of optimal fuel stops with costs
        """
        total_distance = route_data['distance_miles']
        route_coords = route_data['geometry']['coordinates']  # List of [lon, lat]
        
        # Calculate number of stops needed
        num_stops = int(total_distance / tank_range_miles)
        
        if num_stops == 0:
            # Trip is short enough, no stops needed
            return []
        
        # Get all fuel stations with coordinates
        stations = FuelStation.objects.exclude(
            latitude__isnull=True
        ).exclude(
            longitude__isnull=True
        ).order_by('retail_price')
        
        if not stations.exists():
            raise ValueError(
                "No fuel stations with coordinates found. "
                "Please run: python manage.py geocode_stations"
            )
        
        fuel_stops = []
        
        # For each stop, find the cheapest station within range
        for stop_num in range(1, num_stops + 1):
            target_distance = stop_num * tank_range_miles
            
            # Find point on route at target distance
            progress = target_distance / total_distance
            coord_index = min(int(progress * len(route_coords)), len(route_coords) - 1)
            target_point = route_coords[coord_index]
            target_lon, target_lat = target_point
            
            # Find cheapest station within search radius (50 miles)
            search_radius = 50
            best_station = None
            best_cost = float('inf')
            
            for station in stations:
                distance = self.calculate_distance(
                    target_lat, target_lon,
                    float(station.latitude), float(station.longitude)
                )
                
                if distance <= search_radius:
                    # Calculate cost to fill tank
                    gallons_needed = tank_range_miles / fuel_efficiency_mpg
                    cost = float(station.retail_price) * gallons_needed
                    
                    if cost < best_cost:
                        best_cost = cost
                        best_station = station
            
            if best_station:
                gallons_to_fill = tank_range_miles / fuel_efficiency_mpg
                fuel_stops.append({
                    'station': best_station,
                    'stop_order': stop_num,
                    'distance_from_start': target_distance,
                    'gallons_to_fill': gallons_to_fill,
                    'cost': float(best_station.retail_price) * gallons_to_fill,
                    'latitude': float(best_station.latitude),
                    'longitude': float(best_station.longitude)
                })
        
        return fuel_stops