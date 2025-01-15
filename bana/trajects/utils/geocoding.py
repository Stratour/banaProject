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
