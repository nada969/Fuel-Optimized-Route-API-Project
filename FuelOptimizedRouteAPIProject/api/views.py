import json
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


@api_view(['POST'])
def calculate_route(request):
    # Calculate optimal route with fuel stops using OpenRouteService
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
                route_polyline=json.dumps(route_data['geometry'])
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
        
        fuel_stops_response = []
        for stop in fuel_stops_data:
            fuel_stops_response.append({
                'location': f"{stop['station'].name}, {stop['station'].city}, {stop['station'].state}",
                'mile_marker': round(stop['distance_from_start'], 0),
                'price_per_gallon': float(stop['station'].retail_price)
            })
        
        # Custom response
        response_data = {
            'route': {
                'distance_miles': round(float(total_distance), 0),
                'start_location': route_data['start']['display_name'],
                'end_location': route_data['end']['display_name'],
                'duration_hours': round(route_data['duration_seconds'] / 3600, 1)
            },
            'fuel_stops': fuel_stops_response,
            'summary': {
                'total_fuel_cost': round(float(total_cost), 2),
                'total_gallons_needed': round(float(total_gallons), 1),
                'num_stops': len(fuel_stops_data),
                'avg_price_per_gallon': round(avg_price, 2)
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