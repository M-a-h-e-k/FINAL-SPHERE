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
    """Create sample users for testing and demonstration"""
    print("Creating sample users...")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@securesphere.com',
            'password': 'AdminPass123',
            'role': 'superuser',
            'organization': 'SecureSphere Inc.',
            'first_name': 'System',
            'last_name': 'Administrator'
        },
        {
            'username': 'lead_reviewer',
            'email': 'lead@securesphere.com',
            'password': 'LeadPass123',
            'role': 'lead',
            'organization': 'SecureSphere Inc.',
            'first_name': 'John',
            'last_name': 'Reviewer'
        },
        {
            'username': 'demo_client',
            'email': 'client@example.com',
            'password': 'ClientPass123',
            'role': 'client',
            'organization': 'Demo Corporation',
            'first_name': 'Jane',
            'last_name': 'Client',
            'phone': '+1-555-0123'
        },
        {
            'username': 'enterprise_client',
            'email': 'enterprise@company.com',
            'password': 'EnterprisePass123',
            'role': 'client',
            'organization': 'Enterprise Solutions Ltd',
            'first_name': 'Michael',
            'last_name': 'Manager',
            'phone': '+1-555-0456'
        }
    ]
    
    with app.app_context():
        try:
            for user_data in users_data:
                # Check if user already exists
                existing_user = User.query.filter_by(username=user_data['username']).first()
                if not existing_user:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        role=user_data['role'],
                        organization=user_data['organization'],
                        first_name=user_data.get('first_name'),
                        last_name=user_data.get('last_name'),
                        phone=user_data.get('phone'),
                        is_active=True
                    )
                    user.set_password(user_data['password'])
                    db.session.add(user)
                    print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
                else:
                    print(f"ℹ️  User already exists: {user_data['username']}")
            
            db.session.commit()
            print("✅ Sample users created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating sample users: {e}")
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
    """Create sample products for demonstration"""
    print("Creating sample products...")
    
    with app.app_context():
        try:
            # Get demo client
            demo_client = User.query.filter_by(username='demo_client').first()
            enterprise_client = User.query.filter_by(username='enterprise_client').first()
            
            if not demo_client or not enterprise_client:
                print("❌ Sample clients not found. Please create users first.")
                return False
            
            products_data = [
                {
                    'name': 'Web Application Security Assessment',
                    'description': 'Comprehensive security assessment for our customer-facing web application',
                    'owner_id': demo_client.id
                },
                {
                    'name': 'Mobile Banking App Security Review',
                    'description': 'Security evaluation of mobile banking application including API security',
                    'owner_id': demo_client.id
                },
                {
                    'name': 'Enterprise Network Infrastructure Assessment',
                    'description': 'Complete security audit of enterprise network infrastructure and systems',
                    'owner_id': enterprise_client.id
                },
                {
                    'name': 'Cloud Security Posture Assessment',
                    'description': 'Assessment of AWS cloud infrastructure security configuration and compliance',
                    'owner_id': enterprise_client.id
                }
            ]
            
            for product_data in products_data:
                existing_product = Product.query.filter_by(
                    name=product_data['name'], 
                    owner_id=product_data['owner_id']
                ).first()
                
                if not existing_product:
                    product = Product(
                        name=product_data['name'],
                        description=product_data['description'],
                        owner_id=product_data['owner_id']
                    )
                    db.session.add(product)
                    db.session.flush()  # This assigns the ID without committing
                    
                    # Create initial product status
                    status = ProductStatus(
                        product_id=product.id,
                        user_id=product_data['owner_id'],
                        status='in_progress',
                        questions_completed=0,
                        total_questions=0,
                        completion_percentage=0.0
                    )
                    db.session.add(status)
                    
                    print(f"✅ Created product: {product_data['name']}")
                else:
                    print(f"ℹ️  Product already exists: {product_data['name']}")
            
            db.session.commit()
            print("✅ Sample products created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating sample products: {e}")
            db.session.rollback()
            return False

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
                'score_history', 'system_settings'
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
    print("\n📋 Default Login Credentials:")
    print("   • Super Admin: admin / AdminPass123")
    print("   • Lead Reviewer: lead_reviewer / LeadPass123")
    print("   • Demo Client: demo_client / ClientPass123")
    print("   • Enterprise Client: enterprise_client / EnterprisePass123")
    print("\n⚠️  Please change default passwords in production!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)