from django.db import models
from django.core.validators import MinValueValidator

class FuelStation(models.Model):
    """Fuel station with pricing information from CSV"""
    opis_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=2, db_index=True)
    rack_id = models.IntegerField()
    retail_price = models.DecimalField(
        max_digits=6, 
        decimal_places=5,
        validators=[MinValueValidator(0)]
    )
    
    # Geocoding fields (to be populated via geocoding API)
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        db_index=True
    )
    longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['retail_price']
        indexes = [
            models.Index(fields=['state', 'retail_price']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state} (${self.retail_price})"

class Route(models.Model):
    """Calculated route with fuel stops"""
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)
    
    # Route details
    total_distance_miles = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_fuel_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_gallons_needed = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Route polyline from mapping API
    route_polyline = models.TextField(blank=True)
    
    # Vehicle assumptions
    fuel_efficiency_mpg = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.0
    )
    tank_range_miles = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=500.0
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.start_location} → {self.end_location}"

class FuelStop(models.Model):
    """Optimal fuel stop along a route"""
    route = models.ForeignKey(
        Route, 
        related_name='fuel_stops', 
        on_delete=models.CASCADE
    )
    fuel_station = models.ForeignKey(
        FuelStation, 
        on_delete=models.CASCADE
    )
    
    # Stop details
    stop_order = models.PositiveIntegerField()
    distance_from_start_miles = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    gallons_to_fill = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    cost_at_stop = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Position on route
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)

    class Meta:
        ordering = ['route', 'stop_order']
        unique_together = ['route', 'stop_order']

    def __str__(self):
        return f"Stop #{self.stop_order}: {self.fuel_station.name} (${self.cost_at_stop})"
