from .models import *
from rest_framework import serializers
from decimal import Decimal
class FuelStationSerializer(serializers.ModelSerializer):
    # """Serializer for fuel station data"""
    class Meta:
        model = FuelStation
        fields = [
            'id',
            'opis_id',
            'name',
            'address',
            'city',
            'state',
            'rack_id',
            'retail_price',
            'latitude',
            'longitude',
        ]
        read_only_fields = ['id']

class FuelStationMinimalSerializer(serializers.ModelSerializer):
    # """Minimal serializer for nested fuel station data"""
    class Meta:
        model = FuelStation
        fields = [
            'id',
            'name',
            'address',
            'city',
            'state',
            'retail_price',
            'latitude',
            'longitude',
        ]

class FuelStopSerializer(serializers.ModelSerializer):
    # """Serializer for fuel stops with nested station info"""
    fuel_station = FuelStationMinimalSerializer(read_only=True)
    
    class Meta:
        model = FuelStop
        fields = [
            'id',
            'stop_order',
            'fuel_station',
            'distance_from_start_miles',
            'gallons_to_fill',
            'cost_at_stop',
            'latitude',
            'longitude',
        ]
        read_only_fields = ['id']


class RouteSerializer(serializers.ModelSerializer):
    # """Serializer for route with fuel stops"""
    fuel_stops = FuelStopSerializer(many=True, read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id',
            'start_location',
            'end_location',
            'total_distance_miles',
            'total_fuel_cost',
            'total_gallons_needed',
            'fuel_efficiency_mpg',
            'tank_range_miles',
            'route_polyline',
            'fuel_stops',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
 

class RouteRequestSerializer(serializers.Serializer):
    # """Serializer for route calculation request"""
    start_location = serializers.CharField(
        max_length=255,
        help_text="Starting location (e.g., 'New York, NY' or 'Times Square, New York')"
    )
    end_location = serializers.CharField(
        max_length=255,
        help_text="Destination location (e.g., 'Los Angeles, CA')"
    )
    fuel_efficiency_mpg = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
        min_value=Decimal('1'),
        max_value=Decimal('100'),
        help_text="Vehicle fuel efficiency in miles per gallon (default: 10)"
    )
    tank_range_miles = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=500.0,
        min_value=Decimal('50'),
        max_value=Decimal('1000'),
        help_text="Maximum driving range on full tank (default: 500)"
    )
    
    def validate(self, data):
        # """Validate that locations are different"""
        if data.get('start_location') == data.get('end_location'):
            raise serializers.ValidationError(
                "Start and end locations must be different"
            )
        return data


class RouteResponseSerializer(serializers.Serializer):
    # """Serializer for route calculation response with map data"""
    route = RouteSerializer()
    map_data = serializers.JSONField(
        help_text="Map route data including polyline and bounds"
    )
    summary = serializers.DictField(
        help_text="Summary statistics of the route"
    )

