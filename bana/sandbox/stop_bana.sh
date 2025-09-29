#!/bin/bash

PIDFILE="/home/rootkitbana/banaProject/gunicorn.pid"

if [ -f $PIDFILE ]; then
    PID=$(cat $PIDFILE)
    echo "Arrêt de Gunicorn (PID: $PID)..."
    kill $PID
    rm $PIDFILE
    echo "✅ Gunicorn arrêté"
else
    echo "⚠️  PID file non trouvé, arrêt de tous les processus gunicorn..."
    pkill -f "gunicorn.*bana"
    echo "✅ Processus Gunicorn arrêtés"
fi
