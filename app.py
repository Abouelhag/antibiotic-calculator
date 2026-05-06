# app.py - Antibiotic Calculator (Logo, Background, PDF fixed)
import streamlit as st
import json
from fpdf import FPDF
import tempfile
import base64
from datetime import datetime
import os

# ---------- إعداد الصفحة ----------
st.set_page_config(
    page_title="Antibiotic Dose Calculator",
    page_icon="💊",
    layout="centered"
)

# ---------- عرض الشعار إن وُجد (logo.jpeg) ----------
if os.path.exists("logo.jpeg"):
    st.image("logo.jpeg", width=180)
else:
    st.write("")  # فراغ بسيط

# ---------- خلفية متدرجة (تعمل دائماً) ----------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(145deg, #caf0f8 0%, #90e0ef 100%);
        background-attachment: fixed;
    }
    div[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.85);
        border-radius: 16px;
        margin: 10px;
        padding: 10px;
    }
    .stButton > button {
        background-color: #0077b6;
        color: white;
        border-radius: 30px;
        padding: 10px 24px;
        font-weight: bold;
        font-size: 16px;
        border: none;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #023e8a;
        transform: scale(1.02);
    }
    h1, h2, h3 {
        color: #03045e;
    }
    .stSelectbox, .stNumberInput, .stRadio > div {
        background-color: rgba(255,255,255,0.7);
        border-radius: 12px;
        padding: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- دالة تنظيف النصوص من الأحرف غير اللاتينية (لـ PDF) ----------
def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "–": "-",
        "—": "-",
        "’": "'",
        "“": '"',
        "”": '"',
        "…": "...",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.encode('latin-1', errors='ignore').decode('latin-1')

# ---------- تحميل قاعدة البيانات ----------
def load_drugs():
    with open("drugs.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- إنشاء PDF مع تنظيف النصوص ----------
def create_prescription_pdf(patient_info, drug_name, drug_details, dose_text, crcl_value):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 12, txt="Antibiotic Prescription", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt=sanitize_text(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align="R")
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="Patient Information:", ln=True)
    pdf.set_font("Arial", "", 11)
    for key, val in patient_info.items():
        pdf.cell(200, 7, txt=sanitize_text(f"{key}: {val}"), ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="Prescribed Medication:", ln=True)
    pdf.set_font("Arial", "", 11)
    med_text = sanitize_text(f"Drug: {drug_name}\nGeneric: {drug_details.get('generic', 'N/A')}\nDosage: {dose_text}")
    pdf.multi_cell(0, 7, txt=med_text)
    if crcl_value:
        pdf.ln(3)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(200, 6, txt=sanitize_text(f"Creatinine Clearance (CrCl): {crcl_value:.1f} mL/min"), ln=True)
    pdf.ln(8)
    pdf.cell(200, 8, txt="Doctor Signature: _________________", ln=True)
    pdf.cell(200, 6, txt="(This is an electronic prescription for reference only)", ln=True)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name

# ---------- المحتوى الرئيسي ----------
def main_calculator():
    st.title("💊 Antibiotic Dose Calculator")
    st.markdown("### Evidence-based dosing for adults and pediatrics")
    
    drugs_db = load_drugs()
    drug_names = list(drugs_db.keys())
    
    with st.sidebar:
        st.header("📋 Patient Data")
        age = st.number_input("Age (years)", min_value=0, max_value=120, step=1, value=50)
        weight = st.number_input("Weight (kg)", min_value=1.0, max_value=250.0, step=1.0, value=70.0)
        gender = st.radio("Gender", ["Male", "Female"])
        serum_creatinine = st.number_input("Serum Creatinine (mg/dL)", min_value=0.1, step=0.1, value=1.0)
        if gender == "Male":
            crcl = ((140 - age) * weight) / (72 * serum_creatinine)
        else:
            crcl = ((140 - age) * weight) / (72 * serum_creatinine) * 0.85
        st.metric("Creatinine Clearance (CrCl)", f"{crcl:.1f} mL/min")
        liver_status = st.selectbox("Liver disease severity", ["None", "Moderate", "Severe"])
        route = st.radio("Route", ["Oral", "IV (intravenous)"])
    
    drug_choice = st.selectbox("🔎 Choose antibiotic", drug_names)
    drug = drugs_db[drug_choice]
    
    if st.button("📐 Calculate Dose", type="primary"):
        st.subheader("📄 Prescription Result")
        st.write(f"**Generic:** {drug['generic']}")
        st.write(f"**Brands:** {', '.join(drug['brands'])}")
        preg_cat = drug.get("pregnancy_category", "N/A")
        st.write(f"**Pregnancy category:** {preg_cat}")
        if drug.get("lactation_safe"):
            st.success("✅ Compatible with breastfeeding (check local guidelines)")
        else:
            st.warning("⚠️ Caution during breastfeeding – consult specialist")
        
        dosing = drug["dosing"]
        dose_text = ""
        if age >= 18:
            if route.lower() in dosing.get("adult", {}):
                dose_text = dosing["adult"][route.lower()]
            else:
                dose_text = dosing["adult"].get("oral", "No data for this route")
            st.info(f"💊 **Normal adult dose ({route}):** {dose_text}")
        else:
            if "pediatric_weight_based" in dosing:
                p = dosing["pediatric_weight_based"]
                if "min_mg_per_kg_per_day" in p:
                    low = p["min_mg_per_kg_per_day"] * weight
                    high = p["max_mg_per_kg_per_day"] * weight
                    if "max_daily_mg" in p:
                        high = min(high, p["max_daily_mg"])
                    dose_text = f"{low:.0f}–{high:.0f} mg/day {p['interval']}"
                    st.info(f"💊 **Pediatric dose:** {dose_text}")
                elif "day1_mg_per_kg" in p:
                    day1 = p["day1_mg_per_kg"] * weight
                    day2_5 = p["days2to5_mg_per_kg"] * weight
                    dose_text = f"{day1:.0f} mg day 1, then {day2_5:.0f} mg days 2–5"
                    st.info(f"💊 **Pediatric dose:** {dose_text}")
            else:
                dose_text = drug.get("pediatric_note", "No pediatric dosing available – consult specialist")
                st.warning(dose_text)
        
        if "renal_adjustment" in drug:
            renal_rule = drug["renal_adjustment"]
            if isinstance(renal_rule, dict):
                if crcl < 10 and "crcl_lt_10" in renal_rule:
                    st.info(f"🧪 **Renal adjustment (CrCl <10):** {renal_rule['crcl_lt_10']}")
                elif crcl < 30 and "crcl_lt_30" in renal_rule:
                    st.info(f"🧪 **Renal adjustment (CrCl <30):** {renal_rule['crcl_lt_30']}")
                elif crcl < 50 and "crcl_30_50" in renal_rule:
                    st.info(f"🧪 **Renal adjustment (CrCl 30–50):** {renal_rule['crcl_30_50']}")
            else:
                if crcl < 50:
                    st.info(f"🧪 **Renal note:** {renal_rule}")
        
        if liver_status != "None" and "hepatic_adjustment" in drug:
            st.info(f"🌿 **Hepatic adjustment ({liver_status} liver disease):** {drug['hepatic_adjustment']}")
        
        st.caption("⚠️ **Disclaimer:** Educational use only. Always consult a physician.")
        
        patient_info = {
            "Age": f"{age} years",
            "Weight": f"{weight} kg",
            "Gender": gender,
            "Serum Creatinine": f"{serum_creatinine} mg/dL",
            "CrCl": f"{crcl:.1f} mL/min",
            "Liver": liver_status
        }
        pdf_path = create_prescription_pdf(patient_info, drug_choice, drug, dose_text, crcl if crcl else None)
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="prescription_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf" style="background-color:#28a745; color:white; padding:10px 24px; text-decoration:none; border-radius:30px; font-weight:bold;">📥 Download Prescription (PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main_calculator()
