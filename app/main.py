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

from backend.db import add_patient, delete_patient, delete_report, load_db
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
# PROFESSIONAL CUSTOM CSS (WITH GENDER FIX)
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

/* GENDER SELECTBOX FIX - Make text white */
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

/* Sidebar customization */
.css-1d391kg, .stSidebar {
    background: linear-gradient(180deg, #0a0e17 0%, #0d1117 100%);
    border-right: 1px solid #30363d;
}

/* Metrics and stats cards */
.metric-card {
    background: linear-gradient(135deg, #161b22, #1c2128);
    border-radius: 16px;
    padding: 1rem;
    border: 1px solid #30363d;
    text-align: center;
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
# ADMIN AUTH FILE HELPERS
# ─────────────────────────────────────────────
ADMIN_FILE = "admin_credentials.json"
LOGIN_HISTORY_FILE = "login_history.json"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_admin() -> dict | None:
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r") as f:
            return json.load(f)
    return None

def save_admin(username: str, password: str):
    with open(ADMIN_FILE, "w") as f:
        json.dump({"username": username, "password": hash_password(password)}, f)

def delete_admin_account():
    if os.path.exists(ADMIN_FILE):
        os.remove(ADMIN_FILE)

def verify_admin(username: str, password: str) -> bool:
    admin = load_admin()
    if admin is None:
        return False
    return admin["username"] == username and admin["password"] == hash_password(password)

# ─────────────────────────────────────────────
# LOGIN HISTORY FUNCTIONS
# ─────────────────────────────────────────────
def load_login_history() -> list:
    if os.path.exists(LOGIN_HISTORY_FILE):
        with open(LOGIN_HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_login_history(history: list):
    with open(LOGIN_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_login_record(username: str):
    history = load_login_history()
    history.append({
        "username": username,
        "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip_address": "Local",
        "status": "success"
    })
    save_login_history(history)

def get_last_login(username: str) -> str | None:
    history = load_login_history()
    user_logins = [h for h in history if h["username"] == username]
    if user_logins:
        return user_logins[-1]["login_time"]
    return None

def get_all_logins() -> list:
    return load_login_history()

# ─────────────────────────────────────────────
# VALIDATION FUNCTIONS
# ─────────────────────────────────────────────
def validate_phone(phone: str) -> bool:
    return bool(re.match(r'^\d{10}$', phone))

def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email))

# ─────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = None
if "delete_id" not in st.session_state:
    st.session_state["delete_id"] = None
if "delete_report_id" not in st.session_state:
    st.session_state["delete_report_id"] = None
if "confirm_delete_admin" not in st.session_state:
    st.session_state["confirm_delete_admin"] = False
if "confirm_clear_history" not in st.session_state:
    st.session_state["confirm_clear_history"] = False
if "form_counter" not in st.session_state:
    st.session_state["form_counter"] = 0
if "current_username" not in st.session_state:
    st.session_state["current_username"] = None
if "last_login" not in st.session_state:
    st.session_state["last_login"] = None

for _field, _default in [("f_name", ""), ("f_age", 1), ("f_gender", ""),
                          ("f_email", ""), ("f_phone", ""), ("f_doctor", "")]:
    if _field not in st.session_state:
        st.session_state[_field] = _default

if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "doctor_filter" not in st.session_state:
    st.session_state["doctor_filter"] = "All Doctors"
if "trigger_search" not in st.session_state:
    st.session_state["trigger_search"] = False

# ─────────────────────────────────────────────
# PROFESSIONAL HEADER SECTION
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 1rem 0 0.5rem 0;">
    <h1 style="font-size: 3rem; font-weight: 800; margin: 0;">
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

# ─────────────────────────────────────────────
# HEADER ROW WITH AUTH
# ─────────────────────────────────────────────
col_title, col_auth = st.columns([3, 1])

with col_title:
    st.markdown("---")

with col_auth:
    if st.session_state["authenticated"]:
        admin = load_admin()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1f6feb11, #388bfd11); 
                    border-radius: 12px; padding: 0.6rem 1rem; text-align: right;
                    border: 1px solid #1f6feb33;">
            <span style="color: #58a6ff; font-weight: 600;">👤 {admin["username"]}</span>
            <span style="color: #8b949e; font-size: 0.7rem; display: block;">Administrator</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["auth_mode"] = None
            st.session_state["current_username"] = None
            st.rerun()
    else:
        admin_exists = load_admin() is not None
        btn_label = "🔐 Sign In" if admin_exists else "📝 Register"
        if st.button(btn_label, key="open_auth_btn", use_container_width=True):
            st.session_state["auth_mode"] = "login" if admin_exists else "register"

st.divider()

# ─────────────────────────────────────────────
# AUTH PANEL
# ─────────────────────────────────────────────
if not st.session_state["authenticated"] and st.session_state["auth_mode"] is not None:
    admin_exists = load_admin() is not None

    if not admin_exists:
        st.markdown('<div style="max-width: 450px; margin: 2rem auto;">', unsafe_allow_html=True)
        st.subheader("🔐 Create Admin Account")
        st.info("No admin registered yet. Only one admin account is allowed.")
        with st.form("register_form"):
            new_user  = st.text_input("Choose Username")
            new_pass  = st.text_input("Choose Password", type="password")
            new_pass2 = st.text_input("Confirm Password", type="password")
            reg_btn   = st.form_submit_button("✅ Register", use_container_width=True)
        if reg_btn:
            if not new_user or not new_pass:
                st.error("Username and password cannot be empty.")
            elif new_pass != new_pass2:
                st.error("Passwords do not match.")
            else:
                save_admin(new_user, new_pass)
                st.success("Admin account created! Please sign in.")
                st.session_state["auth_mode"] = "login"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="max-width: 450px; margin: 2rem auto;">', unsafe_allow_html=True)
        st.subheader("🔑 Admin Sign In")
        with st.form("login_form"):
            uname     = st.text_input("Username")
            upass     = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("🔓 Sign In", use_container_width=True)
        if login_btn:
            if verify_admin(uname, upass):
                add_login_record(uname)
                last_login = get_last_login(uname)
                
                st.session_state["authenticated"] = True
                st.session_state["auth_mode"] = None
                st.session_state["current_username"] = uname
                st.session_state["last_login"] = last_login
                st.rerun()
            else:
                st.error("Invalid credentials.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

# ─────────────────────────────────────────────
# LOGIN INFO DISPLAY
# ─────────────────────────────────────────────
if st.session_state["authenticated"]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**👤 Current User**  \n`{st.session_state['current_username']}`")
    
    with col2:
        if st.session_state.get("last_login"):
            st.markdown(f"**🕐 Last Login**  \n`{st.session_state['last_login']}`")
        else:
            st.markdown("**🕐 Last Login**  \n`First login`")
    
    with col3:
        st.markdown(f"**📅 Current Time**  \n`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

# ─────────────────────────────────────────────
# SETTINGS PANEL
# ─────────────────────────────────────────────
if st.session_state["authenticated"]:
    with st.expander("⚙️ Admin Settings"):

        st.markdown("**🔒 Change Password**")
        with st.form("change_password_form"):
            col1, col2 = st.columns(2)
            with col1:
                old_pass = st.text_input("Current Password", type="password")
                new_p    = st.text_input("New Password", type="password")
            with col2:
                new_p2   = st.text_input("Confirm New Password", type="password")
            chg_btn  = st.form_submit_button("🔄 Update Password", use_container_width=True)
        if chg_btn:
            admin = load_admin()
            if hash_password(old_pass) != admin["password"]:
                st.error("Current password is incorrect.")
            elif not new_p:
                st.error("New password cannot be empty.")
            elif new_p != new_p2:
                st.error("New passwords do not match.")
            else:
                save_admin(admin["username"], new_p)
                st.success("✅ Password updated successfully.")

        st.markdown("---")
        
        st.markdown("**📊 Login History**")
        login_history = get_all_logins()
        if login_history:
            history_data = []
            for record in reversed(login_history[-10:]):
                history_data.append({
                    "Time": record["login_time"],
                    "Username": record["username"],
                    "Status": record["status"]
                })
            st.table(history_data)
            col_clear1, col_clear2 = st.columns([1, 3])
            with col_clear1:
                if st.button("🗑️ Clear All History", key="clear_history_btn", use_container_width=True):
                    st.session_state["confirm_clear_history"] = True
            
            if st.session_state.get("confirm_clear_history", False):
                st.warning("⚠️ Are you sure you want to clear ALL login history? This action cannot be undone.")
                col_yes, col_no = st.columns(2)
                if col_yes.button("✅ Yes, Clear History", key="confirm_clear_yes"):
                    if os.path.exists(LOGIN_HISTORY_FILE):
                        os.remove(LOGIN_HISTORY_FILE)
                    st.success("✅ Login history cleared successfully!")
                    st.session_state["confirm_clear_history"] = False
                    st.rerun()
                if col_no.button("❌ Cancel", key="confirm_clear_no"):
                    st.session_state["confirm_clear_history"] = False
                    st.rerun()
        else:
            st.info("No login history available yet.")

        st.markdown("---")

        st.markdown("**🗑️ Delete Admin Account**")
        st.warning("⚠️ Removes the admin account. App will require re-registration.")

        if not st.session_state["confirm_delete_admin"]:
            if st.button("Delete My Admin Account", key="init_delete_admin"):
                st.session_state["confirm_delete_admin"] = True
                st.rerun()
        else:
            st.error("Are you absolutely sure? This cannot be undone.")
            ca, cb = st.columns(2)
            if ca.button("Yes, Delete Account", key="confirm_del_admin"):
                delete_admin_account()
                st.session_state["authenticated"]       = False
                st.session_state["confirm_delete_admin"] = False
                st.success("Admin account deleted.")
                st.rerun()
            if cb.button("Cancel", key="cancel_del_admin"):
                st.session_state["confirm_delete_admin"] = False
                st.rerun()

    st.divider()

# ─────────────────────────────────────────────
# PATIENT IDENTITY HELPER
# ─────────────────────────────────────────────
def find_existing_patient(name: str, phone: str) -> dict | None:
    reports = load_db()
    for report in reports:
        if (report.get("name", "").strip().lower() == name.strip().lower()
                and report.get("phone", "").strip() == phone.strip()):
            return report
    return None

# ─────────────────────────────────────────────
# PATIENT REGISTRATION FORM (HIDDEN WHEN NOT LOGGED IN)
# ─────────────────────────────────────────────
if st.session_state["authenticated"]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📝 Patient Registration & Diagnosis")
    st.markdown("</div>", unsafe_allow_html=True)

    form_key = f"patient_form_{st.session_state['form_counter']}"

    with st.form(form_key):
        col1, col2 = st.columns(2)
        with col1:
            name   = st.text_input("Full Name *",       value=st.session_state["f_name"])
            age    = st.number_input("Age *", 1, 120,   value=int(st.session_state["f_age"]))
            gender_options = ["Select", "Male", "Female", "Other"]
            current_gender = st.session_state["f_gender"] if st.session_state["f_gender"] in gender_options else "Select"
            gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0
            gender = st.selectbox("Gender *", gender_options, index=gender_index)
        with col2:
            email  = st.text_input("Email Address * (@gmail.com)", value=st.session_state["f_email"])
            phone  = st.text_input("Phone Number * (10 digits)",   value=st.session_state["f_phone"])
            doctor = st.text_input("Referring Doctor",  value=st.session_state["f_doctor"])

        file        = st.file_uploader("Upload Chest X-ray *", type=["png","jpg","jpeg"])
        
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

    # ─────────────────────────────────────────
    # ANALYSIS LOGIC
    # ─────────────────────────────────────────
    if analyze_btn:

        if not name or not phone or not email or not file:
            st.error("❌ Name, Phone Number, Email, and X-ray image are all required.")
            st.stop()
        
        if not gender or gender == "Select":
            st.error("❌ Gender selection is mandatory. Please select Male, Female, or Other.")
            st.stop()
        
        if not validate_phone(phone):
            st.error("❌ Phone number must be exactly 10 digits (numbers only).")
            st.stop()
        
        if not validate_email(email):
            st.error("❌ Email must be a valid Gmail address (ending with @gmail.com).")
            st.stop()

        existing = find_existing_patient(name, phone)

        # Generate unique Report ID for each visit
        report_id = f"R-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        if existing:
            patient_id = existing["patient_id"]
            st.info(f"🔁 **Returning patient detected.** Patient ID: `{patient_id}`")
            st.info(f"📄 **New Report ID:** `{report_id}`")
        else:
            patient_id = f"P-{uuid.uuid4().hex[:6].upper()}"
            st.success(f"🆕 **New patient registered.** Patient ID: `{patient_id}`")
            st.info(f"📄 **Report ID:** `{report_id}`")

        image = Image.open(file)
        st.image(image, caption="Uploaded X-ray", width=400)

        with st.spinner("Analyzing X-ray with AI..."):
            prediction, _, _ = predict(image)

        st.success("✅ Analysis complete.")

        risk_level, risk_msg, severity = calculate_risk(prediction, {"age": age})

        st.subheader("🧠 AI Diagnosis Result")
        st.write(f"**Prediction:** {prediction['class']}")
        st.write(f"**Confidence:** {prediction['confidence']:.2%}")

        st.subheader("⚠️ Risk Assessment")
        st.write(f"**Risk Level:** {risk_level}")
        st.caption(risk_msg)

        with st.spinner("Generating attention heatmap..."):
            heatmap = generate_attention_map(model, image)
        st.image(heatmap, caption="AI Attention Map (Grad-CAM)", width=400)

        # Pass report_id to report generation
        report_bytes = generate_report(
            {"id": patient_id, "report_id": report_id, "age": age, "gender": gender, "doctor": doctor},
            prediction,
            (risk_level, risk_msg),
            heatmap
        )

        # ─────────────────────────────────────────
        # SAVE TO LOCAL STORAGE ONLY
        # ─────────────────────────────────────────
        with st.spinner("Saving patient data..."):
            # Create patient folder
            patient_folder = f"storage/{patient_id}"
            os.makedirs(patient_folder, exist_ok=True)
            
            # Save with report_id in filename to preserve history
            report_path = f"{patient_folder}/report_{report_id}.pdf"
            image_path = f"{patient_folder}/xray_{report_id}.jpg"
            
            # Save report PDF
            with open(report_path, "wb") as fw:
                fw.write(report_bytes)
            
            # Fix image mode for JPEG compatibility
            save_image = image.copy()
            if save_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', save_image.size, (255, 255, 255))
                rgb_image.paste(save_image, mask=save_image.split()[3] if len(save_image.split()) > 3 else None)
                save_image = rgb_image
            elif save_image.mode != 'RGB':
                save_image = save_image.convert('RGB')
            
            # Save X-ray image
            save_image.save(image_path, 'JPEG', quality=95)
            
            report_url = report_path
            image_url = image_path
            
            st.success(f"✅ Files saved to local storage. Report ID: {report_id}")

        # Save to database with report_id
        add_patient({
            "patient_id":   patient_id,
            "report_id":    report_id,
            "name":         name,
            "age":          age,
            "gender":       gender,
            "email":        email,
            "phone":        phone,
            "doctor":       doctor,
            "prediction":   prediction,
            "risk":         risk_level,
            "report_path":  report_url,
            "image_url":    image_url,
            "visit_date":   datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # ── EMAIL PORTION ─────────────────────────────────
        try:
            # Try to send email if we have a local file path
            if os.path.exists(report_url):
                result = send_email(
                    to_email=email,
                    file_path=report_url,
                    patient_name=name,
                    prediction=prediction
                )
                
                if isinstance(result, tuple):
                    success, message = result
                    if success:
                        st.success(f"📩 Professional report emailed to {email}")
                    else:
                        st.warning(f"⚠️ {message}")
                else:
                    st.success(f"📩 Report sent to {email}")
            else:
                st.info(f"📁 Report saved locally. Download from dashboard.")
        except Exception as e:
            st.info(f"📁 Report saved locally. Download from dashboard.")
        # ─────────────────────────────────────────────────────────

        st.success(f"✅ Visit recorded | Patient ID: `{patient_id}` | Report ID: `{report_id}`")

        st.session_state["f_name"]   = ""
        st.session_state["f_age"]    = 1
        st.session_state["f_gender"] = "Select"
        st.session_state["f_email"]  = ""
        st.session_state["f_phone"]  = ""
        st.session_state["f_doctor"] = ""
        st.session_state["form_counter"] += 1
        st.rerun()

    st.divider()

else:
    # Show locked message when not authenticated
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: rgba(22, 27, 34, 0.4); 
                border-radius: 20px; border: 1px dashed #30363d; margin: 1rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🔐</div>
        <h3 style="color: #58a6ff;">Registration Area Locked</h3>
        <p style="color: #8b949e;">Please sign in as administrator to register patients.</p>
        <p style="color: #8b949e; font-size: 0.85rem;">Use the <strong>Sign In</strong> button in the top right corner.</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PATIENT DASHBOARD (HIDDEN WHEN NOT LOGGED IN)
# ─────────────────────────────────────────────
if st.session_state["authenticated"]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📊 Patient Dashboard - All Visits")
    st.markdown("</div>", unsafe_allow_html=True)

    # Load all reports (each visit is a separate record)
    reports = load_db()

    st.markdown("### 🔍 Search & Filter Visits")

    col_search, col_filter, col_button = st.columns([2, 2, 1])

    with col_search:
        search_input = st.text_input(
            "Search by Patient ID / Name / Phone / Report ID",
            placeholder="e.g., P-AB12CD or John or R-20250115",
            key="search_input_field"
        )

    with col_filter:
        all_doctors = sorted({r.get("doctor", "").strip() for r in reports if r.get("doctor", "").strip()})
        doctor_options = ["All Doctors"] + all_doctors
        filter_input = st.selectbox(
            "Filter by Doctor",
            options=doctor_options,
            key="filter_input_field"
        )

    with col_button:
        st.write("")
        st.write("")
        search_clicked = st.button("🔍 Search", key="search_button", use_container_width=True)

    if search_clicked:
        st.session_state["search_query"] = search_input
        st.session_state["doctor_filter"] = filter_input
        st.session_state["trigger_search"] = True
        st.rerun()

    current_search = st.session_state.get("search_query", "")
    current_filter = st.session_state.get("doctor_filter", "All Doctors")

    def matches_search(record: dict, query: str) -> bool:
        if not query.strip():
            return True
        q = query.strip().lower()
        pid = record.get("patient_id", "").lower()
        pname = record.get("name", "").lower()
        pphone = record.get("phone", "").lower()
        report_id = record.get("report_id", "").lower()
        return (q in pid) or (q in pname) or (q in pphone) or (q in report_id)

    filtered_reports = [
        r for r in reports
        if matches_search(r, current_search)
        and (current_filter == "All Doctors" or r.get("doctor", "") == current_filter)
    ]

    if current_search or current_filter != "All Doctors":
        filter_text = []
        if current_search:
            filter_text.append(f'Search: "{current_search}"')
        if current_filter != "All Doctors":
            filter_text.append(f'Doctor: {current_filter}')
        
        st.caption(f"🔍 Showing results for: { ' | '.join(filter_text) }")
        
        if st.button("🗑️ Clear Filters", key="clear_filters"):
            st.session_state["search_query"] = ""
            st.session_state["doctor_filter"] = "All Doctors"
            st.session_state["trigger_search"] = False
            st.rerun()

    if len(reports) == 0:
        st.info("No visits recorded yet.")
    elif len(filtered_reports) == 0:
        st.warning("No records match your search or filter criteria.")
    else:
        st.caption(f"Showing **{len(filtered_reports)}** of **{len(reports)}** total visits")

        # Group by patient for better organization
        patients_grouped = {}
        for report in filtered_reports[::-1]:  # Newest first
            patient_id = report.get("patient_id")
            if patient_id not in patients_grouped:
                patients_grouped[patient_id] = []
            patients_grouped[patient_id].append(report)

        for patient_id, patient_reports in patients_grouped.items():
            patient_name = patient_reports[0].get("name", "Unknown")
            
            # Create an expander for each patient (showing all their visits)
            with st.expander(f"🧑 {patient_name} (ID: {patient_id}) - {len(patient_reports)} visit(s)"):
                
                for idx, report in enumerate(patient_reports):
                    # Each visit as a sub-expander
                    visit_label = f"📄 Visit {idx + 1} | Report ID: {report.get('report_id', 'N/A')} | Date: {report.get('visit_date', 'N/A')} | Risk: {report.get('risk', 'N/A')}"
                    
                    with st.expander(visit_label):
                        col_left, col_right = st.columns([2, 1])
                        
                        with col_left:
                            st.markdown(f"**👤 Patient ID:** {report.get('patient_id', 'N/A')}")
                            st.markdown(f"**📄 Report ID:** {report.get('report_id', 'N/A')}")
                            st.markdown(f"**📅 Visit Date:** {report.get('visit_date', 'N/A')}")
                            st.markdown(f"**👤 Name:** {report.get('name', 'N/A')}")
                            st.markdown(f"**🎂 Age:** {report.get('age', 'N/A')}")
                            st.markdown(f"**⚧ Gender:** {report.get('gender', 'N/A')}")
                            st.markdown(f"**📞 Phone:** {report.get('phone', 'N/A')}")
                            st.markdown(f"**📧 Email:** {report.get('email', 'N/A')}")
                            st.markdown(f"**👨‍⚕️ Doctor:** {report.get('doctor', 'N/A')}")
                            st.markdown(f"**🧠 Prediction:** {report.get('prediction', {}).get('class', 'N/A')}")
                            st.markdown(f"**📊 Confidence:** {report.get('prediction', {}).get('confidence', 0):.2%}")
                            st.markdown(f"**⚠️ Risk:** {report.get('risk', 'N/A')}")

                        with col_right:
                            rpath = report.get("report_path", "")
                            if rpath and os.path.exists(rpath):
                                with open(rpath, "rb") as rf:
                                    unique_key = f"dl_{report.get('report_id')}_{uuid.uuid4().hex[:6]}"
                                    st.download_button(
                                        "📄 Download Report",
                                        data=rf,
                                        file_name=f"{report.get('patient_id')}_{report.get('report_id')}.pdf",
                                        mime="application/pdf",
                                        key=unique_key
                                    )
                            
                            # Delete this specific report
                            delete_key = f"del_report_{report.get('report_id')}_{idx}"
                            if st.button("🗑️ Delete This Visit", key=delete_key):
                                st.session_state["delete_report_id"] = report.get("report_id")
                                st.rerun()

                        # Confirmation dialog for deleting single report
                        if st.session_state.get("delete_report_id") == report.get("report_id"):
                            st.error(f"⚠️ Are you sure you want to delete this visit (Report ID: {report.get('report_id')})?")
                            col_yes, col_no = st.columns(2)
                            
                            if col_yes.button("✅ Yes, Delete This Visit", key=f"confirm_del_report_{report.get('report_id')}"):
                                if delete_report(report.get("report_id")):
                                    st.success(f"✅ Visit {report.get('report_id')} deleted successfully!")
                                    st.session_state["delete_report_id"] = None
                                    st.rerun()
                                else:
                                    st.error("Failed to delete report")
                            
                            if col_no.button("❌ Cancel", key=f"cancel_del_report_{report.get('report_id')}"):
                                st.session_state["delete_report_id"] = None
                                st.rerun()
                
                # Option to delete ALL records for this patient
                st.markdown("---")
                col_del_all1, col_del_all2 = st.columns([1, 3])
                with col_del_all1:
                    if st.button(f"🗑️ Delete ALL Records for {patient_name}", key=f"del_all_{patient_id}"):
                        st.session_state[f"confirm_del_all_{patient_id}"] = True
                
                if st.session_state.get(f"confirm_del_all_{patient_id}", False):
                    st.error(f"⚠️ Are you sure you want to delete ALL {len(patient_reports)} records for {patient_name}? This cannot be undone!")
                    col_yes_all, col_no_all = st.columns(2)
                    if col_yes_all.button("✅ Yes, Delete All", key=f"confirm_all_yes_{patient_id}"):
                        if delete_patient(patient_id):
                            st.success(f"✅ All records for {patient_name} deleted successfully!")
                            st.session_state[f"confirm_del_all_{patient_id}"] = False
                            st.rerun()
                    if col_no_all.button("❌ Cancel", key=f"confirm_all_no_{patient_id}"):
                        st.session_state[f"confirm_del_all_{patient_id}"] = False
                        st.rerun()
    
    st.divider()

else:
    # Show locked message when not authenticated
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: rgba(22, 27, 34, 0.4); 
                border-radius: 20px; border: 1px dashed #30363d; margin: 1rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
        <h3 style="color: #58a6ff;">Dashboard Locked</h3>
        <p style="color: #8b949e;">Please sign in as administrator to view patient records.</p>
    </div>
    """, unsafe_allow_html=True)