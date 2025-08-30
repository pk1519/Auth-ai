"""
User Authentication Module for AuthAI

This module handles:
- MongoDB connection and user collection management
- User registration with password hashing
- User login verification
- Session management
"""

import bcrypt
import pymongo
from datetime import datetime
import os
from typing import Optional, Dict, Any
import streamlit as st

# MongoDB Configuration
# You can change these settings based on your MongoDB setup
MONGODB_URI = "mongodb://localhost:27017/"  # Default local MongoDB
DATABASE_NAME = "authai_db"
COLLECTION_NAME = "users"

class UserAuthManager:
    def __init__(self, mongodb_uri: str = MONGODB_URI, db_name: str = DATABASE_NAME):
        """Initialize the User Authentication Manager"""
        self.mongodb_uri = mongodb_uri
        self.db_name = db_name
        self.collection_name = COLLECTION_NAME
        self._client = None
        self._db = None
        self._collection = None
        
    def connect(self) -> bool:
        """Connect to MongoDB database"""
        try:
            self._client = pymongo.MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            self._client.server_info()
            self._db = self._client[self.db_name]
            self._collection = self._db[self.collection_name]
            
            # Create unique index on username and email
            self._collection.create_index("username", unique=True)
            self._collection.create_index("email", unique=True)
            
            return True
        except Exception as e:
            st.error(f"MongoDB connection failed: {str(e)}")
            return False
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hashed password"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user
        Returns: {"success": bool, "message": str, "user_id": str (if success)}
        """
        if self._collection is None:
            if not self.connect():
                return {"success": False, "message": "Database connection failed"}
        
        # Validate input
        if not username or not email or not password:
            return {"success": False, "message": "All fields are required"}
        
        if len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters long"}
        
        # Check if user already exists
        try:
            existing_user = self._collection.find_one({
                "$or": [{"username": username}, {"email": email}]
            })
            
            if existing_user:
                if existing_user.get("username") == username:
                    return {"success": False, "message": "Username already exists"}
                else:
                    return {"success": False, "message": "Email already registered"}
            
            # Create new user
            user_data = {
                "username": username,
                "email": email,
                "password_hash": self.hash_password(password),
                "created_at": datetime.utcnow(),
                "last_login": None,
                "is_active": True
            }
            
            result = self._collection.insert_one(user_data)
            
            return {
                "success": True,
                "message": "User registered successfully",
                "user_id": str(result.inserted_id)
            }
            
        except Exception as e:
            return {"success": False, "message": f"Registration failed: {str(e)}"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user login
        Returns: {"success": bool, "message": str, "user": dict (if success)}
        """
        if self._collection is None:
            if not self.connect():
                return {"success": False, "message": "Database connection failed"}
        
        if not username or not password:
            return {"success": False, "message": "Username and password are required"}
        
        try:
            # Find user by username or email
            user = self._collection.find_one({
                "$or": [{"username": username}, {"email": username}]
            })
            
            if not user:
                return {"success": False, "message": "Invalid username or password"}
            
            if not user.get("is_active", True):
                return {"success": False, "message": "Account is deactivated"}
            
            # Verify password
            if not self.verify_password(password, user["password_hash"]):
                return {"success": False, "message": "Invalid username or password"}
            
            # Update last login
            self._collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Remove password hash from returned user data
            user_data = {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "created_at": user["created_at"],
                "last_login": datetime.utcnow()
            }
            
            return {
                "success": True,
                "message": "Login successful",
                "user": user_data
            }
            
        except Exception as e:
            return {"success": False, "message": f"Login failed: {str(e)}"}
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if self._collection is None:
            if not self.connect():
                return None
        
        try:
            from bson.objectid import ObjectId
            user = self._collection.find_one({"_id": ObjectId(user_id)})
            if user:
                return {
                    "user_id": str(user["_id"]),
                    "username": user["username"],
                    "email": user["email"],
                    "created_at": user["created_at"],
                    "last_login": user.get("last_login")
                }
        except Exception as e:
            st.error(f"Error retrieving user: {str(e)}")
        return None
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user information"""
        if self._collection is None:
            if not self.connect():
                return False
        
        try:
            from bson.objectid import ObjectId
            # Remove sensitive fields that shouldn't be updated directly
            safe_fields = ["username", "email", "last_login", "is_active"]
            safe_update = {k: v for k, v in update_data.items() if k in safe_fields}
            
            if not safe_update:
                return False
            
            result = self._collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": safe_update}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            st.error(f"Error updating user: {str(e)}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        if self._collection is None:
            if not self.connect():
                return {"success": False, "message": "Database connection failed"}
        
        if len(new_password) < 6:
            return {"success": False, "message": "New password must be at least 6 characters long"}
        
        try:
            from bson.objectid import ObjectId
            user = self._collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Verify old password
            if not self.verify_password(old_password, user["password_hash"]):
                return {"success": False, "message": "Current password is incorrect"}
            
            # Update password
            new_hash = self.hash_password(new_password)
            result = self._collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password_hash": new_hash}}
            )
            
            if result.modified_count > 0:
                return {"success": True, "message": "Password changed successfully"}
            else:
                return {"success": False, "message": "Password change failed"}
                
        except Exception as e:
            return {"success": False, "message": f"Password change failed: {str(e)}"}


# Session Management Functions
def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = UserAuthManager()

def login_user_session(user_data: Dict[str, Any]):
    """Set user session after successful login"""
    st.session_state.authenticated = True
    st.session_state.user = user_data

def logout_user_session():
    """Clear user session"""
    st.session_state.authenticated = False
    st.session_state.user = None
    
    # Clear other AuthAI related session state
    keys_to_clear = ['monitor', 'monitor_running', 'bot_simulator', 'bot_running', 
                     'detection_history', 'feature_history', 'model_info', 'last_detection']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current logged in user"""
    return st.session_state.get('user') if is_authenticated() else None

def require_authentication():
    """Decorator-like function to require authentication"""
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()
    return True


# Database setup function
def setup_database():
    """Setup MongoDB database and collections"""
    auth_manager = UserAuthManager()
    if auth_manager.connect():
        st.success("✅ MongoDB connection successful!")
        auth_manager.close_connection()
        return True
    else:
        st.error("❌ MongoDB connection failed. Please check your MongoDB server.")
        return False


# Test MongoDB connection
def test_mongodb_connection(uri: str = MONGODB_URI) -> bool:
    """Test MongoDB connection"""
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        client.close()
        return True
    except Exception as e:
        st.error(f"MongoDB connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the authentication system
    auth_manager = UserAuthManager()
    
    if auth_manager.connect():
        print("✅ MongoDB connected successfully!")
        
        # Test user registration
        result = auth_manager.register_user("testuser", "test@example.com", "testpassword123")
        print(f"Registration result: {result}")
        
        # Test user login
        login_result = auth_manager.login_user("testuser", "testpassword123")
        print(f"Login result: {login_result}")
        
        auth_manager.close_connection()
    else:
        print("❌ MongoDB connection failed!")
