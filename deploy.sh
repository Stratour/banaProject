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

# 2. Dépendances Python
echo "[2/5] Dépendances Python..."
$PIP install -r "$PROD_DIR/requirements.txt" -q
echo "  OK"
echo ""

# 3. CSS Tailwind (non versionné, copié depuis dev)
echo "[3/5] CSS Tailwind..."
if [ -d "$DEV_DIR/bana/theme/static/css" ]; then
    cp -r "$DEV_DIR/bana/theme/static/css" "$PROD_DIR/bana/theme/static/"
    echo "  OK (copié depuis dev)"
else
    echo "  ATTENTION : CSS introuvable dans dev ($DEV_DIR/bana/theme/static/css)"
    echo "  Lance 'python manage.py tailwind build' dans dev avant de déployer."
    exit 1
fi
echo ""

# 4. Migrations
echo "[4/5] Migrations..."
cd "$PROD_DIR/bana"
$PYTHON manage.py migrate --noinput
echo ""

# 5. Collectstatic
echo "[5/5] Collectstatic..."
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
