#!/bin/bash
echo "Arrêt de Gunicorn..."
PID=$(pgrep -f "gunicorn.*bana.wsgi")
if [ ! -z "$PID" ]; then
    kill -TERM $PID
    echo "Signal d'arrêt envoyé au processus $PID"
    sleep 2
    # Vérifier si le processus est toujours actif
    if pgrep -f "gunicorn.*bana.wsgi" > /dev/null; then
        echo "Arrêt forcé..."
        pkill -9 -f "gunicorn.*bana.wsgi"
    fi
    echo "Gunicorn arrêté"
else
    echo "Aucun processus Gunicorn trouvé"
fi
