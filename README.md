# 🏥 PneumoScreen AI

### Deep Learning-Based Pneumonia Detection & Reporting System

🚀 **PneumoScreen AI** is an end-to-end AI-powered system that detects pneumonia from chest X-rays and generates professional clinical reports with risk assessment and explainability.

---

## 📌 Overview

Pneumonia is a serious respiratory disease that requires early detection.
This project leverages **Deep Learning + Computer Vision** to assist in rapid screening using chest X-ray images.

💡 Built as a **real-world clinical prototype**, including:

* Patient registration system
* AI diagnosis
* Risk assessment
* Automated PDF report generation
* Email delivery system

---

## 🎯 Key Features

### 🧠 AI-Based Pneumonia Detection

* Classifies **Normal vs Pneumonia**
* Provides confidence score for predictions

### 🔍 Explainable AI (Grad-CAM)

* Visual heatmaps showing model focus regions
* Improves trust and interpretability

### ⚠️ Risk Assessment Engine

* Calculates severity based on prediction + patient age
* Provides actionable insights

### 📄 Professional Report Generation

* Generates **clinical-style PDF reports**
* Includes patient details, prediction, and risk

### 📧 Email Automation

* Sends reports directly to patient email
* Clean HTML-based medical email template

### 📊 Patient Dashboard

* Stores patient records
* Tracks multiple visits
* Search & filter system

---

## 🧠 Tech Stack

| Category        | Tools           |
| --------------- | --------------- |
| Language        | Python          |
| Deep Learning   | PyTorch         |
| Computer Vision | OpenCV          |
| UI              | Streamlit       |
| Explainability  | Grad-CAM        |
| Email Service   | Yagmail         |
| Data Handling   | NumPy, PIL      |
| Deployment      | Streamlit Cloud |

---

## 🏗️ Project Structure

```
pneumoscreen-ai/ 
├── app/ 
│   ├── main.py                 # Streamlit application entry point 
│   ├── backend/ 
│   │   ├── __init__.py 
│   │   ├── auth_db.py          # User authentication & management 
│   │   ├── db.py               # Patient data persistence 
│   │   └── mailer.py           # Email notification service 
│   └── utils/ 
│       ├── __init__.py 
│       ├── inference.py        # ViT model inference 
│       ├── gradcam.py          # Attention heatmap generation 
│       ├── report.py           # PDF report generation 
│       └── riskengine.py       # Risk assessment logic 
├── storage/                    # User-specific file storage 
├── database/                   # JSON database files 
├── requirements.txt            # Python dependencies 
└── README.md                   # Project documentation
```

---

## ⚙️ Installation Guide

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/pneumoscreen-ai.git
cd pneumoscreen-ai
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
streamlit run app/main.py
```

---

## 📊 Model Details

* Model: Vision Transformer (ViT) / ResNet (configurable)
* Dataset: Chest X-ray Pneumonia Dataset
* Classes:

  * NORMAL
  * PNEUMONIA

---

## 📸 Workflow

1. Register patient
2. Upload chest X-ray image
3. AI analyzes the image
4. View prediction + confidence
5. Generate Grad-CAM heatmap
6. Generate PDF report
7. Send report via email

---

## ⚠️ Disclaimer

This system is intended for **educational and research purposes only**.

❗ Not a replacement for professional medical diagnosis
❗ Always consult a certified healthcare professional

---

## 🚀 Future Improvements

* Multi-disease detection
* Cloud database integration (Firebase / AWS)
* Mobile application
* Doctor analytics dashboard
* Real-time hospital integration

---
Live app demo: https://pneumoscreenai-narczp6xlbyakaoszgcr6n.streamlit.app/
---

## 📬 Contact

**Sourav Das**
B.Tech AI & ML Student

📧 Email: souravdas5670@gmail.com
🔗 LinkedIn: https://www.linkedin.com/in/sourav-das-20032a2a7/
(Check my full documentation in linkedin under licences)
---

## 🧠 Tags

AI • Machine Learning • Deep Learning • Medical AI • Computer Vision
Healthcare AI • PyTorch • Streamlit • OpenCV
