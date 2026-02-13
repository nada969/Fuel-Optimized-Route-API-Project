  
from django.urls import path
from . import views

urlpatterns = [
    path('fuel-stations/', views.list_fuel_stations, name='list_fuel_stations'),
    path('calculate_route/', views.calculate_route, name='calculate_route'),
    path('get_route/', views.get_route, name='get_route'),
    path('list_routes/', views.list_routes, name='list_routes'),
]