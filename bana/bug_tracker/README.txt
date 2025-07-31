# Bug Tracker Django avec HTMX

Un système complet de gestion de bugs développé avec Django et HTMX pour une expérience utilisateur réactive.

## 🚀 Fonctionnalités

### Gestion des Bugs
- ✅ Création, modification et suppression de bugs
- ✅ Classification par statut, priorité et sévérité
- ✅ Assignation aux utilisateurs
- ✅ Suivi des versions affectées et corrigées
- ✅ Gestion des environnements de test

### Interface Réactive avec HTMX
- ✅ Filtrage en temps réel sans rechargement de page
- ✅ Mise à jour instantanée des statuts
- ✅ Assignation rapide via modals
- ✅ Ajout de commentaires en direct
- ✅ Upload de pièces jointes avec feedback

### Système de Commentaires et Pièces Jointes
- ✅ Commentaires avec historique
- ✅ Pièces jointes multiples (images, PDF, logs, etc.)
- ✅ Historique complet des modifications

### Dashboard et Statistiques
- ✅ Vue d'ensemble avec graphiques
- ✅ Statistiques par priorité et composant
- ✅ Actions rapides
- ✅ Activité récente

## 📦 Installation

### Prérequis
```bash
pip install django
pip install faker  # Pour les données de test (optionnel)
```

### Configuration

1. **Créer l'application Django** (si ce n'est pas déjà fait)
```bash
django-admin startproject myproject
cd myproject
python manage.py startapp bug_tracker
```

2. **Ajouter à INSTALLED_APPS dans settings.py**
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bug_tracker',  # ← Ajouter cette ligne
]
```

3. **Créer les migrations**
```bash
python manage.py makemigrations bug_tracker
python manage.py migrate
```

4. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

5. **Charger les données de test** (optionnel)
```bash
python manage.py load_sample_data
```

6. **Lancer le serveur**
```bash
python manage.py runserver
```

## 🎯 URLs et Navigation

- **Dashboard** : `/` - Vue d'ensemble avec statistiques
- **Liste des bugs** : `/bugs/` - Liste paginée avec filtres
- **Nouveau bug** : `/create/` - Formulaire de création
- **Détail bug** : `/<id>/` - Vue détaillée avec commentaires
- **Admin** : `/admin/` - Interface d'administration Django

## 💡 Utilisation

### Créer un Bug
1. Cliquer sur "Nouveau Bug" depuis n'importe quelle page
2. Remplir les informations obligatoires (titre, description, étapes de reproduction)
3. Sélectionner le composant et la version affectée
4. Définir la priorité et la sévérité
5. Optionnel : assigner à un utilisateur

### Filtrer les Bugs
- Utiliser la barre de recherche pour chercher dans le titre/description
- Filtrer par statut, priorité, composant ou assigné
- Les filtres s'appliquent automatiquement via HTMX

### Gérer un Bug
- **Changer le statut** : Menu déroulant dans la liste ou page de détail
- **Assigner** : Bouton "Assigner" ou icône crayon
- **Ajouter commentaires** : Formulaire en bas de la page de détail
- **Joindre fichiers** : Bouton "+" dans la section pièces jointes

### Modaux HTMX
- **Assignation** : Modal pour changer l'assigné rapidement
- **Édition** : Modal pour modifier les informations principales
- **Changement de statut** : Dropdown avec mise à jour instantanée

## 🎨 Personnalisation

### Styles CSS
Les couleurs et styles sont définis dans le template `base.html` :
- Priorités : couleurs selon l'urgence
- Sévérités : codes couleur Bootstrap
- Statuts : badges colorés
- Animations HTMX : transitions fluides

### Modèles de Données
- `Bug` : Modèle principal avec tous les champs
- `Component` : Composants/modules de l'application
- `Version` : Versions logicielles
- `Environment` : Environnements de test
- `BugComment` : Commentaires sur les bugs
- `BugAttachment` : Pièces jointes
- `BugHistory` : Historique des modifications

### Extensions HTMX
- Auto-submit des formulaires de filtre
- Mise à jour partielle des éléments
- Indicateurs de chargement
- Gestion des erreurs

## 🔧 Configuration Avancée

### Pièces Jointes
```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5MB
