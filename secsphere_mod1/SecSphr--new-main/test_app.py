#!/usr/bin/env python3

import sys
import os

print("Testing SecureSphere Application...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    print("Importing Flask modules...")
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_mail import Mail
    print("✅ Flask modules imported successfully")
    
    print("Importing app...")
    from app import app, init_database
    print("✅ App imported successfully")
    
    print("Initializing database...")
    init_database()
    print("✅ Database initialized")
    
    print("Starting Flask app on port 5001...")
    app.run(debug=True, port=5001, host='0.0.0.0')
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()