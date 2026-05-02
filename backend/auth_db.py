import json
import os
import hashlib
import secrets
import shutil
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
    """Hash a password using SHA256 with salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}:{hash_obj.hexdigest()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, stored_hash = hashed.split(":")
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == stored_hash
    except:
        return False

def create_user(email: str, password: str, name: str) -> bool:
    """Create a new user account"""
    users = load_users()
    
    if email in users:
        return False
    
    users[email] = {
        "email": email,
        "name": name,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "user_folder": email.replace('@', '_at_').replace('.', '_dot_')
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
            "user_folder": user["user_folder"]
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
            "user_folder": user["user_folder"]
        }
    return None

def change_password(email: str, old_password: str, new_password: str) -> bool:
    """Change user password"""
    users = load_users()
    
    if email not in users:
        return False
    
    if not verify_password(old_password, users[email]["password"]):
        return False
    
    users[email]["password"] = hash_password(new_password)
    save_users(users)
    return True

def delete_user_account(email: str) -> bool:
    """Delete user account and all associated data"""
    users = load_users()
    
    if email not in users:
        return False
    
    # Delete user's database file (patients)
    try:
        from backend.db import get_user_db_path
        db_path = get_user_db_path(email)
        if db_path and os.path.exists(db_path):
            os.remove(db_path)
    except:
        pass
    
    # Delete user's storage folder (X-rays and reports)
    user_folder = email.replace('@', '_at_').replace('.', '_dot_')
    storage_path = f"storage/{user_folder}"
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)
    
    # Remove user from users database
    del users[email]
    save_users(users)
    return True

def get_user_stats(email: str):
    """Get user statistics (patient count, visit count)"""
    try:
        from backend.db import load_db
        reports = load_db(email)
        unique_patients = set()
        
        for report in reports:
            unique_patients.add(report.get("patient_id"))
        
        return {
            "total_patients": len(unique_patients),
            "total_visits": len(reports)
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {"total_patients": 0, "total_visits": 0}
