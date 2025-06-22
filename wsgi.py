#!/usr/bin/python3

"""
WSGI configuration file for CrisQuiz Flask application.

This file is used by PythonAnywhere to run your Flask app in production.
Make sure to replace 'yourusername' with your actual PythonAnywhere username.
"""

import sys
import os

# Add your project directory to the Python path
# IMPORTANT: Replace 'yourusername' with your actual PythonAnywhere username
project_home = '/home/yourusername/CrisQuiz'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables if needed
os.environ.setdefault('FLASK_ENV', 'production')

# Import your Flask application
from app import app as application

# Initialize database if it doesn't exist
from app import init_db, DATABASE
if not os.path.exists(os.path.join(project_home, DATABASE)):
    init_db()
    print("Database initialized for production")

if __name__ == "__main__":
    application.run()
