#!/usr/bin/env python3
"""
Database Migration Script for SecureSphere
This script adds missing columns to existing database tables.
Run this script if you encounter database column errors.
"""

import sqlite3
import os

def migrate_database():
    """Add missing columns to existing database"""
    db_path = 'instance/securesphere.db'
    
    if not os.path.exists(db_path):
        print("Database file not found. Please run the main application first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add is_reviewed column to questionnaire_response table
        try:
            cursor.execute("ALTER TABLE questionnaire_response ADD COLUMN is_reviewed BOOLEAN DEFAULT 0")
            print("✅ Added is_reviewed column to questionnaire_response table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  is_reviewed column already exists")
            else:
                print(f"❌ Error adding is_reviewed column: {e}")
        
        # Add score column to questionnaire_response table
        try:
            cursor.execute("ALTER TABLE questionnaire_response ADD COLUMN score INTEGER DEFAULT 0")
            print("✅ Added score column to questionnaire_response table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  score column already exists")
            else:
                print(f"❌ Error adding score column: {e}")
        
        # Add created_at column to lead_comment table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE lead_comment ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("✅ Added created_at column to lead_comment table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  created_at column already exists")
            else:
                print(f"❌ Error adding created_at column: {e}")
        
        # Create new tables if they don't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    status VARCHAR(50) DEFAULT 'in_progress',
                    questions_completed INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES product (id),
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """)
            print("✅ Created product_status table")
        except sqlite3.OperationalError as e:
            print(f"ℹ️  product_status table: {e}")
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS score_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    section_name VARCHAR(100) NOT NULL,
                    total_score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 0,
                    percentage REAL DEFAULT 0.0,
                    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES product (id),
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """)
            print("✅ Created score_history table")
        except sqlite3.OperationalError as e:
            print(f"ℹ️  score_history table: {e}")
        
        conn.commit()
        print("\n🎉 Database migration completed successfully!")
        print("You can now run the application without errors.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Starting database migration...")
    migrate_database()