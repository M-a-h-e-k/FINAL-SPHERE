#!/usr/bin/env python3
"""
Professional Database Initialization Script for SecureSphere
Creates a complete, persistent database with proper structure and sample data.
"""

import os
import sys
from datetime import datetime, timezone
from app import app, db, User, Product, ProductStatus, QuestionnaireResponse, LeadComment, ScoreHistory, SystemSettings

def create_database():
    """Create all database tables"""
    print("Creating database tables...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
            return True
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False

def create_sample_users():
    """Create only essential system user"""
    print("Creating essential system user...")

    with app.app_context():
        try:
            # Only create admin if it doesn't exist
            existing_admin = User.query.filter_by(username='admin').first()
            if not existing_admin:
                admin = User(
                    username='admin',
                    email='admin@securesphere.com',
                    role='superuser',
                    organization='SecureSphere Inc.',
                    first_name='System',
                    last_name='Administrator'
                )
                admin.set_password('AdminPass123')
                db.session.add(admin)
                print(f"✅ Created admin user for system management")
            else:
                print(f"ℹ️  Admin user already exists")

            db.session.commit()
            print("✅ Essential user created successfully")
            return True

        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()
            return False

def create_system_settings():
    """Create system settings for the application"""
    print("Creating system settings...")

    settings_data = [
        {
            'key': 'app_name',
            'value': 'SecureSphere',
            'description': 'Application name displayed in the interface'
        },
        {
            'key': 'app_version',
            'value': '2.0.0',
            'description': 'Current application version'
        },
        {
            'key': 'scoring_enabled',
            'value': 'true',
            'description': 'Enable or disable scoring functionality'
        },
        {
            'key': 'max_file_size',
            'value': '10485760',  # 10MB in bytes
            'description': 'Maximum file upload size in bytes'
        },
        {
            'key': 'session_timeout',
            'value': '3600',  # 1 hour in seconds
            'description': 'User session timeout in seconds'
        },
        {
            'key': 'email_notifications',
            'value': 'true',
            'description': 'Enable email notifications'
        },
        {
            'key': 'maintenance_mode',
            'value': 'false',
            'description': 'Enable maintenance mode'
        }
    ]

    with app.app_context():
        try:
            for setting_data in settings_data:
                existing_setting = SystemSettings.query.filter_by(key=setting_data['key']).first()
                if not existing_setting:
                    setting = SystemSettings(
                        key=setting_data['key'],
                        value=setting_data['value'],
                        description=setting_data['description']
                    )
                    db.session.add(setting)
                    print(f"✅ Created setting: {setting_data['key']}")
                else:
                    print(f"ℹ️  Setting already exists: {setting_data['key']}")

            db.session.commit()
            print("✅ System settings created successfully")
            return True

        except Exception as e:
            print(f"❌ Error creating system settings: {e}")
            db.session.rollback()
            return False

def create_sample_products():
    """Skip sample products creation - products will be created by users"""
    print("Skipping sample products creation - products will be created by users")
    return True

def verify_database():
    """Verify that the database was created correctly"""
    print("Verifying database integrity...")

    with app.app_context():
        try:
            # Check table creation using inspector
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            expected_tables = [
                'users', 'products', 'product_statuses',
                'questionnaire_responses', 'lead_comments',
                'score_history', 'system_settings', 'invitation_tokens'
            ]

            for table in expected_tables:
                if table in tables:
                    print(f"✅ Table exists: {table}")
                else:
                    print(f"❌ Table missing: {table}")
                    return False

            # Check sample data
            user_count = User.query.count()
            product_count = Product.query.count()
            settings_count = SystemSettings.query.count()

            print(f"📊 Database Statistics:")
            print(f"   • Users: {user_count}")
            print(f"   • Products: {product_count}")
            print(f"   • System Settings: {settings_count}")

            if user_count > 0 and settings_count > 0:
                print("✅ Database verification successful")
                return True
            else:
                print("❌ Database verification failed - missing data")
                return False

        except Exception as e:
            print(f"❌ Error verifying database: {e}")
            return False

def backup_existing_database():
    """Backup existing database if it exists"""
    db_path = os.path.join('instance', 'securesphere.db')
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"✅ Existing database backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error backing up database: {e}")
            return False
    return True

def main():
    """Main initialization function"""
    print("🚀 Starting SecureSphere Database Initialization")
    print("=" * 60)

    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)

    # Backup existing database
    if not backup_existing_database():
        print("❌ Failed to backup existing database")
        return False

    # Create database
    if not create_database():
        print("❌ Database initialization failed")
        return False

    # Create sample users
    if not create_sample_users():
        print("❌ User creation failed")
        return False

    # Create system settings
    if not create_system_settings():
        print("❌ System settings creation failed")
        return False

    # Create sample products
    if not create_sample_products():
        print("❌ Product creation failed")
        return False

    # Verify database
    if not verify_database():
        print("❌ Database verification failed")
        return False

    print("=" * 60)
    print("🎉 Database initialization completed successfully!")
    print("\n📋 Admin Login Credentials:")
    print("   • Super Admin: admin / AdminPass123")
    print("\n⚠️  Please change admin password in production!")
    print("💡 Users and products will be created through the admin interface")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)