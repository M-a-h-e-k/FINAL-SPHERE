#!/usr/bin/env python3
"""
SecureSphere Web Application Startup Script
"""

import os
import sys
from app import app, db, init_database

def setup_and_run():
    """Setup database and run the webapp"""
    print("🚀 Starting SecureSphere Web Application...")
    print("=" * 50)
    
    # Initialize database
    print("📊 Initializing database...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            return False
    
    # Check if running in debug mode
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("✅ All systems ready!")
    print("🌐 Starting web server...")
    print("=" * 50)
    print(f"🔗 Access your webapp at: http://127.0.0.1:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the Flask app
        app.run(
            host='127.0.0.1',
            port=5001,
            debug=debug_mode,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    setup_and_run()