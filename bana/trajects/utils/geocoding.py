from django.conf import settings
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut,GeocoderUnavailable
from django.contrib import messages


api_key = settings.OPEN_STREET_MAP_API_KEY
base_url = 'https://api.openrouteservice.org/v2/matrix'
geolocator = Nominatim(user_agent="BanaCommunity")

def get_coordinate(address, country=None, request=None):
    location = check_address(address, country)
    if location:
        if request:
            messages.success(request, "Address found and registered.")
        return True, (location.latitude, location.longitude)
    else:
        if request:
            messages.error(request, "The address could not be found. Please check the input and try again.")
        return False, None


def check_address(address, country=None):
    try:
        if country:
            location = geolocator.geocode(f"{address}, {country}")
        else:
            location = geolocator.geocode(address)
        return location
    except GeocoderTimedOut:
        raise Exception("Geocoding service timeout. Please try again.")

# ======================================================================= #
def matrix(payload):
    response = requests.post(base_url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None


'''
what should look like the coordinate send to the matrix .

# Define the coordinates for your points
coordinates = [
    {"lat": 52.5200, "lng": 13.4050},  # Point A
    {"lat": 52.5205, "lng": 13.4055},  # Point B
    {"lat": 52.5210, "lng": 13.4060}   # Point C
]

# Prepare the payload
payload = {
    "locations": coordinates,
    "metrics": ["distance"],
    "profile": "driving-car",
    "api_key": api_key
}
'''
