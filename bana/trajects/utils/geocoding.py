import json
import requests
from django.conf import settings


def get_autocomplete_suggestions(query):
    """
    Récupère les suggestions d'adresses via l'API Google Geocoding tout en limitant à la Belgique.
    :param query: Texte saisi par l'utilisateur (par exemple, 'Bruxelles').
    :return: Liste des adresses suggérées ou un message d'erreur.
    """
    api_key = settings.GOOGLE_MAPS_API_KEY
    base_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"

    params = {
        "input": query,             # Texte de la recherche
        "key": api_key,             # Clé API Google
        "components": "country:BE", # Restreint les résultats à la Belgique
        "types": "geocode|establishment",
        "language": "fr",
        
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Lève une erreur en cas de réponse HTTP non valide
        data = response.json()

        if data.get("status") == "OK":
            suggestions = [
                {"description": item["description"], "place_id": item["place_id"]}
                for item in data.get("predictions", [])
            ]
            return suggestions
        else:
            return f"Erreur API: {data.get('status')}"

    except requests.RequestException as e:
        return f"Erreur de connexion à l'API: {e}"
    
def get_place_details(place_id):
    api_key = settings.GOOGLE_MAPS_API_KEY
    base_url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "geometry,formatted_address,name",
        "key": api_key,
        "language": "fr",
    }

    print("DEBUG - Place_id : ", place_id)
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK":
            result = data.get("result", {})
            geometry = result.get("geometry", {}).get("location", {})
            return {
                "address": result.get("formatted_address"),
                "lat": geometry.get("lat"),
                "lng": geometry.get("lng"),
                "name": result.get("name"),
            }
        else:
            return {"error": f"Erreur API: {data.get('status')}"}
    except requests.RequestException as e:
        return {"error": f"Erreur de connexion à l'API: {e}"}


'''
def get_autocomplete_suggestions(query):
    api_key = settings.GOOGLE_MAPS_API_KEY
    base_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"

    params = {
        "input": query,
        "key": api_key,
        "components": "country:BE",
        "types": "geocode|establishment",
        "language": "fr",
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK":
            suggestions = []
            for item in data.get("predictions", []):
                suggestions.append({
                    "description": item.get("description"),
                    "place_id": item.get("place_id")
                })
            return suggestions
        else:
            return f"Erreur API: {data.get('status')}"
    except requests.RequestException as e:
        return f"Erreur de connexion à l'API: {e}"

'''