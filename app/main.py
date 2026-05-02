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
from backend.auth_db import create_user, authenticate_user, get_user
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
    
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; min-height: 70vh;">
        <div style="background: linear-gradient(135deg, #1f6feb11, #388bfd11); 
                    border-radius: 20px; padding: 2.5rem; text-align: center;
                    border: 1px solid #1f6feb33; max-width: 450px; width: 100%;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🏥</div>
            <h1 style="color: #58a6ff; margin-bottom: 0.5rem;">PneumoScreen AI</h1>
            <p style="color: #8b949e; margin-bottom: 1.5rem;">Deep Learning-Based Pneumonia Screening & Reporting System</p>
    """, unsafe_allow_html=True)
    
    # Toggle between Login and Signup
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
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = user["email"]
                    st.session_state["user_name"] = user["name"]
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    
    else:  # signup
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

# Show login screen if not logged in
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
# PATIENT IDENTITY HELPER (USER-SPECIFIC)
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
        name   = st.text_input("Full Name *",       value=st.session_state["f_name"])
        age    = st.number_input("Age *", 1, 120,   value=int(st.session_state["f_age"]))
        gender_options = ["Select", "Male", "Female", "Other"]
        current_gender = st.session_state["f_gender"] if st.session_state["f_gender"] in gender_options else "Select"
        gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0
        gender = st.selectbox("Gender *", gender_options, index=gender_index)
    with col2:
        email  = st.text_input("Patient Email * (@gmail.com)", value=st.session_state["f_email"])
        phone  = st.text_input("Phone Number * (10 digits)",   value=st.session_state["f_phone"])
        doctor = st.text_input("Referring Doctor",  value=st.session_state["f_doctor"])

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
        st.error("❌ Gender selection is mandatory. Please select Male, Female, or Other.")
        st.stop()
    
    if not validate_phone(phone):
        st.error("❌ Phone number must be exactly 10 digits (numbers only).")
        st.stop()
    
    if not validate_email(email):
        st.error("❌ Patient email must be a valid Gmail address (ending with @gmail.com).")
        st.stop()

    existing = find_existing_patient(name, phone)

    # Generate unique Report ID for each visit
    now_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y%m%d")
    report_id = f"R-{now_str}-{uuid.uuid4().hex[:6].upper()}"

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

    report_bytes = generate_report(
        {"id": patient_id, "report_id": report_id, "age": age, "gender": gender, "doctor": doctor},
        prediction,
        (risk_level, risk_msg),
        heatmap
    )

    # ─────────────────────────────────────────
    # SAVE TO USER-SPECIFIC STORAGE
    # ─────────────────────────────────────────
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
        "report_path":  report_path,
        "image_url":    image_path,
        "visit_date":   datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    }, st.session_state["user_email"])

    # ── EMAIL PORTION ─────────────────────────────────
    try:
        if os.path.exists(report_path):
            result = send_email(
                to_email=email,
                file_path=report_path,
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
# PATIENT DASHBOARD (USER-SPECIFIC)
# ─────────────────────────────────────────────
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("📊 Patient Dashboard - My Patients")
st.markdown("</div>", unsafe_allow_html=True)

# Load only current user's reports
reports = load_db(st.session_state["user_email"])

st.markdown("### 🔍 Search & Filter")

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
        st.rerun()

if len(reports) == 0:
    st.info("📋 No patients registered yet. Use the form above to add your first patient.")
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
        
        with st.expander(f"🧑 {patient_name} (ID: {patient_id}) - {len(patient_reports)} visit(s)"):
            
            for idx, report in enumerate(patient_reports):
                visit_label = f"📄 Visit {idx + 1} | Report: {report.get('report_id', 'N/A')} | Date: {report.get('visit_date', 'N/A')} | Risk: {report.get('risk', 'N/A')}"
                
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
                        
                        delete_key = f"del_report_{report.get('report_id')}_{idx}"
                        if st.button("🗑️ Delete This Visit", key=delete_key):
                            st.session_state["delete_report_id"] = report.get("report_id")
                            st.rerun()

                    if st.session_state.get("delete_report_id") == report.get("report_id"):
                        st.error(f"⚠️ Delete this visit (Report: {report.get('report_id')})?")
                        col_yes, col_no = st.columns(2)
                        if col_yes.button("✅ Yes, Delete", key=f"confirm_del_{report.get('report_id')}"):
                            if delete_report(report.get("report_id"), st.session_state["user_email"]):
                                st.success(f"✅ Visit {report.get('report_id')} deleted!")
                                st.session_state["delete_report_id"] = None
                                st.rerun()
                        if col_no.button("❌ Cancel", key=f"cancel_del_{report.get('report_id')}"):
                            st.session_state["delete_report_id"] = None
                            st.rerun()
            
            st.markdown("---")
            col_del_all1, col_del_all2 = st.columns([1, 3])
            with col_del_all1:
                if st.button(f"🗑️ Delete ALL Records for {patient_name}", key=f"del_all_{patient_id}"):
                    st.session_state[f"confirm_del_all_{patient_id}"] = True
            
            if st.session_state.get(f"confirm_del_all_{patient_id}", False):
                st.error(f"⚠️ Delete ALL {len(patient_reports)} records for {patient_name}?")
                col_yes_all, col_no_all = st.columns(2)
                if col_yes_all.button("✅ Yes, Delete All", key=f"confirm_all_yes_{patient_id}"):
                    if delete_patient(patient_id, st.session_state["user_email"]):
                        st.success(f"✅ All records for {patient_name} deleted!")
                        st.session_state[f"confirm_del_all_{patient_id}"] = False
                        st.rerun()
                if col_no_all.button("❌ Cancel", key=f"confirm_all_no_{patient_id}"):
                    st.session_state[f"confirm_del_all_{patient_id}"] = False
                    st.rerun()

st.divider()
