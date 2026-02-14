import requests
import os
from django.conf import settings

def get_route(start, finish):
    api_key = settings.OPENROUTESERVICE_API_KEY

    url = "https://api.openrouteservice.org"
    
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

    return api_key, url, headers, body
