#!/usr/bin/env python3
"""
Database Migration Script for SecureSphere
Handles database schema updates safely.
"""

import sqlite3
import os
from app import app, db

def migrate_database():
    """Apply all necessary database migrations"""

    # Get database path
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
    if not db_path:
        db_path = 'instance/users.db'

    print(f"Migrating database at: {db_path}")

    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Migration 1: Add needs_client_response column to questionnaire_response table
        try:
            cursor.execute("SELECT needs_client_response FROM questionnaire_response LIMIT 1")
            print("✓ needs_client_response column already exists")
        except sqlite3.OperationalError:
            print("Adding needs_client_response column to questionnaire_response table...")
            cursor.execute("""
                ALTER TABLE questionnaire_response
                ADD COLUMN needs_client_response BOOLEAN DEFAULT 0
            """)
            print("✓ Added needs_client_response column")

        # Migration 2: Add any other necessary columns here

        # Commit changes
        conn.commit()
        print("✓ All migrations completed successfully")

    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def create_tables():
    """Create all tables if they don't exist"""
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created/verified")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise

if __name__ == "__main__":
    print("Starting database migration...")

    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)

    # Run migrations
    migrate_database()
    create_tables()

    print("✅ Database migration completed!")