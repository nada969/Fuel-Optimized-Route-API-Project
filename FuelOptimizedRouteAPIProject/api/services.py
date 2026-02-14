import requests
from django.conf import settings
from math import radians, sin, cos, sqrt, atan2
from decimal import Decimal
from .models import FuelStation
# from management.commands.openrouteservice import get_route

class RouteService:
    def __init__(self):
        api_key = settings.OPENROUTESERVICE_API_KEY
        if not api_key:
            raise ValueError(
                "OPENROUTESERVICE_API_KEY not configured. "
                "Please add it to your .env file"
            )
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org"
    
    def _is_location_in_usa(self, geocoded_location):
        """Check if a geocoded location is within the USA"""
        
        if not isinstance(geocoded_location, dict):
            raise ValueError(
                f"Invalid geocoded location format (expected dict, got {type(geocoded_location).__name__})"
            )
        
        # Get the display name
        display_name = geocoded_location.get('display_name', '').lower()
        
        # Check properties for country code
        props = geocoded_location.get('properties', {})
        country_code = props.get('country_a', '').upper()
        
        # STRICT CHECK: Must be exactly 'US' or 'USA'
        if country_code in ['US', 'USA']:
            return True
        
        # Fallback: Check display name for USA indicators
        usa_indicators = ['united states', 'usa', 'u.s.']
        
        # Make sure it's NOT other countries
        non_usa_indicators = [
            'united kingdom', 'uk', 'england', 'scotland', 'wales',
            'canada', 'mexico', 'france', 'germany', 'spain', 'italy'
        ]
        
        # If any non-USA country is mentioned, reject
        for indicator in non_usa_indicators:
            if indicator in display_name:
                return False
        
        # Check for USA indicators
        for indicator in usa_indicators:
            if indicator in display_name:
                return True
        
        return False
    def geocode_location(self, location):
        """
        Geocode a location using OpenRouteService ONLY
        
        Args:
            location: String like "New York, NY"
            
        Returns:
            dict: {'lat': float, 'lon': float, 'display_name': str}
        """
        url = f"{self.base_url}/geocode/search"
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        params = {
            'text': location,
            'size': 1,
            # 'boundary.country': 'US'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('features'):
                raise ValueError(f"Location not found: {location}")
            
            feature = data['features'][0]
            coords = feature['geometry']['coordinates']  # [lon, lat]
            
            result = {
                'lon': coords[0],
                'lat': coords[1],
                'display_name': feature['properties'].get('label', location),
                'properties': feature['properties']
            }
            
            # Validate location is in USA
            if not self._is_location_in_usa(result):
                raise ValueError(
                    f"Location '{location}' is not within the USA. "
                    "This API only supports routes within the United States."
                )
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Geocoding failed for '{location}': {str(e)}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid geocoding response for '{location}': {str(e)}")
    
    def calculate_route(self, start_location, end_location):
        """
        Calculate route between two USA locations
        
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
        
        # Validate both locations are in USA
        if not self._is_location_in_usa(start):
            raise ValueError(
                f"Start location is not within the USA. "
                "This API only supports routes within the United States."
            )
        
        if not self._is_location_in_usa(end):
            raise ValueError(
                f"End location is not within the USA. "
                "This API only supports routes within the United States."
            )
        
        # Calculate route using OpenRouteService
        coords = [
            [start['lon'], start['lat']],
            [end['lon'], end['lat']]
        ]
        
        url = f"{self.base_url}/v2/directions/driving-car/geojson"
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'coordinates': coords,
            'instructions': False
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            route = response.json()
            
            feature = route['features'][0]
            properties = feature['properties']
            geometry = feature['geometry']
            
            # Get distance and duration
            distance_meters = properties['summary']['distance']
            duration_seconds = properties['summary']['duration']
            
            # Convert meters to miles
            distance_miles = distance_meters * 0.000621371
            
            return {
                'start': start,
                'end': end,
                'distance_miles': distance_miles,
                'duration_seconds': duration_seconds,
                'geometry': geometry,
                'bbox': route['bbox']
            }
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Route calculation error: {str(e)}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid route response: {str(e)}")
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points (Haversine formula)"""
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
        Simple approach: Use start state + neighboring states
        Only 3 API calls total!
        """
        total_distance = route_data['distance_miles']
        route_coords = route_data['geometry']['coordinates']
        
        num_stops = int(total_distance / tank_range_miles)
        
        if num_stops == 0:
            return []
        
        # Get start and end states (already have from geocoding!)
        start_state = route_data['start']['properties'].get('region_a', '').upper()
        end_state = route_data['end']['properties'].get('region_a', '').upper()
        
        # Get neighboring states
        nearby_states = self._get_nearby_states(start_state, end_state)
        
        # Find cheapest stations in nearby states
        stations_nearby = FuelStation.objects.filter(
            state__in=nearby_states
        ).order_by('retail_price')
        
        if not stations_nearby.exists():
            # Fallback: use all stations
            stations_nearby = FuelStation.objects.all().order_by('retail_price')
        
        if not stations_nearby.exists():
            raise ValueError("No fuel stations found in database")
        
        fuel_stops = []
        gallons_to_fill = tank_range_miles / fuel_efficiency_mpg
        
        # Assign cheapest stations to each stop
        for stop_num in range(1, num_stops + 1):
            target_distance = stop_num * tank_range_miles
            progress = target_distance / total_distance
            coord_index = min(int(progress * len(route_coords)), len(route_coords) - 1)
            target_point = route_coords[coord_index]
            target_lon, target_lat = target_point
            
            # Rotate through cheapest stations
            station_index = (stop_num - 1) % stations_nearby.count()
            best_station = stations_nearby[station_index]
            
            cost = float(best_station.retail_price) * gallons_to_fill
            
            fuel_stops.append({
                'station': best_station,
                'stop_order': stop_num,
                'distance_from_start': target_distance,
                'gallons_to_fill': gallons_to_fill,
                'cost': cost,
                'latitude': target_lat,
                'longitude': target_lon
            })
        
        return fuel_stops


    def _get_nearby_states(self, start_state, end_state):
        """
        Get start state, end state, and their neighboring states
        Simple US geography - no API calls needed!
        """
        # US state neighbors map (simplified)
        state_neighbors = {
            'AL': ['FL', 'GA', 'TN', 'MS'],
            'AK': [],  # No land neighbors
            'AZ': ['CA', 'NV', 'UT', 'NM'],
            'AR': ['MO', 'TN', 'MS', 'LA', 'TX', 'OK'],
            'CA': ['OR', 'NV', 'AZ'],
            'CO': ['WY', 'NE', 'KS', 'OK', 'NM', 'UT'],
            'CT': ['MA', 'RI', 'NY'],
            'DE': ['PA', 'NJ', 'MD'],
            'FL': ['GA', 'AL'],
            'GA': ['FL', 'AL', 'TN', 'NC', 'SC'],
            'HI': [],  # No land neighbors
            'ID': ['MT', 'WY', 'UT', 'NV', 'OR', 'WA'],
            'IL': ['WI', 'IN', 'KY', 'MO', 'IA'],
            'IN': ['MI', 'OH', 'KY', 'IL'],
            'IA': ['MN', 'WI', 'IL', 'MO', 'NE', 'SD'],
            'KS': ['NE', 'MO', 'OK', 'CO'],
            'KY': ['IN', 'OH', 'WV', 'VA', 'TN', 'MO', 'IL'],
            'LA': ['TX', 'AR', 'MS'],
            'ME': ['NH'],
            'MD': ['PA', 'DE', 'VA', 'WV'],
            'MA': ['NH', 'RI', 'CT', 'VT', 'NY'],
            'MI': ['WI', 'IN', 'OH'],
            'MN': ['WI', 'IA', 'SD', 'ND'],
            'MS': ['LA', 'AR', 'TN', 'AL'],
            'MO': ['IA', 'IL', 'KY', 'TN', 'AR', 'OK', 'KS', 'NE'],
            'MT': ['ND', 'SD', 'WY', 'ID'],
            'NE': ['SD', 'IA', 'MO', 'KS', 'CO', 'WY'],
            'NV': ['ID', 'UT', 'AZ', 'CA', 'OR'],
            'NH': ['ME', 'MA', 'VT'],
            'NJ': ['NY', 'DE', 'PA'],
            'NM': ['CO', 'OK', 'TX', 'AZ'],
            'NY': ['VT', 'MA', 'CT', 'NJ', 'PA'],
            'NC': ['VA', 'TN', 'GA', 'SC'],
            'ND': ['MN', 'SD', 'MT'],
            'OH': ['PA', 'WV', 'KY', 'IN', 'MI'],
            'OK': ['KS', 'MO', 'AR', 'TX', 'NM', 'CO'],
            'OR': ['WA', 'ID', 'NV', 'CA'],
            'PA': ['NY', 'NJ', 'DE', 'MD', 'WV', 'OH'],
            'RI': ['MA', 'CT'],
            'SC': ['NC', 'GA'],
            'SD': ['ND', 'MN', 'IA', 'NE', 'WY', 'MT'],
            'TN': ['KY', 'VA', 'NC', 'GA', 'AL', 'MS', 'AR', 'MO'],
            'TX': ['OK', 'AR', 'LA', 'NM'],
            'UT': ['ID', 'WY', 'CO', 'NM', 'AZ', 'NV'],
            'VT': ['NY', 'NH', 'MA'],
            'VA': ['MD', 'WV', 'KY', 'TN', 'NC'],
            'WA': ['ID', 'OR'],
            'WV': ['OH', 'PA', 'MD', 'VA', 'KY'],
            'WI': ['MI', 'IL', 'IA', 'MN'],
            'WY': ['MT', 'SD', 'NE', 'CO', 'UT', 'ID'],
        }
        
        # Start with start and end states
        nearby = set([start_state, end_state])
        
        # Add neighbors of start state
        if start_state in state_neighbors:
            nearby.update(state_neighbors[start_state])
        
        # Add neighbors of end state
        if end_state in state_neighbors:
            nearby.update(state_neighbors[end_state])
        
        # Remove any empty strings
        nearby.discard('')
        
        return list(nearby)