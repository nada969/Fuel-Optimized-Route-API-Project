  
from django.urls import path
from . import views

urlpatterns = [
    path('fuel-stations/', views.list_fuel_stations, name='list_fuel_stations'),
]