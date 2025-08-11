#!/bin/bash

cd /home/bana_community/banaProject/bana

# Active l'environnement virtuel si tu en utilises un
source ./../env/bin/activate

exec gunicorn bana.wsgi:application \
    --config /home/bana_community/banaProject/bana/gunicorn.conf.py
