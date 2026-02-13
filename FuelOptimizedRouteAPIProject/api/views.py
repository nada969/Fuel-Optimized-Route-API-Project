from django.shortcuts import render
from rest_framework.decorators import api_view
from .models import *
from .serializers import *
from .services import RouteService
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.db import transaction
from decimal import Decimal


@api_view(['GET'])
def list_fuel_stations(request):
    # """
    # List all fuel stations 
    # GET /api/fuel-stations/
    # """
    queryset = FuelStation.objects.all()
    
    # Filter by state
    state = request.GET.get('state')
    if state:
        queryset = queryset.filter(state__iexact=state)
    
    # Search in name and city
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | 
            Q(city__icontains=search)
        )
    
    # Ordering (default: cheapest first)
    ordering = request.GET.get('ordering', 'retail_price')
    if ordering in ['retail_price', '-retail_price', 'name', 'city', 'state']:
        queryset = queryset.order_by(ordering)
    
    # Limit results
    limit = int(request.GET.get('limit', 20))
    queryset = queryset[:limit]
    
    serializer = FuelStationSerializer(queryset, many=True)
    
    return Response({
        'count': len(serializer.data),
        'results': serializer.data
    })


@api_view(['POST'])
def calculate_route(request):
    """
    Calculate optimal route with fuel stops using OpenRouteService
    
    POST /api/calculate_route/
    
    Request body:
    {
        "start_location": "New York, NY",
        "end_location": "Los Angeles, CA",
        "fuel_efficiency_mpg": 10.0,  
        "tank_range_miles": 500.0     
    }
    
    Response:
    {
        "route": {...},
        "map_data": {...},
        "summary": {...}
    }
    """
    # Validate request
    serializer = RouteRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    start_location = data['start_location']
    end_location = data['end_location']
    fuel_efficiency_mpg = float(data.get('fuel_efficiency_mpg', Decimal('10.0')))
    tank_range_miles = float(data.get('tank_range_miles', Decimal('500.0')))
    
    try:
        # Initialize route service
        route_service = RouteService()
        
        # Step 1: Calculate route
        route_data = route_service.calculate_route(start_location, end_location)
        
        # Step 2: Find optimal fuel stops
        fuel_stops_data = route_service.find_optimal_fuel_stops(
            route_data,
            fuel_efficiency_mpg,
            tank_range_miles
        )
        
        # Step 3: Calculate totals
        total_distance = Decimal(str(route_data['distance_miles']))
        total_gallons = total_distance / Decimal(str(fuel_efficiency_mpg))
        total_cost = sum(stop['cost'] for stop in fuel_stops_data)
        
        # Step 4: Save to database
        with transaction.atomic():
            route = Route.objects.create(
                start_location=route_data['start']['display_name'],
                end_location=route_data['end']['display_name'],
                total_distance_miles=total_distance,
                total_fuel_cost=Decimal(str(total_cost)),
                total_gallons_needed=total_gallons,
                fuel_efficiency_mpg=Decimal(str(fuel_efficiency_mpg)),
                tank_range_miles=Decimal(str(tank_range_miles)),
                route_polyline=str(route_data['geometry'])
            )
            
            # Create fuel stops
            for stop_data in fuel_stops_data:
                FuelStop.objects.create(
                    route=route,
                    fuel_station=stop_data['station'],
                    stop_order=stop_data['stop_order'],
                    distance_from_start_miles=Decimal(str(stop_data['distance_from_start'])),
                    gallons_to_fill=Decimal(str(stop_data['gallons_to_fill'])),
                    cost_at_stop=Decimal(str(stop_data['cost'])),
                    latitude=Decimal(str(stop_data['latitude'])),
                    longitude=Decimal(str(stop_data['longitude']))
                )
        
        # Step 5: Prepare response
        route_serializer = RouteSerializer(route)
        
        avg_price = (
            total_cost / float(total_gallons) 
            if total_gallons > 0 
            else 0
        )
        
        response_data = {
            'route': route_serializer.data,
            'map_data': {
                'geometry': route_data['geometry'],
                'bbox': route_data['bbox'],
                'start_coords': {
                    'lat': route_data['start']['lat'],
                    'lon': route_data['start']['lon']
                },
                'end_coords': {
                    'lat': route_data['end']['lat'],
                    'lon': route_data['end']['lon']
                }
            },
            'summary': {
                'num_stops': len(fuel_stops_data),
                'avg_price_per_gallon': round(avg_price, 2),
                'total_distance_miles': float(total_distance),
                'total_fuel_cost': float(total_cost),
                'total_gallons_needed': float(total_gallons),
                'estimated_duration_hours': round(route_data['duration_seconds'] / 3600, 2)
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_route(request, route_id):
    """
    Get a specific route by ID
    
    GET /api/route/{id}/
    """
    try:
        route = Route.objects.get(id=route_id)
        serializer = RouteSerializer(route)
        return Response(serializer.data)
    except Route.DoesNotExist:
        return Response(
            {'error': 'Route not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def list_routes(request):
    """
    List all calculated routes
    
    GET /api/routes/
    """
    routes = Route.objects.all()[:20]  # Limit to 20 most recent
    serializer = RouteSerializer(routes, many=True)
    return Response({
        'count': len(serializer.data),
        'results': serializer.data
    })