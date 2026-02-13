from django.shortcuts import render
from rest_framework.decorators import api_view
from .models import FuelStation
from .serializers import FuelStationSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

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
