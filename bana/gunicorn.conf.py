import multiprocessing
import os

# Socket Unix
bind = "unix:/run/bana-gunicorn.sock"
backlog = 2048

# Workers
workers = 3  # Commençons avec moins de workers
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/home/bana_community/banaProject/logs/gunicorn_access.log"
errorlog = "/home/bana_community/banaProject/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "bana_django"

# Working directory
chdir = "/home/bana_community/banaProject/bana"

# Pas de daemon mode pour systemd
daemon = False

# Permissions du socket
umask = 0
