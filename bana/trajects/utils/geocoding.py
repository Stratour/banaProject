from django.conf import settings
import googlemaps
from django.contrib import messages

# Initialiser le client Google Maps
gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

def get_coordinate(address, country=None, request=None):
    """Vérifie l'adresse et retourne les coordonnées (latitude, longitude)."""
    location = check_address(address, country)
    if location:
        if request:
            messages.success(request, "Adresse trouvée et enregistrée.")
        return True, location
    else:
        if request:
            messages.error(request, "L'adresse n'a pas pu être trouvée. Veuillez vérifier les informations saisies.")
        return False, None

def check_address(address, country=None):
    """Utilise l'API Google Maps pour vérifier et géocoder une adresse."""
    try:
        if country:
            address = f"{address}, {country}"
        
        # Requête à l'API Google Maps
        geocode_result = gmaps.geocode(address)

        # Si une adresse est trouvée
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            return None
    except Exception as e:
        raise Exception(f"Erreur lors de la vérification de l'adresse : {e}")
