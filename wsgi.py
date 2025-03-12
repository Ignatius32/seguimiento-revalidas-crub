#!/usr/bin/env python3
import sys
import os

# Add the application directory to the Python path
sys.path.insert(0, '/var/www/seguimiento-revalidas-crub')

# Set environment variables if needed
os.environ['FLASK_ENV'] = 'production'

# Import the Flask application
from app import app as application

# This allows Apache/mod_wsgi to find the application
if __name__ == '__main__':
    application.run()