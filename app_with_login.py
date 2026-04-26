# app_with_login.py - Complete antibiotic calculator with manual PayPal & admin upgrade
import streamlit as st
import json
from db import create_user, authenticate_user, upgrade_to_premium

# --------------------------------------------------
# Load drug database (only used for premium content)
# --------------------------------------------------
def load_drugs():
    with open("drugs.json", "r") as f:
        return json.load(f)

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Ricos Biology Journal - Antibiotic Calculator",
    page_icon="💊",
    layout="centered"
)

# --------------------------------------------------
# Helper functions for UI
# --------------------------------------------------
def login_signup_page():
    st.title("💊 Ricos Biology Journal")
    st.markdown("### Antibiotic Dose Calculator")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary"):
            user = authenticate_user(email, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = user['email']
                st.session_state['is_premium'] = bool(user['is_premium'])
                st.rerun()
            else:
                st.error("Invalid email or password")

    with tab2:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        if st.button("Sign Up"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                if create_user(new_email, new_password):
                    st.success("Account created! Please log in.")
                else:
                    st.error("User already exists. Try a different email.")

def upgrade_section():
    """Shows a simple PayPal link (no webhook). You receive email, then upgrade manually via admin panel."""
    st.markdown("---")
    st.header("✨ Upgrade to Premium")
    st.write("Get access to **ALL antibiotics** and advanced features for a **one-time payment of $1.99 USD**.")
    st.markdown("[👉 Click here to pay with PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=drabouelhag5@gmail.com&item_name=Ricos%20Biology%20Journal%20-%20Premium%20Upgrade&amount=1.99&currency_code=USD)")
    st.caption("After payment, we will upgrade your account within 24 hours. Contact support@ricosbiology.net if urgent.")

def display_premium_content():
    """Full antibiotic calculator – premium users see everything."""
    st.subheader("🎉 Premium Content – Full Antibiotic Database")
    st.success("You have full access to all antibiotics and advanced features.")

    drugs_db = load_drugs()
    drug_names = list(drugs_db.keys())

    # Sidebar inputs for premium features
    with st.sidebar:
        st.header("Patient Data")
        age = st.number_input("Age (years)", min_value=0, step=1, value=50)
        weight = st.number_input("Weight (kg)", min_value=0.0, step=1.0, value=70.0)
        gender = st.radio("Gender", ["Male", "Female"])
        serum_creatinine = st.number_input("Serum Creatinine (mg/dL)", min_value=0.1, step=0.1, value=1.0)

        # CrCl calculation
        if gender == "Male":
            crcl = ((140 - age) * weight) / (72 * serum_creatinine)
        else:
            crcl = ((140 - age) * weight) / (72 * serum_creatinine) * 0.85
        st.metric("Creatinine Clearance (CrCl)", f"{crcl:.1f} mL/min")

        liver_status = st.selectbox("Liver disease severity", ["None", "Moderate", "Severe"])
        route = st.radio("Route", ["Oral", "IV (intravenous)"])

    # Main drug selection
    drug_choice = st.selectbox("💊 Choose antibiotic", drug_names)
    drug = drugs_db[drug_choice]

    if st.button("Calculate Dose", type="primary"):
        st.subheader("📋 Prescription Result")
        st.write(f"**Generic:** {drug['generic']}")
        st.write(f"**Brands:** {', '.join(drug['brands'])}")

        # Pregnancy & lactation
        preg_cat = drug.get("pregnancy_category", "N/A")
        st.write(f"**Pregnancy category:** {preg_cat}")
        if drug.get("lactation_safe"):
            st.success("✅ Compatible with breastfeeding (check local guidelines)")
        else:
            st.warning("⚠️ Caution during breastfeeding – consult specialist")

        # Adult vs pediatric
        dosing = drug["dosing"]
        if age >= 18:
            # Adult dosing
            if route.lower() in dosing.get("adult", {}):
                dose_text = dosing["adult"][route.lower()]
            else:
                dose_text = dosing["adult"].get("oral", "No data for this route")
            st.info(f"💊 **Normal adult dose ({route}):** {dose_text}")
        else:
            # Pediatric
            if "pediatric_weight_based" in dosing:
                p = dosing["pediatric_weight_based"]
                if "min_mg_per_kg_per_day" in p:
                    low = p["min_mg_per_kg_per_day"] * weight
                    high = p["max_mg_per_kg_per_day"] * weight
                    if "max_daily_mg" in p:
                        high = min(high, p["max_daily_mg"])
                    st.info(f"💊 **Pediatric dose:** {low:.0f}–{high:.0f} mg/day {p['interval']}")
                elif "day1_mg_per_kg" in p:
                    day1 = p["day1_mg_per_kg"] * weight
                    day2_5 = p["days2to5_mg_per_kg"] * weight
                    st.info(f"💊 **Pediatric dose:** {day1:.0f} mg day 1, then {day2_5:.0f} mg days 2–5")
            else:
                st.warning(drug.get("pediatric_note", "No pediatric dosing available – consult specialist"))

        # Renal adjustment
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

        # Hepatic adjustment
        if liver_status != "None" and "hepatic_adjustment" in drug:
            st.info(f"🌿 **Hepatic adjustment ({liver_status} liver disease):** {drug['hepatic_adjustment']}")

        st.caption("⚠️ **Disclaimer:** Educational use only. Always consult a physician.")

def display_free_content():
    """Limited calculator – free users see only 3 basic drugs."""
    st.subheader("🔓 Free Access")
    st.write("You have access to a limited set of antibiotics (Amoxicillin, Ciprofloxacin, Metronidazole).")
    st.write("Upgrade to Premium to unlock all 15+ antibiotics and advanced features.")

    st.markdown("---")
    age = st.number_input("Age (years)", min_value=0, step=1, value=30)
    weight = st.number_input("Weight (kg)", min_value=0.0, step=1.0, value=70.0)
    drug = st.selectbox("Choose antibiotic", ["Amoxicillin", "Ciprofloxacin", "Metronidazole"])

    if st.button("Calculate Dose (Free)"):
        st.subheader("Result")
        if drug == "Amoxicillin":
            if age >= 18:
                st.info("💊 500–875 mg every 12 hours OR 250–500 mg every 8 hours")
            else:
                low = 20 * weight
                high = 45 * weight
                if high > 3000:
                    high = 3000
                st.info(f"💊 {low:.0f}–{high:.0f} mg per day, divided every 8–12 hours")
        elif drug == "Ciprofloxacin":
            if age >= 18:
                st.info("💊 500–750 mg every 12 hours")
            else:
                st.warning("Not recommended for children under 18")
        else:  # Metronidazole
            if age >= 18:
                st.info("💊 500 mg every 8 hours OR 750 mg every 8 hours")
            else:
                low = 15 * weight
                high = 35 * weight
                if high > 4000:
                    high = 4000
                st.info(f"💊 {low:.0f}–{high:.0f} mg per day, divided every 8 hours")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_signup_page()
        return

    # Logged in
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state['user_email']}**")
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("---")
        st.caption("Ricos Biology Journal\n[https://ricosbiology.net](https://ricosbiology.net)")

        # ------------- ADMIN PANEL -------------
        ADMIN_EMAIL = "info@ricosbiology.net"   # <-- Your admin email (the one you log in with)
        if st.session_state['user_email'] == ADMIN_EMAIL:
            st.markdown("---")
            st.subheader("🔐 Admin Panel")
            user_to_upgrade = st.text_input("User email to upgrade (premium)")
            if st.button("Upgrade to Premium"):
                if user_to_upgrade:
                    upgrade_to_premium(user_to_upgrade)
                    st.success(f"✅ Upgraded {user_to_upgrade} to premium!")
                else:
                    st.error("Please enter an email address.")
        # --------------------------------------

    st.title("💊 Antibiotic Dose Calculator")

    if st.session_state.get('is_premium', False):
        display_premium_content()
    else:
        display_free_content()
        upgrade_section()

if __name__ == "__main__":
    main()
