"""
MongoDB Database Setup and Testing Script for AuthAI

This script helps with:
- Testing MongoDB connection
- Setting up the database and collections
- Creating test users
- Validating authentication functionality
"""

import sys
import os
from datetime import datetime
from user_auth import UserAuthManager, test_mongodb_connection

def print_separator(title=""):
    """Print a separator line with optional title"""
    print("\n" + "="*60)
    if title:
        print(f"  {title}")
        print("="*60)

def test_database_connection():
    """Test MongoDB database connection"""
    print_separator("MongoDB Connection Test")
    
    print("Testing MongoDB connection...")
    if test_mongodb_connection():
        print("✅ MongoDB connection successful!")
        return True
    else:
        print("❌ MongoDB connection failed!")
        print("\nPlease ensure:")
        print("1. MongoDB is installed on your system")
        print("2. MongoDB service is running")
        print("3. MongoDB is accessible at mongodb://localhost:27017/")
        return False

def setup_database():
    """Setup database and collections"""
    print_separator("Database Setup")
    
    auth_manager = UserAuthManager()
    
    if not auth_manager.connect():
        print("❌ Failed to connect to MongoDB")
        return False
    
    print("✅ Connected to MongoDB successfully!")
    print(f"Database: {auth_manager.db_name}")
    print(f"Collection: {auth_manager.collection_name}")
    
    # Database and collection are created automatically when first document is inserted
    print("✅ Database and collections are ready!")
    
    auth_manager.close_connection()
    return True

def create_test_users():
    """Create test users for testing"""
    print_separator("Creating Test Users")
    
    auth_manager = UserAuthManager()
    
    if not auth_manager.connect():
        print("❌ Failed to connect to MongoDB")
        return False
    
    # Test users to create
    test_users = [
        {"username": "admin", "email": "admin@authai.com", "password": "admin123"},
        {"username": "testuser", "email": "test@example.com", "password": "test123"},
        {"username": "demo_user", "email": "demo@authai.com", "password": "demo123"}
    ]
    
    created_users = []
    
    for user_data in test_users:
        print(f"\nCreating user: {user_data['username']}")
        result = auth_manager.register_user(
            user_data["username"], 
            user_data["email"], 
            user_data["password"]
        )
        
        if result["success"]:
            print(f"✅ User '{user_data['username']}' created successfully")
            created_users.append(user_data)
        else:
            if "already exists" in result["message"]:
                print(f"ℹ️  User '{user_data['username']}' already exists")
            else:
                print(f"❌ Failed to create user '{user_data['username']}': {result['message']}")
    
    auth_manager.close_connection()
    
    if created_users:
        print(f"\n✅ Successfully created {len(created_users)} new test users")
        print("\nTest users available:")
        for user in test_users:
            print(f"  • Username: {user['username']}, Password: {user['password']}")
    
    return True

def test_authentication():
    """Test authentication functionality"""
    print_separator("Authentication Testing")
    
    auth_manager = UserAuthManager()
    
    if not auth_manager.connect():
        print("❌ Failed to connect to MongoDB")
        return False
    
    # Test with existing user
    print("Testing login with test user...")
    login_result = auth_manager.login_user("testuser", "test123")
    
    if login_result["success"]:
        print("✅ Login test successful!")
        print(f"  User: {login_result['user']['username']}")
        print(f"  Email: {login_result['user']['email']}")
    else:
        print(f"❌ Login test failed: {login_result['message']}")
    
    # Test with wrong password
    print("\nTesting login with wrong password...")
    wrong_login = auth_manager.login_user("testuser", "wrongpassword")
    
    if not wrong_login["success"]:
        print("✅ Wrong password correctly rejected")
    else:
        print("❌ Wrong password was accepted (security issue!)")
    
    auth_manager.close_connection()
    return True

def display_system_info():
    """Display system information"""
    print_separator("AuthAI System Information")
    
    print("AuthAI Authentication System")
    print(f"Python Version: {sys.version}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Setup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if required files exist
    required_files = [
        "user_auth.py",
        "auth_pages.py", 
        "authai_streamlit_app.py",
        "authai_core.py"
    ]
    
    print("\nRequired Files Check:")
    all_files_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (MISSING)")
            all_files_exist = False
    
    if all_files_exist:
        print("\n✅ All required files are present!")
    else:
        print("\n❌ Some required files are missing!")

def run_installation_guide():
    """Display MongoDB installation guide"""
    print_separator("MongoDB Installation Guide")
    
    print("If MongoDB is not installed, please follow these steps:\n")
    
    print("1. **Download MongoDB Community Server:**")
    print("   Visit: https://www.mongodb.com/try/download/community")
    print("   Select your operating system and download the installer\n")
    
    print("2. **Install MongoDB:**")
    print("   Run the downloaded installer and follow the installation wizard")
    print("   Make sure to select 'Install MongoDB as a Service'\n")
    
    print("3. **Start MongoDB Service:**")
    print("   Windows: Open Command Prompt as Administrator and run:")
    print("   net start MongoDB\n")
    
    print("4. **Verify Installation:**")
    print("   Run this command to test: mongosh")
    print("   You should see the MongoDB shell prompt\n")
    
    print("5. **Alternative - MongoDB Atlas (Cloud):**")
    print("   For a cloud solution, create a free cluster at:")
    print("   https://cloud.mongodb.com")
    print("   Update the MONGODB_URI in user_auth.py with your connection string\n")

def main():
    """Main setup function"""
    print("🔒 AuthAI Authentication System Setup")
    print("=====================================")
    
    # Display system info
    display_system_info()
    
    # Test database connection
    if not test_database_connection():
        run_installation_guide()
        print("\n❌ Setup cannot continue without MongoDB connection")
        return False
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        return False
    
    # Create test users
    if not create_test_users():
        print("❌ Test user creation failed")
        return False
    
    # Test authentication
    if not test_authentication():
        print("❌ Authentication testing failed")
        return False
    
    # Success message
    print_separator("Setup Complete!")
    print("✅ AuthAI authentication system is ready!")
    print("\nNext Steps:")
    print("1. Run the Streamlit app:")
    print("   streamlit run authai_streamlit_app.py")
    print("\n2. Use these test credentials to login:")
    print("   Username: admin, Password: admin123")
    print("   Username: testuser, Password: test123")
    print("   Username: demo_user, Password: demo123")
    print("\n3. Create your own user account using the signup page")
    print("\n🎉 Enjoy using AuthAI!")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {str(e)}")
        print("Please check the error message and try again.")
