#!/bin/bash

cd /home/rootkitbana/banaProject/bana

# Active l'environnement virtuel si tu en utilises un
source ./../env/bin/activate

exec gunicorn bana.wsgi:application \
    --config /home/rootkitbana/banaProject/bana/gunicorn.conf.py
