import json
import uuid
import os
from datetime import datetime

DB_PATH = "database/patients.json"

# ─────────────────────────────────────────────
# LOAD DATABASE (FROM LOCAL JSON FILE)
# ─────────────────────────────────────────────
def load_db():
    """
    Load all patients from local JSON file
    """
    if not os.path.exists(DB_PATH):
        return []

    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return []


# ─────────────────────────────────────────────
# SAVE DATABASE (TO LOCAL JSON FILE)
# ─────────────────────────────────────────────
def save_db(data):
    """
    Save all patients to local JSON file
    """
    os.makedirs("database", exist_ok=True)
    
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ─────────────────────────────────────────────
# ADD PATIENT VISIT (NEW RECORD FOR EACH VISIT)
# ─────────────────────────────────────────────
def add_patient(record):
    """
    Add a new patient visit record (each visit is separate)
    """
    data = load_db()
    
    # Create ID if not already provided
    if "patient_id" not in record:
        record["patient_id"] = "P-" + uuid.uuid4().hex[:6].upper()
    
    # Add timestamp
    record["created_at"] = datetime.now().isoformat()
    
    data.append(record)
    save_db(data)
    
    return record["patient_id"]


# ─────────────────────────────────────────────
# DELETE SPECIFIC REPORT/VISIT
# ─────────────────────────────────────────────
def delete_report(report_id):
    """
    Delete a specific report/visit by its report_id
    """
    data = load_db()
    
    new_data = [record for record in data if record.get("report_id") != report_id]
    
    if len(data) == len(new_data):
        return False  # nothing deleted
    
    save_db(new_data)
    
    # Also delete the physical files
    for record in data:
        if record.get("report_id") == report_id:
            report_path = record.get("report_path", "")
            image_path = record.get("image_url", "")
            
            if report_path and os.path.exists(report_path):
                os.remove(report_path)
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
            break
    
    return True


# ─────────────────────────────────────────────
# DELETE ALL RECORDS FOR A PATIENT
# ─────────────────────────────────────────────
def delete_patient(patient_id):
    """
    Delete ALL records for a patient by patient_id
    """
    data = load_db()
    
    # Find all records to delete files
    records_to_delete = [record for record in data if record.get("patient_id") == patient_id]
    
    # Delete physical files
    for record in records_to_delete:
        report_path = record.get("report_path", "")
        image_path = record.get("image_url", "")
        
        if report_path and os.path.exists(report_path):
            os.remove(report_path)
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
    
    # Remove from database
    new_data = [record for record in data if record.get("patient_id") != patient_id]
    
    if len(data) == len(new_data):
        return False
    
    save_db(new_data)
    return True


# ─────────────────────────────────────────────
# GET PATIENT HISTORY (ALL VISITS)
# ─────────────────────────────────────────────
def get_patient_history(patient_id):
    """
    Get all visit records for a specific patient
    """
    data = load_db()
    return [record for record in data if record.get("patient_id") == patient_id]


# ─────────────────────────────────────────────
# GET ALL REPORTS/VISITS
# ─────────────────────────────────────────────
def get_all_reports():
    """
    Get all reports/visits (each record is a separate visit)
    """
    return load_db()


# ─────────────────────────────────────────────
# SEARCH REPORTS
# ─────────────────────────────────────────────
def search_reports(search_term):
    """
    Search reports by patient name, patient_id, phone, or report_id
    """
    data = load_db()
    search_term = search_term.lower()
    
    results = []
    for record in data:
        if (search_term in record.get("name", "").lower() or
            search_term in record.get("patient_id", "").lower() or
            search_term in record.get("phone", "").lower() or
            search_term in record.get("report_id", "").lower()):
            results.append(record)
    
    return results