#!/bin/bash

PROJECTDIR="/home/bana_community/banaProject/bana"
VENVDIR="/home/bana_community/banaProject/env"
LOGDIR="/home/bana_community/banaProject/logs"
PIDFILE="/home/bana_community/banaProject/gunicorn.pid"

cd $PROJECTDIR
source $VENVDIR/bin/activate

# Créer le dossier de logs
mkdir -p $LOGDIR

# Arrêter les anciens processus
if [ -f $PIDFILE ]; then
    kill `cat $PIDFILE` 2>/dev/null
    rm $PIDFILE
fi

echo "Démarrage de Gunicorn sur le port 9685..."

# Démarrer Gunicorn sur le port 9685
gunicorn bana.wsgi:application \
    --bind 127.0.0.1:9685 \
    --workers 3 \
    --timeout 30 \
    --keep-alive 2 \
    --max-requests 1000 \
    --access-logfile $LOGDIR/gunicorn_access.log \
    --error-logfile $LOGDIR/gunicorn_error.log \
    --log-level info \
    --pid $PIDFILE \
    --daemon

sleep 2

if [ -f $PIDFILE ]; then
    echo "✅ Gunicorn démarré avec succès sur le port 9685 (PID: $(cat $PIDFILE))"
    echo "🌐 Site accessible sur http://37.187.94.53 et http://bana.mobi"
    echo "🔧 Test direct : curl -I http://127.0.0.1:9685"
else
    echo "❌ Erreur lors du démarrage de Gunicorn"
fi
