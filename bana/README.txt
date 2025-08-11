
Il faut activer l'environnement virtuel.


# Arrêter
/home/bana_community/banaProject/stop_bana.sh

# Démarrer
/home/bana_community/banaProject/start_bana.sh

# Ou en une commande
/home/bana_community/banaProject/stop_bana.sh && /home/bana_community/banaProject/start_bana.sh


# Méthode rapide pour redémarrer
pkill -f gunicorn && cd /home/bana_community/banaProject/bana && source /home/bana_community/banaProject/env/bin/activate && gunicorn bana.wsgi:application --bind 127.0.0.1:9685 --workers 3 --timeout 30 --daemon

Toute la procédure fournie et détaillé par Claude.ai
https://claude.ai/share/b4f66ce2-bd48-41a0-9e9d-176e765c935e
