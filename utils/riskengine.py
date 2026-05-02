# utils/risk_engine.py

def calculate_risk(prediction, patient=None):
    """
    Clinical Risk Engine
    --------------------
    Inputs:
        prediction: dict -> {"class": str, "confidence": float}
        patient: dict (optional) -> {"age": int, "gender": str}

    Returns:
        risk_level: str  (LOW / MEDIUM / HIGH / UNCERTAIN)
        message: str     (clinical explanation)
        severity_score: int (0–100)
    """

    pred_class = prediction["class"].upper()
    confidence = float(prediction["confidence"])

    age = None
    if patient and "age" in patient:
        age = patient["age"]

    # ─────────────────────────────────────────
    # 1. HANDLE LOW CONFIDENCE (UNCERTAIN CASE)
    # ─────────────────────────────────────────
    if confidence < 0.55:
        return (
            "UNCERTAIN",
            "Model confidence is low. Repeat scan or further diagnostic testing recommended.",
            int(confidence * 100)
        )

    # ─────────────────────────────────────────
    # 2. DISEASE CASE (BACTERIAL / PNEUMONIA)
    # ─────────────────────────────────────────
    if pred_class in ["BACTERIAL", "PNEUMONIA", "COVID", "TB"]:

        if confidence > 0.85:
            risk_level = "HIGH"
            message = "Strong radiological evidence of infection. Immediate clinical evaluation required."
        elif confidence > 0.65:
            risk_level = "MEDIUM"
            message = "Moderate probability of infection. Recommend further diagnostic confirmation."
        else:
            risk_level = "LOW"
            message = "Weak indicators. Monitor symptoms and consider follow-up."

        # 🔥 Age-based escalation (clinical realism)
        if age is not None and age >= 60:
            risk_level = "HIGH"
            message += " High-risk patient due to age."

        severity_score = int(confidence * 100)

    # ─────────────────────────────────────────
    # 3. NORMAL CASE
    # ─────────────────────────────────────────
    elif pred_class == "NORMAL":

        if confidence > 0.85:
            risk_level = "LOW"
            message = "No radiological abnormalities detected."
        elif confidence > 0.65:
            risk_level = "LOW"
            message = "Largely normal scan. Minor variations possible."
        else:
            risk_level = "MEDIUM"
            message = "Uncertain normal finding. Clinical correlation advised."

        severity_score = int((1 - confidence) * 100)

    # ─────────────────────────────────────────
    # 4. FALLBACK (UNKNOWN CLASS)
    # ─────────────────────────────────────────
    else:
        risk_level = "UNCERTAIN"
        message = "Unknown classification. Model output not recognized."
        severity_score = int(confidence * 100)

    return risk_level, message, severity_score