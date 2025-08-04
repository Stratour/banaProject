from django.contrib.auth.models import User
from monapp.models import Profile  # Remplacez 'monapp' par le nom de votre application
import random
import json

# --- Liste de vraies adresses de lieux publics à Bruxelles (au format JSON simulé) ---
adresses_bruxelles = [
    {
        "line1": "Place de la Bourse",
        "city": "Bruxelles",
        "country": "BE",
        "postal_code": "1000"
    },
    {
        "line1": "Grand-Place",
        "city": "Bruxelles",
        "country": "BE",
        "postal_code": "1000"
    },
    {
        "line1": "Rue du Marché aux Herbes 61",
        "city": "Bruxelles",
        "country": "BE",
        "postal_code": "1000"
    },
    {
        "line1": "Avenue Louise 23",
        "city": "Ixelles",
        "country": "BE",
        "postal_code": "1050"
    },
    {
        "line1": "Rue de la Loi 1",
        "city": "Bruxelles",
        "country": "BE",
        "postal_code": "1000"
    },
    {
        "line1": "Chaussée de Wavre 25",
        "city": "Ixelles",
        "country": "BE",
        "postal_code": "1050"
    },
    {
        "line1": "Rue Neuve",
        "city": "Bruxelles",
        "country": "BE",
        "postal_code": "1000"
    },
    {
        "line1": "Chaussée de Charleroi 154",
        "city": "Saint-Gilles",
        "country": "BE",
        "postal_code": "1060"
    },
    {
        "line1": "Avenue des Saisons 123",
        "city": "Ixelles",
        "country": "BE",
        "postal_code": "1050"
    },
    {
        "line1": "Place Flagey",
        "city": "Ixelles",
        "country": "BE",
        "postal_code": "1050"
    },
    {
        "line1": "Place Brugmann 18",
        "city": "Ixelles",
        "country": "BE",
        "postal_code": "1050"
    },
]

# Options pour les champs "service" et "transport_modes"
services = ['parent', 'yaya']
transports = ['voiture', 'transport en commun', 'vélo', 'à pied']


# --- Récupération des utilisateurs et création des profils ---
users = list(User.objects.filter(username__startswith='lambda_'))
random.shuffle(adresses_bruxelles) # Mélanger la liste pour des adresses aléatoires

# Utilisation d'une compréhension de liste pour créer les objets Profile
profiles_to_create = [
    Profile(
        user=user,
        # On choisit une adresse et on la sérialise en JSON
        address=json.dumps(adresses_bruxelles.pop()),
        ci_is_verified=True,
        service=random.choice(services),
        transport_modes=random.sample(transports, random.randint(1, 3)),
        bio=f"Bonjour, je suis {user.first_name}. Je recherche des services de garde d'enfants.",
        phone=f"04{random.randint(70, 79)}{random.randint(100000, 999999)}"
    ) for user in users
]

# Insertion des profils dans la base de données en une seule requête
Profile.objects.bulk_create(profiles_to_create)

# --- Vérification finale ---
print(f"Création de {len(profiles_to_create)} profils terminée.")
for p in Profile.objects.all():
    print(f"Profil pour l'utilisateur '{p.user.username}' créé. Adresse: {json.loads(p.address)['line1']}, {json.loads(p.address)['city']}.")























from django.contrib.auth.models import User
from accounts.models import Profile  # Remplacez 'monapp' par le nom de votre application

import random
import json

# Liste des communes de Bruxelles et des rues fictives
communes_bruxelles = [
    "Anderlecht", "Auderghem", "Berchem-Sainte-Agathe", "Bruxelles-Ville",
    "Etterbeek", "Evere", "Forest", "Ganshoren", "Ixelles",
    "Jette", "Koekelberg", "Molenbeek-Saint-Jean", "Saint-Gilles",
    "Saint-Josse-ten-Noode", "Schaerbeek", "Uccle", "Watermael-Boitsfort",
    "Woluwe-Saint-Lambert", "Woluwe-Saint-Pierre"
]
rues = ["Rue de la Loi", "Avenue Louise", "Rue Neuve", "Chaussée de Charleroi", "Place de la Bourse"]

# Options pour les champs "service" et "transport_modes"
services = ['parent', 'yaya']
transports = ['voiture', 'transport en commun', 'vélo', 'à pied']

# Données d'adresse au format JSON fictif
def get_random_address(communes, rues):
    return json.dumps({
        "line1": f"{random.choice(rues)} {random.randint(1, 150)}",
        "city": random.choice(communes),
        "country": "BE",
        "postal_code": f"1{random.randint(0, 2)}{random.randint(0, 9)}0" # Codes postaux de Bruxelles
    })



# Récupérer les utilisateurs créés précédemment
users_a_peupler = User.objects.filter(username__startswith='lambda_')

# Boucle pour créer un profil pour chaque utilisateur
for user in users_a_peupler:
    # Choix aléatoire pour les champs
    service_aleatoire = random.choice(services)
    transport_mode_aleatoire = random.sample(transports, random.randint(1, 3)) # Choisir entre 1 et 3 modes de transport

    try:
        # Création de l'objet Profile, en le liant à l'utilisateur
        profile = Profile.objects.create(
            user=user,
            address=get_random_address(communes_bruxelles, rues), # Utilisation de l'adresse fictive
            ci_is_verified=True, # Le champ est défini à True comme demandé
            bvm_is_verified=False,
            prfl_is_verified=False,
            service=service_aleatoire,
            transport_modes=transport_mode_aleatoire,
            bio=f"Ceci est la biographie de l'utilisateur {user.first_name} {user.last_name}.",
            phone=f"04{random.randint(70, 79)}{random.randint(100000, 999999)}"
        )
        print(f"Profil créé pour l'utilisateur : {user.username}")
    except Exception as e:
        print(f"Erreur lors de la création du profil pour {user.username} : {e}")

# Vérification (optionnel)
print("\nListe des profils créés et leurs utilisateurs :")
for p in Profile.objects.all():
    print(f"User: {p.user.username}, Service: {p.service}, Adresse: {p.address}, Vérifié: {p.ci_is_verified}")
