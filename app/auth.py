import streamlit as st
import json
import os
import hashlib

USERS_FILE = "database/users.json"

# ─────────────────────────────────────────────
# 🔐 PASSWORD HASHING
# ─────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─────────────────────────────────────────────
# 📂 LOAD USERS (SAFE)
# ─────────────────────────────────────────────
def load_users():
    if not os.path.exists(USERS_FILE):
        os.makedirs("database", exist_ok=True)

        # Create default admin
        default_user = {
            "admin": hash_password("admin123")
        }

        with open(USERS_FILE, "w") as f:
            json.dump(default_user, f, indent=4)

        return default_user

    with open(USERS_FILE) as f:
        return json.load(f)

# ─────────────────────────────────────────────
# 🔐 LOGIN FUNCTION
# ─────────────────────────────────────────────
def login():

    # Initialize session
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:

        st.sidebar.title("🔐 Admin Login")

        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):

            users = load_users()
            hashed_input = hash_password(password)

            if username in users and users[username] == hashed_input:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    else:
        st.sidebar.success(f"Logged in as {st.session_state.user}")

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

# ─────────────────────────────────────────────
# ✅ AUTH CHECK
# ─────────────────────────────────────────────
def check_auth():
    return st.session_state.get("logged_in", False)