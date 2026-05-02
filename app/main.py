import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import streamlit as st
from PIL import Image
import uuid
import json
import hashlib
import re
from datetime import datetime
import io
import pytz

from backend.db import add_patient, delete_patient, delete_report, load_db
from backend.auth_db import create_user, authenticate_user, get_user, change_password, delete_user_account, get_user_stats
from backend.mailer import send_email

from utils.inference import predict, model
from utils.gradcam import generate_attention_map
from utils.report import generate_report
from utils.riskengine import calculate_risk

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="PneumoScreen AI", layout="wide", page_icon="🏥")

# ─────────────────────────────────────────────
# PROFESSIONAL CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0a0e17 0%, #0d1117 100%);
}

/* Glass morphism effect for cards */
.glass-card {
    background: rgba(22, 27, 34, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(31, 111, 235, 0.2);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

/* Headers */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
}

.gradient-text {
    background: linear-gradient(135deg, #58a6ff, #1f6feb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(31, 111, 235, 0.2);
    color: white;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(31, 111, 235, 0.4);
    background: linear-gradient(135deg, #388bfd, #58a6ff);
}

/* Form inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    color: #e6edf3 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1rem !important;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 2px rgba(31, 111, 235, 0.2) !important;
}

/* GENDER SELECTBOX FIX */
.stSelectbox > div > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    color: #e6edf3 !important;
}

.stSelectbox label {
    color: #e6edf3 !important;
}

div[data-baseweb="select"] {
    color: #e6edf3 !important;
}

div[data-baseweb="select"] > div {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
}

.stSelectbox [data-baseweb="select"] [data-testid="stMarkdownContainer"] {
    color: #e6edf3 !important;
}

div[data-baseweb="select"] div[role="button"] {
    color: #e6edf3 !important;
}

div[data-baseweb="select"] ul {
    background-color: #161b22 !important;
}

div[data-baseweb="select"] ul li {
    color: #e6edf3 !important;
    background-color: #161b22 !important;
}

div[data-baseweb="select"] ul li:hover {
    background-color: #1f6feb !important;
    color: white !important;
}

div[data-baseweb="select"] ul li[aria-selected="true"] {
    background-color: #1f6feb !important;
    color: white !important;
}

/* Form containers */
.stForm {
    background: rgba(22, 27, 34, 0.6);
    backdrop-filter: blur(5px);
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* Expanders */
.streamlit-expanderHeader {
    background: rgba(22, 27, 34, 0.8);
    border-radius: 12px;
    border: 1px solid #30363d;
    font-weight: 600;
    color: #e6edf3;
}

.streamlit-expanderContent {
    background: rgba(22, 27, 34, 0.4);
    border-radius: 0 0 12px 12px;
    border: 1px solid #30363d;
    border-top: none;
}

/* Info/Warning/Success boxes */
.stAlert {
    border-radius: 12px;
    border-left: 4px solid;
}

/* Divider */
hr {
    margin: 2rem 0;
    background: linear-gradient(90deg, transparent, #1f6feb, #58a6ff, #1f6feb, transparent);
    height: 2px;
    border: none;
}

/* Badge styles */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 30px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'Inter', monospace;
}

.badge-primary {
    background: linear-gradient(135deg, #1f6feb22, #388bfd22);
    border: 1px solid #1f6feb;
    color: #58a6ff;
}

.badge-success {
    background: linear-gradient(135deg, #23863622, #2ea04322);
    border: 1px solid #238636;
    color: #3fb950;
}

.badge-warning {
    background: linear-gradient(135deg, #da363322, #f0883e22);
    border: 1px solid #da3633;
    color: #f85149;
}

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
}

.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #2ea043, #3fb950);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOGIN HISTORY FUNCTIONS
# ─────────────────────────────────────────────
LOGIN_HISTORY_FILE = "login_history.json"

def load_login_history():
    if os.path.exists(LOGIN_HISTORY_FILE):
        with open(LOGIN_HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_login_history(history):
    with open(LOGIN_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_login_record(username):
    history = load_login_history()
    history.append({
        "username": username,
        "login_time": datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success"
    })
    save_login_history(history)

def get_last_login(username):
    history = load_login_history()
    user_logins = [h for h in history if h["username"] == username]
    if user_logins:
        return user_logins[-1]["login_time"]
    return None

def get_all_logins():
    return load_login_history()

# ─────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"
if "form_counter" not in st.session_state:
    st.session_state["form_counter"] = 0
if "delete_report_id" not in st.session_state:
    st.session_state["delete_report_id"] = None
if "confirm_delete_account" not in st.session_state:
    st.session_state["confirm_delete_account"] = False
if "confirm_clear_history" not in st.session_state:
    st.session_state["confirm_clear_history"] = False

for _field, _default in [("f_name", ""), ("f_age", 1), ("f_gender", ""),
                          ("f_email", ""), ("f_phone", ""), ("f_doctor", "")]:
    if _field not in st.session_state:
        st.session_state[_field] = _default

if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "doctor_filter" not in st.session_state:
    st.session_state["doctor_filter"] = "All Doctors"

# ─────────────────────────────────────────────
# VALIDATION FUNCTIONS
# ─────────────────────────────────────────────
def validate_phone(phone: str) -> bool:
    return bool(re.match(r'^\d{10}$', phone))

def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email))

# ─────────────────────────────────────────────
# AUTHENTICATION UI
# ─────────────────────────────────────────────

def login_screen():
    """Display login/signup screen"""
    
    # Center everything
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; min-height: 70vh;">
        <div style="text-align: center; max-width: 500px; width: 100%;">
    """, unsafe_allow_html=True)
    
    # Logo and Title - Single line "PneumoScreen AI" with emoji
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <div style="font-size: 5rem; margin-bottom: 0.5rem;">🏥</div>
        <h1 style="font-size: 2.5rem; font-weight: 700; margin: 0; color: #e6edf3;">
            PneumoScreen AI
        </h1>
        <p style="color: #8b949e; margin-top: 0.5rem; font-size: 0.9rem;">
            Deep Learning-Based Pneumonia Screening & Reporting System
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature badges (four badges in a row) - matching second image
    st.markdown("""
    <div style="display: flex; justify-content: center; gap: 0.8rem; flex-wrap: wrap; margin: 1.5rem 0 2rem 0;">
        <span style="background: rgba(31, 111, 235, 0.15); padding: 0.35rem 1rem; border-radius: 30px; font-size: 0.75rem; color: #58a6ff; border: 1px solid rgba(31, 111, 235, 0.3);">🧠 AI-Powered Analysis</span>
        <span style="background: rgba(31, 111, 235, 0.15); padding: 0.35rem 1rem; border-radius: 30px; font-size: 0.75rem; color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.3);">📊 Clinical Grade</span>
        <span style="background: rgba(31, 111, 235, 0.15); padding: 0.35rem 1rem; border-radius: 30px; font-size: 0.75rem; color: #58a6ff; border: 1px solid rgba(31, 111, 235, 0.3);">🩻 Chest X-Ray</span>
        <span style="background: rgba(31, 111, 235, 0.15); padding: 0.35rem 1rem; border-radius: 30px; font-size: 0.75rem; color: #f85149; border: 1px solid rgba(248, 81, 73, 0.3);">⚡ Real-Time Detection</span>
    </div>
    """, unsafe_allow_html=True)

    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login", use_container_width=True, key="login_tab"):
            st.session_state["auth_mode"] = "login"
            st.rerun()
    with col2:
        if st.button("📝 Sign Up", use_container_width=True, key="signup_tab"):
            st.session_state["auth_mode"] = "signup"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state["auth_mode"] == "login":
        st.subheader("Welcome Back!")
        
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Sign In", use_container_width=True)
        
        if login_btn:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                user = authenticate_user(email, password)
                if user:
                    add_login_record(email)
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = user["email"]
                    st.session_state["user_name"] = user["name"]
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    
    else:
        st.subheader("Create New Account")
        
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Create Account", use_container_width=True)
        
        if signup_btn:
            if not name or not email or not password:
                st.error("Please fill all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not validate_email(email):
                st.error("Please use a valid Gmail address (@gmail.com)")
            else:
                if create_user(email, password, name):
                    st.success("Account created successfully! Please login.")
                    st.session_state["auth_mode"] = "login"
                    st.rerun()
                else:
                    st.error("Email already exists. Please use another email or login.")
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()
# ─────────────────────────────────────────────
# MAIN APP (Only shown when logged in)
# ─────────────────────────────────────────────

# Header with user info
col_title, col_profile = st.columns([3, 1])

with col_title:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0;">
            <span class="gradient-text">🏥 PneumoScreen AI</span>
        </h1>
        <p style="font-size: 1.1rem; color: #8b949e; margin-top: 0.5rem;">
            Deep Learning-Based Pneumonia Screening & Reporting System
        </p>
        <div style="display: flex; justify-content: center; gap: 0.8rem; margin-top: 1rem; flex-wrap: wrap;">
            <span class="badge badge-primary">🧠 AI-Powered Analysis</span>
            <span class="badge badge-success">📊 Clinical Grade</span>
            <span class="badge badge-primary">🩻 Chest X-Ray</span>
            <span class="badge badge-warning">⚡ Real-Time Detection</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_profile:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1f6feb11, #388bfd11); 
                border-radius: 12px; padding: 0.6rem 1rem; text-align: right;
                border: 1px solid #1f6feb33;">
        <span style="color: #58a6ff; font-weight: 600;">👤 {st.session_state['user_name']}</span>
        <span style="color: #8b949e; font-size: 0.7rem; display: block;">{st.session_state['user_email']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = None
        st.session_state["user_name"] = None
        st.rerun()

st.divider()

# ─────────────────────────────────────────────
# LOGIN INFO DISPLAY
# ─────────────────────────────────────────────
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**👤 Current User**  \n`{st.session_state['user_name']}`")

with col2:
    last_login = get_last_login(st.session_state["user_email"])
    if last_login:
        st.markdown(f"**🕐 Last Login**  \n`{last_login}`")
    else:
        st.markdown("**🕐 Last Login**  \n`First login`")

with col3:
    now_time = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"**📅 Current Time**  \n`{now_time}`")

st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────
# SETTINGS PANEL (Change Password, Delete Account, Login History)
# ─────────────────────────────────────────────
with st.expander("⚙️ Account Settings"):

    # Change Password
    st.markdown("**🔒 Change Password**")
    with st.form("change_password_form"):
        col1, col2 = st.columns(2)
        with col1:
            current_pass = st.text_input("Current Password", type="password")
            new_pass = st.text_input("New Password", type="password")
        with col2:
            confirm_pass = st.text_input("Confirm New Password", type="password")
        chg_btn = st.form_submit_button("🔄 Update Password", use_container_width=True)
    
    if chg_btn:
        if not current_pass or not new_pass:
            st.error("Please fill all fields")
        elif new_pass != confirm_pass:
            st.error("New passwords do not match")
        else:
            from backend.auth_db import change_password
            if change_password(st.session_state["user_email"], current_pass, new_pass):
                st.success("✅ Password updated successfully!")
            else:
                st.error("Current password is incorrect")

    st.markdown("---")
    
    # Login History
    st.markdown("**📊 Login History**")
    login_history = get_all_logins()
    user_logins = [h for h in login_history if h["username"] == st.session_state["user_email"]]
    
    if user_logins:
        history_data = []
        for record in reversed(user_logins[-10:]):
            history_data.append({
                "Time": record["login_time"],
                "Status": record["status"]
            })
        st.table(history_data)
        
        if st.button("🗑️ Clear My Login History", key="clear_history_btn"):
            st.session_state["confirm_clear_history"] = True
        
        if st.session_state.get("confirm_clear_history", False):
            st.warning("⚠️ Clear ALL your login history? This cannot be undone.")
            col_yes, col_no = st.columns(2)
            if col_yes.button("✅ Yes, Clear History", key="confirm_clear_yes"):
                remaining = [h for h in login_history if h["username"] != st.session_state["user_email"]]
                save_login_history(remaining)
                st.success("✅ Login history cleared!")
                st.session_state["confirm_clear_history"] = False
                st.rerun()
            if col_no.button("❌ Cancel", key="confirm_clear_no"):
                st.session_state["confirm_clear_history"] = False
                st.rerun()
    else:
        st.info("No login history available.")

    st.markdown("---")
    
    # Delete Account
    st.markdown("**🗑️ Delete Account**")
    st.warning("⚠️ This will permanently delete ALL your data (patients, reports, and account).")
    
    if not st.session_state["confirm_delete_account"]:
        if st.button("Delete My Account", key="init_delete_account"):
            st.session_state["confirm_delete_account"] = True
            st.rerun()
    else:
        st.error("⚠️ Are you absolutely sure? This cannot be undone!")
        col_yes, col_no = st.columns(2)
        if col_yes.button("✅ Yes, Delete My Account", key="confirm_del_account"):
            from backend.auth_db import delete_user_account
            if delete_user_account(st.session_state["user_email"]):
                st.success("Account deleted successfully!")
                st.session_state["logged_in"] = False
                st.session_state["user_email"] = None
                st.session_state["user_name"] = None
                st.session_state["confirm_delete_account"] = False
                st.rerun()
        if col_no.button("❌ Cancel", key="cancel_del_account"):
            st.session_state["confirm_delete_account"] = False
            st.rerun()

st.divider()

# ─────────────────────────────────────────────
# PATIENT IDENTITY HELPER
# ─────────────────────────────────────────────
def find_existing_patient(name: str, phone: str):
    reports = load_db(st.session_state["user_email"])
    for report in reports:
        if (report.get("name", "").strip().lower() == name.strip().lower()
                and report.get("phone", "").strip() == phone.strip()):
            return report
    return None

# ─────────────────────────────────────────────
# PATIENT REGISTRATION FORM
# ─────────────────────────────────────────────
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("📝 Patient Registration & Diagnosis")
st.markdown("</div>", unsafe_allow_html=True)

form_key = f"patient_form_{st.session_state['form_counter']}"

with st.form(form_key):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", value=st.session_state["f_name"])
        age = st.number_input("Age *", 1, 120, value=int(st.session_state["f_age"]))
        gender_options = ["Select", "Male", "Female", "Other"]
        current_gender = st.session_state["f_gender"] if st.session_state["f_gender"] in gender_options else "Select"
        gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0
        gender = st.selectbox("Gender *", gender_options, index=gender_index)
    with col2:
        email = st.text_input("Patient Email * (@gmail.com)", value=st.session_state["f_email"])
        phone = st.text_input("Phone Number * (10 digits)", value=st.session_state["f_phone"])
        doctor = st.text_input("Referring Doctor", value=st.session_state["f_doctor"])

    file = st.file_uploader("Upload Chest X-ray *", type=["png", "jpg", "jpeg"])
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        analyze_btn = st.form_submit_button("🔍 Analyze & Generate Report", use_container_width=True)
    with col_btn2:
        clear_btn = st.form_submit_button("🧹 Clear Form", use_container_width=True)

if clear_btn:
    st.session_state["f_name"] = ""
    st.session_state["f_age"] = 1
    st.session_state["f_gender"] = ""
    st.session_state["f_email"] = ""
    st.session_state["f_phone"] = ""
    st.session_state["f_doctor"] = ""
    st.session_state["form_counter"] += 1
    st.rerun()

# ─────────────────────────────────────────────
# ANALYSIS LOGIC
# ─────────────────────────────────────────────
if analyze_btn:
    if not name or not phone or not email or not file:
        st.error("❌ Name, Phone Number, Email, and X-ray image are all required.")
        st.stop()
    
    if not gender or gender == "Select":
        st.error("❌ Gender selection is mandatory.")
        st.stop()
    
    if not validate_phone(phone):
        st.error("❌ Phone number must be exactly 10 digits.")
        st.stop()
    
    if not validate_email(email):
        st.error("❌ Patient email must be @gmail.com")
        st.stop()

    existing = find_existing_patient(name, phone)
    now_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y%m%d")
    report_id = f"R-{now_str}-{uuid.uuid4().hex[:6].upper()}"

    if existing:
        patient_id = existing["patient_id"]
        st.info(f"🔁 Returning patient. ID: `{patient_id}` | New Report: `{report_id}`")
    else:
        patient_id = f"P-{uuid.uuid4().hex[:6].upper()}"
        st.success(f"🆕 New patient. ID: `{patient_id}` | Report: `{report_id}`")

    image = Image.open(file)
    st.image(image, caption="Uploaded X-ray", width=400)

    with st.spinner("Analyzing X-ray with AI..."):
        prediction, _, _ = predict(image)

    risk_level, risk_msg, severity = calculate_risk(prediction, {"age": age})

    st.subheader("🧠 AI Diagnosis Result")
    st.write(f"**Prediction:** {prediction['class']} | **Confidence:** {prediction['confidence']:.2%}")
    st.write(f"**Risk Level:** {risk_level}")
    st.caption(risk_msg)

    with st.spinner("Generating attention heatmap..."):
        heatmap = generate_attention_map(model, image)
    st.image(heatmap, caption="Attention Map", width=400)

    report_bytes = generate_report(
        {"id": patient_id, "report_id": report_id, "age": age, "gender": gender, "doctor": doctor},
        prediction,
        (risk_level, risk_msg),
        heatmap
    )

    # Save to user-specific storage
    with st.spinner("Saving patient data..."):
        user_folder = st.session_state["user_email"].replace('@', '_at_').replace('.', '_dot_')
        patient_folder = f"storage/{user_folder}/{patient_id}"
        os.makedirs(patient_folder, exist_ok=True)
        
        report_path = f"{patient_folder}/report_{report_id}.pdf"
        image_path = f"{patient_folder}/xray_{report_id}.jpg"
        
        with open(report_path, "wb") as fw:
            fw.write(report_bytes)
        
        save_image = image.copy()
        if save_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', save_image.size, (255, 255, 255))
            rgb_image.paste(save_image, mask=save_image.split()[3] if len(save_image.split()) > 3 else None)
            save_image = rgb_image
        elif save_image.mode != 'RGB':
            save_image = save_image.convert('RGB')
        save_image.save(image_path, 'JPEG', quality=95)

    # Save to user's database
    add_patient({
        "patient_id": patient_id,
        "report_id": report_id,
        "name": name,
        "age": age,
        "gender": gender,
        "email": email,
        "phone": phone,
        "doctor": doctor,
        "prediction": prediction,
        "risk": risk_level,
        "report_path": report_path,
        "image_url": image_path,
        "visit_date": datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    }, st.session_state["user_email"])

    # Email
    try:
        if os.path.exists(report_path):
            result = send_email(email, report_path, name, prediction)
            if isinstance(result, tuple) and result[0]:
                st.success(f"📩 Report emailed to {email}")
    except:
        st.info("📁 Report saved locally.")

    st.success(f"✅ Recorded | Patient: {patient_id} | Report: {report_id}")

    st.session_state["f_name"] = ""
    st.session_state["f_age"] = 1
    st.session_state["f_gender"] = "Select"
    st.session_state["f_email"] = ""
    st.session_state["f_phone"] = ""
    st.session_state["f_doctor"] = ""
    st.session_state["form_counter"] += 1
    st.rerun()

st.divider()

# ─────────────────────────────────────────────
# PATIENT DASHBOARD
# ─────────────────────────────────────────────
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("📊 Patient Dashboard")
st.markdown("</div>", unsafe_allow_html=True)

reports = load_db(st.session_state["user_email"])

# Search and Filter
col_search, col_filter, col_button = st.columns([2, 2, 1])

with col_search:
    search_input = st.text_input("Search by ID / Name / Phone / Report ID", key="search_input")

with col_filter:
    all_doctors = sorted({r.get("doctor", "").strip() for r in reports if r.get("doctor", "").strip()})
    filter_input = st.selectbox("Filter by Doctor", ["All Doctors"] + all_doctors, key="filter_input")

with col_button:
    st.write("")
    if st.button("🔍 Search", use_container_width=True):
        st.session_state["search_query"] = search_input
        st.session_state["doctor_filter"] = filter_input
        st.rerun()

def matches_search(record, query):
    if not query:
        return True
    q = query.lower()
    return (q in record.get("patient_id", "").lower() or
            q in record.get("name", "").lower() or
            q in record.get("phone", "").lower() or
            q in record.get("report_id", "").lower())

filtered = [r for r in reports if matches_search(r, st.session_state.get("search_query", ""))]
if st.session_state.get("doctor_filter", "All Doctors") != "All Doctors":
    filtered = [r for r in filtered if r.get("doctor", "") == st.session_state["doctor_filter"]]

if not reports:
    st.info("No patients registered yet.")
elif not filtered:
    st.warning("No matching records.")
else:
    st.caption(f"Showing {len(filtered)} of {len(reports)} records")
    
    patients_grouped = {}
    for report in filtered[::-1]:
        pid = report.get("patient_id")
        if pid not in patients_grouped:
            patients_grouped[pid] = []
        patients_grouped[pid].append(report)
    
    for patient_id, patient_reports in patients_grouped.items():
        patient_name = patient_reports[0].get("name", "Unknown")
        with st.expander(f"🧑 {patient_name} (ID: {patient_id}) - {len(patient_reports)} visit(s)"):
            for idx, report in enumerate(patient_reports):
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.markdown(f"**📄 Report ID:** {report.get('report_id', 'N/A')}")
                    st.markdown(f"**📅 Visit Date:** {report.get('visit_date', 'N/A')}")
                    st.markdown(f"**Age:** {report['age']} | **Gender:** {report['gender']}")
                    st.markdown(f"**Doctor:** {report.get('doctor', 'N/A')}")
                    st.markdown(f"**Prediction:** {report['prediction']['class']} ({report['prediction']['confidence']:.2%})")
                    st.markdown(f"**Risk:** {report['risk']}")
                with col_right:
                    rpath = report.get("report_path", "")
                    if rpath and os.path.exists(rpath):
                        with open(rpath, "rb") as f:
                            st.download_button("📄 Download", f, 
                                file_name=f"{patient_id}_{report['report_id']}.pdf",
                                key=f"dl_{report['report_id']}")
                    if st.button("🗑️ Delete", key=f"del_{report['report_id']}"):
                        if delete_report(report['report_id'], st.session_state["user_email"]):
                            st.rerun()
                st.divider()
