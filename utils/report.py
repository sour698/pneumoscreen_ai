from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
from datetime import datetime


def generate_report(patient, prediction, risk, heatmap_image):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    # Custom styles
    center_style = ParagraphStyle(
        "center",
        parent=styles["Title"],
        alignment=1
    )
    
    # Create a smaller style for the subtitle
    subtitle_style = ParagraphStyle(
        "subtitle",
        parent=styles["Heading3"],
        alignment=1,
        fontSize=10
    )

    heading_style = ParagraphStyle(
        "heading",
        parent=styles["Heading2"],
        spaceAfter=6
    )

    content = []

    # ─────────────────────────────────────────
    # HEADER - UPDATED (Two lines for better display)
    # ─────────────────────────────────────────
    content.append(Paragraph("PneumoScreen AI", center_style))
    content.append(Spacer(1, 3))
    content.append(Paragraph("Deep Learning-Based Pneumonia Screening & Reporting System", subtitle_style))
    content.append(Spacer(1, 15))

    # ─────────────────────────────────────────
    # PATIENT DETAILS TABLE (IMPROVED)
    # ─────────────────────────────────────────
    table_data = [
        ["Patient ID", patient.get("id", "N/A"), "Report ID", patient.get("report_id", "N/A")],
        ["Date", datetime.now().strftime("%d-%m-%Y %H:%M"), "Age / Sex", f"{patient.get('age', 'N/A')} / {patient.get('gender', 'N/A')}"],
        ["Ref. Doctor", patient.get("doctor", "Not Specified"), "Visit Date", datetime.now().strftime("%d-%m-%Y")]
    ]

    table = Table(table_data, colWidths=[100, 150, 100, 150])
    table.setStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)
    ])

    content.append(table)
    content.append(Spacer(1, 15))

    # ─────────────────────────────────────────
    # INVESTIGATION TITLE
    # ─────────────────────────────────────────
    content.append(Paragraph("<b>CHEST X-RAY (PA VIEW)</b>", heading_style))
    content.append(Spacer(1, 10))

    # ─────────────────────────────────────────
    # FINDINGS (CLINICAL LANGUAGE)
    # ─────────────────────────────────────────
    content.append(Paragraph("<b>Findings:</b>", heading_style))

    if prediction["class"] == "BACTERIAL":
        findings = """
        Patchy areas of increased opacity are noted in the lung fields,
        suggestive of infective pathology. No pleural effusion is identified.
        Cardiac silhouette appears within normal limits.
        Bony thoracic structures are unremarkable.
        """
    else:
        findings = """
        Lung fields appear clear with no focal consolidation.
        No pleural effusion or pneumothorax detected.
        Cardiac silhouette is within normal limits.
        Visualized bony thoracic cage is unremarkable.
        """

    content.append(Paragraph(findings, styles["Normal"]))
    content.append(Spacer(1, 12))

    # ─────────────────────────────────────────
    # IMPRESSION
    # ─────────────────────────────────────────
    content.append(Paragraph("<b>Impression:</b>", heading_style))

    impression = f"""
    {prediction['class']} detected with confidence of {prediction['confidence']:.2%}.
    """

    content.append(Paragraph(impression, styles["Normal"]))
    content.append(Spacer(1, 12))

    # ─────────────────────────────────────────
    # RISK
    # ─────────────────────────────────────────
    content.append(Paragraph("<b>Risk Assessment:</b>", heading_style))
    content.append(Paragraph(f"{risk[0]} - {risk[1]}", styles["Normal"]))
    content.append(Spacer(1, 12))

    # ─────────────────────────────────────────
    # ADVICE
    # ─────────────────────────────────────────
    content.append(Paragraph("<b>Advice:</b>", heading_style))

    if prediction["class"] == "BACTERIAL":
        advice = "Clinical correlation is advised. Further evaluation and treatment recommended."
    else:
        advice = "No active pathology detected. Routine follow-up if clinically indicated."

    content.append(Paragraph(advice, styles["Normal"]))
    content.append(Spacer(1, 15))

    # ─────────────────────────────────────────
    # HEATMAP IMAGE (SAFE SAVE)
    # ─────────────────────────────────────────
    img_path = "temp_heatmap.jpg"

    if heatmap_image.mode != "RGB":
        heatmap_image = heatmap_image.convert("RGB")

    heatmap_image.save(img_path)

    content.append(Image(img_path, width=300, height=300))
    content.append(Spacer(1, 15))

    # ─────────────────────────────────────────
    # SIGNATURE
    # ─────────────────────────────────────────
    content.append(Paragraph("__________________________", styles["Normal"]))
    content.append(Paragraph("Consultant Radiologist", styles["Normal"]))
    content.append(Spacer(1, 10))

    # DISCLAIMER
    content.append(Paragraph(
        "<i>This is an AI-assisted report. Final diagnosis should be confirmed by a certified radiologist.</i>",
        styles["Italic"]
    ))

    # Build
    doc.build(content)

    buffer.seek(0)
    return buffer.getvalue()