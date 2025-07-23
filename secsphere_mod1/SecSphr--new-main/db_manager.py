#!/usr/bin/env python3
"""
SecureSphere Database Management Utility
"""

import sys
import os
import shutil
from datetime import datetime
from app import app, db, User, Product

def backup_database():
    """Create a backup of the current database"""
    db_path = os.path.join('instance', 'securesphere.db')
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return False

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"instance/backup_{timestamp}.db"

    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def show_stats():
    """Display database statistics"""
    print("📊 SecureSphere Database Statistics")
    print("=" * 40)

    with app.app_context():
        try:
            total_users = User.query.count()
            total_products = Product.query.count()

            print(f"👥 Users: {total_users}")
            print(f"📦 Products: {total_products}")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "backup":
            backup_database()
        elif command == "stats":
            show_stats()
        else:
            print("Usage: python3 db_manager.py [backup|stats]")
    else:
        show_stats()
