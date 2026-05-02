import json
import os
import bcrypt
from datetime import datetime

USERS_DB_PATH = "database/users.json"

def get_users_db_path():
    """Get path to users database"""
    os.makedirs("database", exist_ok=True)
    return USERS_DB_PATH

def load_users():
    """Load all users from database"""
    db_path = get_users_db_path()
    if not os.path.exists(db_path):
        return {}
    
    try:
        with open(db_path, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    """Save users to database"""
    db_path = get_users_db_path()
    with open(db_path, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(email: str, password: str, name: str) -> bool:
    """Create a new user account"""
    users = load_users()
    
    # Check if user already exists
    if email in users:
        return False
    
    # Create new user
    users[email] = {
        "email": email,
        "name": name,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "patient_folder": email.replace('@', '_at_').replace('.', '_dot_')
    }
    
    save_users(users)
    return True

def authenticate_user(email: str, password: str):
    """Authenticate a user"""
    users = load_users()
    
    if email not in users:
        return None
    
    user = users[email]
    if verify_password(password, user["password"]):
        return {
            "email": user["email"],
            "name": user["name"],
            "patient_folder": user["patient_folder"]
        }
    
    return None

def get_user(email: str):
    """Get user by email"""
    users = load_users()
    if email in users:
        user = users[email]
        return {
            "email": user["email"],
            "name": user["name"],
            "patient_folder": user["patient_folder"]
        }
    return None
