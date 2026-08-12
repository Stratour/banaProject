#!/bin/bash
set -e

PROD_DIR="/home/rootkitbana/banaProject-prod"
DEV_DIR="/home/rootkitbana/banaProject"
PYTHON="/home/rootkitbana/env/bin/python"
PIP="/home/rootkitbana/env/bin/pip"

echo ""
echo "======================================="
echo "   Déploiement BanaCommunity"
echo "======================================="
echo ""

# 1. Pull main
echo "[1/6] Récupération de main..."
git config --global --add safe.directory "$PROD_DIR"
git -C "$PROD_DIR" pull origin main
echo ""

# 2. Vérification .env prod
echo "[2/6] Vérification .env prod..."
if [ ! -f "$PROD_DIR/bana/.env" ]; then
    echo "  ERREUR : $PROD_DIR/bana/.env manquant."
    echo "  Crée-le manuellement avec DEBUG=False et les credentials prod."
    exit 1
fi
echo "  OK (non écrasé)"
echo ""

# 3. Dépendances Python
echo "[3/6] Dépendances Python..."
$PIP install -r "$PROD_DIR/requirements.txt" -q
echo "  OK"
echo ""

# 4. CSS Tailwind (non versionné : reconstruit dans dev, puis copié)
echo "[4/6] CSS Tailwind..."
echo "  Build de production..."
# Sous-shell : ne pas polluer le cwd des etapes suivantes.
# Sans ce build, on risque de deployer la sortie non minifiee du watcher
# 'tailwind start', 25% plus lourde et potentiellement incomplete.
( cd "$DEV_DIR/bana" && $PYTHON manage.py tailwind build )

if [ -d "$DEV_DIR/bana/theme/static/css" ]; then
    cp -r "$DEV_DIR/bana/theme/static/css" "$PROD_DIR/bana/theme/static/"
    echo "  OK (build + copié depuis dev)"
else
    echo "  ERREUR : CSS introuvable après le build ($DEV_DIR/bana/theme/static/css)"
    exit 1
fi
echo ""

# 5. Migrations
echo "[5/6] Migrations..."
cd "$PROD_DIR/bana"
$PYTHON manage.py migrate --noinput
echo ""

# 6. Collectstatic
echo "[6/6] Collectstatic..."
$PYTHON manage.py collectstatic --noinput 2>&1 | tail -2
echo ""

# Redémarrage gunicorn
echo "Redémarrage de gunicorn..."
sudo systemctl restart bana-gunicorn
sleep 2

# Vérification finale
if systemctl is-active --quiet bana-gunicorn; then
    echo ""
    echo "======================================="
    echo "   Déploiement réussi"
    echo "======================================="
    echo ""
else
    echo ""
    echo "======================================="
    echo "   ERREUR : gunicorn n'a pas démarré"
    echo "======================================="
    sudo systemctl status bana-gunicorn --no-pager
    exit 1
fi
