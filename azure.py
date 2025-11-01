# Azure configuration file
import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the project directory to the Python path
sys.path.insert(0, BASE_DIR)

# WSGI application path
wsgi_app = "config.wsgi:application"

# Gunicorn config
bind = "0.0.0.0:8000"
workers = 2
threads = 4
timeout = 600