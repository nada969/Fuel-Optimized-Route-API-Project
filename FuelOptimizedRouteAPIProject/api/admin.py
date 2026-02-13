from .serializers import *
from django.contrib import admin


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'retail_price', 'opis_id']
    list_filter = ['state']
    search_fields = ['name', 'city', 'state', 'address']
    ordering = ['retail_price']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = [
        'start_location', 
        'end_location', 
        'total_distance_miles', 
        'total_fuel_cost',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['start_location', 'end_location']
    readonly_fields = ['created_at']


@admin.register(FuelStop)
class FuelStopAdmin(admin.ModelAdmin):
    list_display = [
        'route',
        'stop_order', 
        'fuel_station', 
        'distance_from_start_miles',
        'cost_at_stop'
    ]
    list_filter = ['route']
    search_fields = ['fuel_station__name', 'route__start_location']