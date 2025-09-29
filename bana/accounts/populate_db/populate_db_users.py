# Ouvrir le shell ou le shell_plus
from django.contrib.auth.models import User

# Liste de données d'utilisateurs fictifs
users_data = [
    {'username': 'john.doe', 'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com'},
    {'username': 'jane.smith', 'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com'},
    {'username': 'peter.jones', 'first_name': 'Peter', 'last_name': 'Jones', 'email': 'peter.jones@example.com'},
    {'username': 'susan.brown', 'first_name': 'Susan', 'last_name': 'Brown', 'email': 'susan.brown@example.com'},
    {'username': 'david.wilson', 'first_name': 'David', 'last_name': 'Wilson', 'email': 'david.wilson@example.com'},
    {'username': 'emily.davis', 'first_name': 'Emily', 'last_name': 'Davis', 'email': 'emily.davis@example.com'},
    {'username': 'mike.miller', 'first_name': 'Mike', 'last_name': 'Miller', 'email': 'mike.miller@example.com'},
    {'username': 'linda.taylor', 'first_name': 'Linda', 'last_name': 'Taylor', 'email': 'linda.taylor@example.com'},
    {'username': 'robert.moore', 'first_name': 'Robert', 'last_name': 'Moore', 'email': 'robert.moore@example.com'},
    {'username': 'nancy.anderson', 'first_name': 'Nancy', 'last_name': 'Anderson', 'email': 'nancy.anderson@example.com'}
]

default_password = 'password123'

# Boucle pour créer et sauvegarder chaque utilisateur
for user_data in users_data:
    prefixed_username = f"lambda_{user_data['username']}"
    try:
        user = User.objects.create_user(
            username=prefixed_username,
            email=user_data['email'],
            password=default_password,
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        print(f"Utilisateur créé : {user.username}")
    except Exception as e:
        print(f"Erreur lors de la création de l'utilisateur {prefixed_username} : {e}")

# Supprimer tous users contenant le terme 'lambda'
User.objects.filter(username__startswith='lambda_').delete()
