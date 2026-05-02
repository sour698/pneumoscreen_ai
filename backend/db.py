import json
import uuid
import os
from datetime import datetime

DB_DIR = "database"
PATIENTS_DIR = "storage"

# ─────────────────────────────────────────────
# HELPER: GET USER-SPECIFIC DATABASE PATH
# ─────────────────────────────────────────────
def get_user_db_path(user_email):
    """
    Get database path for specific user
    Each user has their own JSON file
    """
    # Create safe filename from email (replace special characters)
    safe_email = user_email.replace('@', '_at_').replace('.', '_dot_')
    user_db_path = os.path.join(DB_DIR, f"user_{safe_email}_patients.json")
    os.makedirs(DB_DIR, exist_ok=True)
    return user_db_path


def get_user_storage_path(user_email):
    """
    Get storage folder path for specific user
    Each user has their own storage folder
    """
    safe_email = user_email.replace('@', '_at_').replace('.', '_dot_')
    user_storage_path = os.path.join(PATIENTS_DIR, safe_email)
    os.makedirs(user_storage_path, exist_ok=True)
    return user_storage_path


# ─────────────────────────────────────────────
# LOAD DATABASE (USER-SPECIFIC)
# ─────────────────────────────────────────────
def load_db(user_email=None):
    """
    Load all patients for a specific user
    If no user_email provided, returns empty list
    """
    if not user_email:
        return []
    
    db_path = get_user_db_path(user_email)
    
    if not os.path.exists(db_path):
        return []
    
    try:
        with open(db_path, "r") as f:
            return json.load(f)
    except:
        return []


# ─────────────────────────────────────────────
# SAVE DATABASE (USER-SPECIFIC)
# ─────────────────────────────────────────────
def save_db(data, user_email):
    """
    Save all patients for a specific user
    """
    if not user_email:
        return False
    
    db_path = get_user_db_path(user_email)
    os.makedirs(DB_DIR, exist_ok=True)
    
    with open(db_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return True


# ─────────────────────────────────────────────
# ADD PATIENT VISIT (USER-SPECIFIC)
# ─────────────────────────────────────────────
def add_patient(record, user_email):
    """
    Add a new patient visit record for a specific user
    """
    if not user_email:
        return None
    
    data = load_db(user_email)
    
    # Create ID if not already provided
    if "patient_id" not in record:
        record["patient_id"] = "P-" + uuid.uuid4().hex[:6].upper()
    
    # Add timestamp and user reference
    record["created_at"] = datetime.now().isoformat()
    record["user_email"] = user_email
    
    data.append(record)
    save_db(data, user_email)
    
    return record["patient_id"]


# ─────────────────────────────────────────────
# DELETE SPECIFIC REPORT/VISIT (USER-SPECIFIC)
# ─────────────────────────────────────────────
def delete_report(report_id, user_email):
    """
    Delete a specific report/visit by its report_id for a specific user
    """
    if not user_email:
        return False
    
    data = load_db(user_email)
    
    # Find the report to delete
    report_to_delete = None
    for record in data:
        if record.get("report_id") == report_id:
            report_to_delete = record
            break
    
    if not report_to_delete:
        return False
    
    # Delete physical files
    report_path = report_to_delete.get("report_path", "")
    image_path = report_to_delete.get("image_url", "")
    
    if report_path and os.path.exists(report_path):
        try:
            os.remove(report_path)
        except:
            pass
    
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except:
            pass
    
    # Remove from database
    new_data = [record for record in data if record.get("report_id") != report_id]
    
    if len(data) == len(new_data):
        return False
    
    save_db(new_data, user_email)
    return True


# ─────────────────────────────────────────────
# DELETE ALL RECORDS FOR A PATIENT (USER-SPECIFIC)
# ─────────────────────────────────────────────
def delete_patient(patient_id, user_email):
    """
    Delete ALL records for a patient by patient_id for a specific user
    """
    if not user_email:
        return False
    
    data = load_db(user_email)
    
    # Find all records to delete files
    records_to_delete = [record for record in data if record.get("patient_id") == patient_id]
    
    # Delete physical files
    for record in records_to_delete:
        report_path = record.get("report_path", "")
        image_path = record.get("image_url", "")
        
        if report_path and os.path.exists(report_path):
            try:
                os.remove(report_path)
            except:
                pass
        
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
    
    # Remove from database
    new_data = [record for record in data if record.get("patient_id") != patient_id]
    
    if len(data) == len(new_data):
        return False
    
    save_db(new_data, user_email)
    return True


# ─────────────────────────────────────────────
# GET PATIENT HISTORY (ALL VISITS FOR A PATIENT)
# ─────────────────────────────────────────────
def get_patient_history(patient_id, user_email):
    """
    Get all visit records for a specific patient for a specific user
    """
    if not user_email:
        return []
    
    data = load_db(user_email)
    return [record for record in data if record.get("patient_id") == patient_id]


# ─────────────────────────────────────────────
# GET ALL REPORTS/VISITS FOR A USER
# ─────────────────────────────────────────────
def get_all_reports(user_email):
    """
    Get all reports/visits for a specific user
    """
    if not user_email:
        return []
    
    return load_db(user_email)


# ─────────────────────────────────────────────
# SEARCH REPORTS (USER-SPECIFIC)
# ─────────────────────────────────────────────
def search_reports(search_term, user_email):
    """
    Search reports by patient name, patient_id, phone, or report_id for a specific user
    """
    if not user_email:
        return []
    
    data = load_db(user_email)
    search_term = search_term.lower()
    
    results = []
    for record in data:
        if (search_term in record.get("name", "").lower() or
            search_term in record.get("patient_id", "").lower() or
            search_term in record.get("phone", "").lower() or
            search_term in record.get("report_id", "").lower()):
            results.append(record)
    
    return results


# ─────────────────────────────────────────────
# GET USER STATISTICS
# ─────────────────────────────────────────────
def get_user_stats(user_email):
    """
    Get statistics for a specific user
    """
    if not user_email:
        return {"total_patients": 0, "total_visits": 0}
    
    data = load_db(user_email)
    
    # Get unique patients
    unique_patients = set()
    for record in data:
        unique_patients.add(record.get("patient_id"))
    
    return {
        "total_patients": len(unique_patients),
        "total_visits": len(data)
    }


# ─────────────────────────────────────────────
# DELETE ALL USER DATA (USE WITH CAUTION)
# ─────────────────────────────────────────────
def delete_all_user_data(user_email):
    """
    DELETE ALL data for a specific user (for testing/debugging)
    Use with extreme caution!
    """
    if not user_email:
        return False
    
    # Delete database file
    db_path = get_user_db_path(user_email)
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Delete storage folder and all files
    storage_path = get_user_storage_path(user_email)
    if os.path.exists(storage_path):
        import shutil
        shutil.rmtree(storage_path)
    
    return True
