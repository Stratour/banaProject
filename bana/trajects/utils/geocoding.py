from django.conf import settings
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

api_key = settings.OPEN_STREET_MAP_API_KEY 
base_url = 'https://api.openrouteservice.org/v2/matrix' # for verifying if the adress is correct 
geolocator = Nominatim(user_agent="BanaCommunity") # for converting adress to Lat Long point

coordinate = {'lat' :"5555",'long' :"66666"} 
payload = {
    "locations": coordinate,
    "metrics": ["distance"],
    "profile": "driving-car",
    "api_key": api_key
}

# Make the API request
response = requests.post(base_url, json=payload)

# Parse the response
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")

# ==================================================================================== #



def check_address(address, country=None):
    try:
        if country:
            location = geolocator.geocode(address, country=country)
        else:
            location = geolocator.geocode(address)
        return location
    except GeocoderTimedOut:
        return None

def address_exists(address, country=None):
    location = check_address(address, country)
    if location:
        return f"Address exists: {location.address}"
    else:
        return "Address does not exist."