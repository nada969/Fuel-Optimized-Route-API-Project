import csv
from api.models import FuelStation

csv_path = r'D:/SW/BE projects/3- Fuel-Optimized-Route-API-Project/Fuel-Optimized-Route-API-Project/FuelOptimizedRouteAPIProject/fuel-prices-for-be-assessment.csv'

stations = []
with open(csv_path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        stations.append(FuelStation(
            opis_id=int(row['OPIS Truckstop ID']),
            name=row['Truckstop Name'],
            address=row['Address'],
            city=row['City'],
            state=row['State'],
            rack_id=int(row['Rack ID']),
            retail_price=float(row['Retail Price'])
        ))

FuelStation.objects.bulk_create(stations)
print(f"Imported {len(stations)} fuel stations")