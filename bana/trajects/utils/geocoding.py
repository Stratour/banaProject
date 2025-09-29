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
            suggestions = [item["description"] for item in data.get("predictions", [])]
            return suggestions
        else:
            return f"Erreur API: {data.get('status')}"

    except requests.RequestException as e:
        return f"Erreur de connexion à l'API: {e}"
    
'''
def get_autocomplete_suggestions(query):
    """
    Récupère les suggestions d'adresses via l'API Google Place tout en limitant à la Belgique.
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
            suggestions = []
            for item in data.get("predictions", []):
                description = item.get("description")
                place_id = item.get("place_id")
                print("Description :", description)
                print("Place ID    :", place_id)
                print("----------")
                suggestions.append({
                    "description": description,
                    "place_id": place_id
                })
            return suggestions
        else:
            return f"Erreur API: {data.get('status')}"

    except requests.RequestException as e:
        return f"Erreur de connexion à l'API: {e}"
    

def get_place_details(place_id):
    """
    Récupère les détails d'un lieu via son place_id (latitude, longitude, adresse).
    :param place_id: ID unique du lieu (provenant d'Autocomplete API).
    :return: dict avec 'address', 'lat', 'lng' ou message d'erreur.
    """
    api_key = settings.GOOGLE_MAPS_API_KEY
    base_url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "geometry,formatted_address,name",
        "key": api_key,
        "language": "fr",
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Debug : affiche tout le JSON reçu
        print("===== Place Details API JSON =====")
        import json
        print(json.dumps(data, indent=4, ensure_ascii=False))

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