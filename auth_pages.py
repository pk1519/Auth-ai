"""
Authentication Pages for AuthAI

This module contains the UI pages for:
- User registration/signup
- User login
- Authentication forms with validation
"""

import streamlit as st
import re
from user_auth import (
    UserAuthManager, init_session_state, login_user_session, 
    is_authenticated, get_current_user
)

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_username(username: str) -> bool:
    """Validate username format"""
    # Username should be 3-20 characters, alphanumeric and underscores only
    if len(username) < 3 or len(username) > 20:
        return False
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

def show_signup_page():
    """Display the signup page"""
    st.title("🔐 Sign Up for AuthAI")
    st.markdown("Create your account to access the AuthAI behavioral biometrics system")
    
    # Initialize auth manager
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = UserAuthManager()
    
    with st.form("signup_form", clear_on_submit=True):
        st.subheader("Create Your Account")
        
        # Input fields
        username = st.text_input(
            "Username",
            placeholder="Enter a unique username (3-20 characters)",
            help="Username can contain letters, numbers, and underscores only"
        )
        
        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address",
            help="We'll use this for account verification and notifications"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter a secure password (min 6 characters)",
            help="Use a strong password with letters, numbers, and symbols"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password"
        )
        
        # Terms and conditions checkbox
        terms_accepted = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            help="You must accept the terms to create an account"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            
            if not username:
                errors.append("Username is required")
            elif not validate_username(username):
                errors.append("Username must be 3-20 characters long and contain only letters, numbers, and underscores")
            
            if not email:
                errors.append("Email is required")
            elif not validate_email(email):
                errors.append("Please enter a valid email address")
            
            if not password:
                errors.append("Password is required")
            elif len(password) < 6:
                errors.append("Password must be at least 6 characters long")
            
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if not terms_accepted:
                errors.append("You must accept the Terms of Service")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Attempt registration
                with st.spinner("Creating your account..."):
                    result = st.session_state.auth_manager.register_user(username, email, password)
                
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    st.success("🎉 Account created successfully! You can now log in.")
                    st.session_state.signup_success = True
                else:
                    st.error(f"❌ {result['message']}")
    
    # Link to login page
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Already have an account? Log In", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

def show_login_page():
    """Display the login page"""
    st.title("🔐 Login to AuthAI")
    st.markdown("Sign in to access your AuthAI behavioral biometrics dashboard")
    
    # Initialize auth manager
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = UserAuthManager()
    
    with st.form("login_form", clear_on_submit=False):
        st.subheader("Welcome Back!")
        
        # Input fields
        username = st.text_input(
            "Username or Email",
            placeholder="Enter your username or email address"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )
        
        # Remember me checkbox (for future implementation)
        remember_me = st.checkbox("Remember me", help="Keep me logged in on this device")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("❌ Please enter both username/email and password")
            else:
                # Attempt login
                with st.spinner("Signing you in..."):
                    result = st.session_state.auth_manager.login_user(username, password)
                
                if result["success"]:
                    # Set user session
                    login_user_session(result["user"])
                    
                    st.success(f"✅ {result['message']}")
                    st.success(f"🎉 Welcome back, {result['user']['username']}!")
                    
                    # Redirect to main app
                    st.balloons()
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
    
    # Additional options
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Create New Account", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
    
    with col2:
        if st.button("Forgot Password?", use_container_width=True):
            st.info("Password reset functionality coming soon!")
            st.markdown("Please contact your administrator for password reset.")

def show_profile_page():
    """Display user profile page"""
    if not is_authenticated():
        st.error("Please log in to access this page.")
        return
    
    user = get_current_user()
    st.title(f"👤 User Profile - {user['username']}")
    
    # User information
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Username:** {user['username']}")
        st.info(f"**Email:** {user['email']}")
    
    with col2:
        st.info(f"**Member Since:** {user['created_at'].strftime('%B %d, %Y')}")
        if user.get('last_login'):
            st.info(f"**Last Login:** {user['last_login'].strftime('%B %d, %Y at %I:%M %p')}")
    
    # Change password section
    st.markdown("---")
    st.subheader("🔐 Change Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            errors = []
            
            if not current_password:
                errors.append("Current password is required")
            if not new_password:
                errors.append("New password is required")
            elif len(new_password) < 6:
                errors.append("New password must be at least 6 characters long")
            if new_password != confirm_new_password:
                errors.append("New passwords do not match")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                result = st.session_state.auth_manager.change_password(
                    user['user_id'], current_password, new_password
                )
                
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                else:
                    st.error(f"❌ {result['message']}")

def show_database_setup_page():
    """Display database setup page"""
    st.title("🗄️ Database Setup")
    st.markdown("Configure your MongoDB connection for AuthAI user management")
    
    # MongoDB connection test
    st.subheader("MongoDB Connection Test")
    
    if st.button("Test MongoDB Connection", use_container_width=True):
        with st.spinner("Testing MongoDB connection..."):
            auth_manager = UserAuthManager()
            if auth_manager.connect():
                st.success("✅ MongoDB connection successful!")
                st.success("Database and collections are ready for use.")
                auth_manager.close_connection()
            else:
                st.error("❌ MongoDB connection failed!")
                st.error("Please ensure MongoDB is running on your system.")
                
                # Show installation instructions
                st.markdown("### MongoDB Installation Guide:")
                st.markdown("1. **Download MongoDB Community Server** from https://www.mongodb.com/try/download/community")
                st.markdown("2. **Install MongoDB** following the installation wizard")
                st.markdown("3. **Start MongoDB service:**")
                st.code("net start MongoDB", language="bash")
                st.markdown("4. **Verify installation by running:**")
                st.code("mongosh", language="bash")
    
    # Configuration info
    st.markdown("---")
    st.subheader("Current Configuration")
    
    config_info = {
        "MongoDB URI": "mongodb://localhost:27017/",
        "Database Name": "authai_db",
        "Collection Name": "users"
    }
    
    for key, value in config_info.items():
        st.info(f"**{key}:** {value}")
    
    st.markdown("---")
    st.markdown("### 📋 Database Schema")
    st.markdown("The user collection will contain documents with the following fields:")
    
    schema = {
        "username": "string (unique)",
        "email": "string (unique)",
        "password_hash": "string (bcrypt hashed)",
        "created_at": "datetime",
        "last_login": "datetime (nullable)",
        "is_active": "boolean"
    }
    
    for field, description in schema.items():
        st.text(f"• {field}: {description}")


# Authentication wrapper function
def show_auth_page():
    """Main authentication page router"""
    # Initialize session state
    init_session_state()
    
    # Initialize page state
    if 'page' not in st.session_state:
        if is_authenticated():
            st.session_state.page = "dashboard"
        else:
            st.session_state.page = "login"
    
    # Show appropriate page
    if st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "signup":
        show_signup_page()
    elif st.session_state.page == "profile":
        show_profile_page()
    elif st.session_state.page == "database_setup":
        show_database_setup_page()
    elif st.session_state.page == "dashboard":
        # This will be handled by the main app
        pass
    else:
        show_login_page()


if __name__ == "__main__":
    # Test the authentication pages
    show_auth_page()
