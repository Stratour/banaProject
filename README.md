# BanaCommunity

Plateforme communautaire Django pour le covoiturage et la garde d'enfants.

## Prérequis

- Python 3.12+
- Django 5.1.4
- Node.js et npm
- PostgreSQL avec PostGIS

## Installation (développement)

1. **Cloner le dépôt et créer une branche**

   ```bash
   git clone git@github.com:Stratour/banaProject.git
   cd banaProject
   git checkout -b your-branch-name
   ```

2. **Créer et activer le virtualenv**

   ```bash
   python3 -m venv env
   source env/bin/activate        # Unix/macOS
   env\Scripts\activate           # Windows
   ```

3. **Installer les dépendances Python**

   ```sh
   pip install -r requirements.txt
   ```

4. **Configurer le fichier `.env`**

   ```sh
   cp bana/.env.example bana/.env
   # Remplir les variables dans bana/.env
   ```

5. **Appliquer les migrations et lancer le serveur**

   ```sh
   cd bana
   python manage.py migrate
   python manage.py runserver
   ```

6. **Tailwind CSS** (dans un second terminal)

   ```sh
   cd bana
   python manage.py tailwind start
   # Si les node_modules sont manquants :
   cd theme/static_src && npm install && npm install cross-env
   ```

## Architecture serveur (production)

La production utilise deux dossiers séparés pour isoler le code de dev du code servi :

```
/home/rootkitbana/banaProject/       ← développement (branche active)
/home/rootkitbana/banaProject-prod/  ← production (toujours sur main)
```

`banaProject-prod/` est un **git worktree** lié au même dépôt. Les deux partagent le même `.git` mais ont leurs fichiers indépendants sur le disque.

- **Gunicorn** (WSGI, port 9768) → pointe sur `banaProject-prod/bana/`
- **Daphne** (ASGI, port 8001) → WebSocket / Django Channels
- **Nginx** → reverse proxy + sert les fichiers statiques et media depuis `banaProject-prod/`
- **Systemd** → service `bana-gunicorn`

## Workflow dev → production

### Étape 1 — Développer dans `banaProject/`

```sh
cd /home/rootkitbana/banaProject
git checkout ma-branche          # travailler sur sa branche, jamais sur main
# ... coder, tester ...
git add .
git commit -m "feat: ..."
git push origin ma-branche
```

### Étape 2 — Merger dans main

**Seul (depuis le terminal) :**

Comme `main` est verrouillé par le worktree prod, on ne peut pas faire `git checkout main`. À la place :

```sh
# Depuis ta branche de dev, pousser directement vers main
git push origin ma-branche:main
```

**En équipe (via GitHub) :**

Ouvrir une Pull Request sur GitHub et merger `ma-branche` → `main` après review.
Recommandé à plusieurs pour la relecture du code et la traçabilité des changements.

> Dans les deux cas, ne jamais merger directement dans `banaProject-prod/` — toujours passer par `main` d'abord.

### Étape 3 — Déployer dans `banaProject-prod/`

Depuis le dossier dev, lancer le script de déploiement :

```sh
cd /home/rootkitbana/banaProject
bash deploy.sh
```

Le script effectue automatiquement dans l'ordre :
1. `git pull origin main` dans le dossier prod
2. Installation des dépendances Python (`pip install -r requirements.txt`)
3. Copie du CSS Tailwind compilé depuis dev (bloque si le CSS est introuvable)
4. `migrate`
5. `collectstatic`
6. Redémarrage de gunicorn + vérification que le service est bien actif

> Si tu as modifié du CSS Tailwind, lance `python manage.py tailwind build` en dev **avant** `deploy.sh`.

> Le dossier `media/` (uploads utilisateurs) est un lien symbolique vers `banaProject/bana/media/` — partagé entre dev et prod.

## Gestion du service

```sh
sudo systemctl status bana-gunicorn
sudo systemctl restart bana-gunicorn
sudo systemctl stop bana-gunicorn
```

Logs :
```sh
tail -f /home/rootkitbana/banaProject/logs/gunicorn_error.log
tail -f /home/rootkitbana/banaProject/logs/gunicorn_access.log
```

## Commandes manage.py utiles

```sh
cd bana

python manage.py runserver           # Serveur de développement
python manage.py makemigrations      # Créer les migrations
python manage.py migrate             # Appliquer les migrations
python manage.py compilemessages     # Compiler les traductions (.po → .mo)
python manage.py collectstatic       # Collecter les fichiers statiques
python manage.py disable_past_trajects  # Désactiver les trajets passés (tâche planifiée)
```

## Travailler en équipe

### Première fois — récupérer le projet

```sh
git clone git@github.com:Stratour/banaProject.git
cd banaProject
git checkout -b ma-branche
```

### Récupérer les derniers changements de main

Si des changements ont été déployés depuis ton dernier clone :

```sh
git fetch origin
git merge origin/main
```

### Proposer ses changements

```sh
git push origin ma-branche    # pousser sa branche
# Ouvrir une Pull Request sur GitHub → main
```

---

## Git — commandes utiles

```sh
git checkout -b feature/my-feature   # nouvelle branche
git checkout branch-name             # changer de branche
git fetch origin                     # récupérer les changements distants
git merge origin/main                # intégrer main dans sa branche
git push origin your-branch-name     # pousser sa branche
git worktree list                    # voir les worktrees actifs
```
