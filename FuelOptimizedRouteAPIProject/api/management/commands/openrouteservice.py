import requests
import os

def get_route(start, finish):
    api_key = os.getenv("ROUTING_API_KEY")

    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            [start["lon"], start["lat"]],
            [finish["lon"], finish["lat"]]
        ]
    }

    response = requests.post(url, json=body, headers=headers)
    return response.json()
