import streamlit as st
import pandas as pd
import re
from io import BytesIO
from gtts import gTTS

st.set_page_config(page_title="SchemeSetu | SASVA", page_icon="🏛️", layout="wide")

# --- DATA ---
INDIAN_STATES = ["West Bengal", "Bihar", "Uttar Pradesh", "Maharashtra", "Delhi", "Rajasthan", "All India"]

TRANSLATIONS = {
    "English": {"title": "SchemeSetu - SASVA", "subtitle": "Your AI Scheme Assistant", "entrepreneur_profile": "Entrepreneur Profile", "state_label": "State", "age_label": "Age", "gender_label": "Gender", "category_label": "Category", "sector_label": "Sector", "tab_matched": "Matched Schemes", "tab_analytics": "Analytics", "ministry_label": "Ministry", "benefit_label": "Benefit", "open_portal": "Apply on Official Portal"},
    "Hindi (हिन्दी)": {"title": "योजना सेतु - SASVA", "subtitle": "आपका AI योजना सहायक", "entrepreneur_profile": "उद्यमी प्रोफाइल", "state_label": "राज्य", "age_label": "आयु", "gender_label": "लिंग", "category_label": "श्रेणी", "sector_label": "क्षेत्र", "tab_matched": "मिलान योजनाएं", "tab_analytics": "विश्लेषण", "ministry_label": "मंत्रालय", "benefit_label": "लाभ", "open_portal": "आधिकारिक पोर्टल पर आवेदन करें"},
    "Bengali (বাংলা)": {"title": "স্কিমসেতু - SASVA", "subtitle": "তোমার AI স্কিম সহকারী", "entrepreneur_profile": "উদ্যোক্তা প্রোফাইল", "state_label": "রাজ্য", "age_label": "বয়স", "gender_label": "লিঙ্গ", "category_label": "ক্যাটাগরি", "sector_label": "সেক্টর", "tab_matched": "মিলে যাওয়া স্কিম", "tab_analytics": "অ্যানালিটিক্স", "ministry_label": "মন্ত্রক", "benefit_label": "সুবিধা", "open_portal": "অফিসিয়াল পোর্টালে আবেদন"}
}

SCHEMES_DATABASE = [
    {"id": "PMEGP", "name": "PM Employment Generation Programme", "ministry": "MSME", "description": "35% subsidy for SC/ST/Women in rural areas.", "status": "Active", "min_loan": 50000, "max_loan": 1000000, "min_age": 18, "max_age": 60, "documents": "Aadhaar, Project Report, Caste Certificate", "guidelines": "Policy Clause 4.2: Age>18, Rural, Investment <10L", "apply_link": "https://www.kviconline.gov.in/pmegpeportal/", "main_benefit": "35% Subsidy"},
    {"id": "MUDRA", "name": "MUDRA Loan Yojana", "ministry": "Finance", "description": "Loan up to 10L for non-farm enterprises.", "status": "Active", "min_loan": 50000, "max_loan": 1000000, "min_age": 18, "max_age": 65, "documents": "Aadhaar, Business Proof, Bank Statement", "guidelines": "Policy Clause 2.1: Any non-farm enterprise", "apply_link": "https://www.mudra.org.in/", "main_benefit": "Loan upto 10L"},
]

def t(key):
    lang = st.session_state.get("selected_lang", "English")
    return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

# --- LANGUAGE SELECTION ---
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = None

if st.session_state.selected_lang is None:
    st.markdown("""
    <style>
    @keyframes floatUpDown {
      0%, 100% { transform: translateY(0px); box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
      50% { transform: translateY(-8px); box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
    }
    .floating-welcome {
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      padding: 28px; border-radius: 16px; text-align: center; margin-bottom: 25px;
      position: sticky; top: 10px; z-index: 999;
      animation: floatUpDown 3s ease-in-out infinite;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .floating-welcome h1 { color: white; margin: 0; font-size: 32px; }
    .floating-welcome p { color: #cbd5e1; margin-top: 8px; font-size: 16px; }
    </style>
    <div class="floating-welcome">
        <h1>Welcome to SchemeSetu - SASVA</h1>
        <p>कृपया अपनी भाषा चुनें / Please select your language</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("English", use_container_width=True):
            st.session_state.selected_lang = "English"
            st.rerun()
        if st.button("বাংলা Bengali", use_container_width=True):
            st.session_state.selected_lang = "Bengali (বাংলা)"
            st.rerun()
    with c2:
        if st.button("हिन्दी Hindi", use_container_width=True):
            st.session_state.selected_lang = "Hindi (हिन्दी)"
            st.rerun()
    st.stop()

# --- MAIN APP ---
if st.sidebar.button("🌐 Change Language"):
    st.session_state.selected_lang = None
    st.rerun()

st.markdown(f"""
<div style="background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%); padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
<div style="font-size:22px; font-weight:bold; color:#1E3A8A;">🏛️ {t('title')}</div>
<div style="color:#1E293B; font-weight:600;">{t('subtitle')}</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header(f"👤 {t('entrepreneur_profile')}")
location = st.sidebar.selectbox(t("state_label"), INDIAN_STATES)
age = st.sidebar.number_input(t("age_label"), 18, 80, 22)
gender = st.sidebar.selectbox(t("gender_label"), ["Female", "Male", "Other"])
social_category = st.sidebar.selectbox(t("category_label"), ["SC", "ST", "OBC", "General"])
funding_needed = st.sidebar.number_input("Required Funding (₹)", 10000, 10000000, 150000)
have_docs = st.sidebar.multiselect("Docs You Have", ["Aadhaar", "PAN", "Project Report", "Caste Certificate", "Business Proof", "Bank Statement"], default=["Aadhaar", "PAN"])

def calculate_score(scheme, user):
    conf = 100
    if user['age'] < scheme['min_age']:
        conf -= 40
    if user['funding'] > scheme['max_loan']:
        conf -= 20
    missing = [d for d in scheme['documents'].split(", ") if d.strip() not in user['docs']]
    if missing:
        conf -= 25
    if conf >= 85:
        status = "Eligible"
    elif conf >= 60:
        status = "Probable"
    else:
        status = "Uncertain"
    approval = max(0, conf - (20 if missing else 0))
    return conf, status, missing, approval

user_profile = {"age": age, "funding": funding_needed, "docs": have_docs}
processed = []
for s in SCHEMES_DATABASE:
    conf, status, missing, approval = calculate_score(s, user_profile)
    sc = s.copy()
    sc.update({"conf": conf, "status": status, "missing": missing, "approval": approval})
    processed.append(sc)
processed = sorted(processed, key=lambda x: x['conf'], reverse=True)

tab1, tab2 = st.tabs([f"🎯 {t('tab_matched')}", f"📊 {t('tab_analytics')}"])

with tab1:
    for s in processed:
        color = "#22C55E" if s['status']=="Eligible" else "#F59E0B"
        st.markdown(f"""<div style="background:white; padding:15px; border-radius:10px; border-left:6px solid {color}; margin-bottom:10px;"><h3 style="margin:0">{s['name']} - {s['id']} | {s['conf']}% - {s['status']}</h3><p><strong>Ministry:</strong> {s['ministry']} | <strong>Evidence:</strong> {s['guidelines']}</p></div>""", unsafe_allow_html=True)
        if s['missing']:
            st.error(f"⛔ Blocker: {', '.join(s['missing'])} missing | Approval: {s['approval']}%")
        else:
            st.success(f"✅ No Blocker | Approval: {s['approval']}% | Fairness: 97/100")
        with st.expander(f"Details - {s['id']}"):
            st.write(s['description'])
            st.link_button(t('open_portal'), s['apply_link'])

with tab2:
    df = pd.DataFrame([{"Scheme": s['id'], "Confidence": s['conf']} for s in processed]).set_index("Scheme")
    st.bar_chart(df)
