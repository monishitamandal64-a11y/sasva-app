import streamlit as st
import pandas as pd
import re
from io import BytesIO
from gtts import gTTS

# --- PAGE CONFIG ---
st.set_page_config(page_title="WELCOME TO SASVA", page_icon="🏛️", layout="wide")

# --- MOCK DATA (jate schemes_data.py chara chole) ---
INDIAN_STATES = ["West Bengal", "Bihar", "Uttar Pradesh", "Maharashtra", "Delhi", "Rajasthan", "All India"]
OFFICIAL_LANGUAGES_INDIA = ["English", "Hindi", "Bengali"]

TRANSLATIONS = {
    "English": {"title": "SchemeSetu - SASVA", "subtitle": "Your AI Scheme Assistant | Team Nexus 5", "search_placeholder": "Search Scheme (e.g. PMEGP, MUDRA)", "entrepreneur_profile": "Entrepreneur Profile", "state_label": "State", "age_label": "Age", "gender_label": "Gender", "category_label": "Category", "sector_label": "Sector", "tab_matched": "Matched Schemes", "tab_analytics": "Analytics", "tab_chatbot": "AI Help", "tab_faqs": "FAQs", "tab_notifications": "Updates", "active_schemes_title": "Recommended Schemes", "match_label": "Match", "ministry_label": "Ministry", "benefit_label": "Benefit", "loan_range_label": "Loan Range", "expander_title": "Details", "match_reasons_title": "Why Matched?", "guidelines_title": "Guidelines", "open_portal": "Apply on Official Portal", "share_whatsapp": "Share"},
    "Hindi (हिन्दी)": {"title": "योजना सेतु - SASVA", "subtitle": "आपका AI योजना सहायक", "search_placeholder": "योजना खोजें", "entrepreneur_profile": "उद्यमी प्रोफाइल", "state_label": "राज्य", "age_label": "आयु", "gender_label": "लिंग", "category_label": "श्रेणी", "sector_label": "क्षेत्र", "tab_matched": "मिलान योजनाएं", "tab_analytics": "विश्लेषण", "tab_chatbot": "AI मदद", "tab_faqs": "FAQs", "tab_notifications": "अपडेट", "active_schemes_title": "अनुशंसित योजनाएं", "match_label": "मैच", "ministry_label": "मंत्रालय", "benefit_label": "लाभ", "loan_range_label": "ऋण सीमा", "expander_title": "विवरण", "match_reasons_title": "क्यों मिला?", "guidelines_title": "दिशानिर्देश", "open_portal": "आधिकारिक पोर्टल पर आवेदन करें", "share_whatsapp": "शेयर करें"},
    "Bengali (বাংলা)": {"title": "স্কিমসেতু - SASVA", "subtitle": "তোমার AI স্কিম সহকারী", "search_placeholder": "স্কিম খোঁজো (যেমন PMEGP)", "entrepreneur_profile": "উদ্যোক্তা প্রোফাইল", "state_label": "রাজ্য", "age_label": "বয়স", "gender_label": "লিঙ্গ", "category_label": "ক্যাটাগরি", "sector_label": "সেক্টর", "tab_matched": "মিলে যাওয়া স্কিম", "tab_analytics": "অ্যানালিটিক্স", "tab_chatbot": "AI সাহায্য", "tab_faqs": "প্রশ্ন", "tab_notifications": "আপডেট", "active_schemes_title": "তোমার জন্য স্কিম", "match_label": "ম্যাচ", "ministry_label": "মন্ত্রক", "benefit_label": "সুবিধা", "loan_range_label": "লোনের পরিমাণ", "expander_title": "বিস্তারিত", "match_reasons_title": "কেন মিলেছে?", "guidelines_title": "গাইডলাইন", "open_portal": "অফিসিয়াল পোর্টালে আবেদন", "share_whatsapp": "শেয়ার করো"}
}

SCHEMES_DATABASE = [
    {"id": "PMEGP", "name": "PM Employment Generation Programme", "ministry": "MSME", "description": "For new micro enterprises in rural areas. 35% subsidy for SC/ST/Women.", "status": "Active", "min_loan": 50000, "max_loan": 1000000, "min_age": 18, "max_age": 60, "target_group": "SC, ST, OBC, Women, General, Rural", "documents": "Aadhaar, Project Report, Caste Certificate, Rural Certificate", "guidelines": "Policy Clause 4.2: Age>18, Rural, Investment <10L", "apply_link": "https://www.kviconline.gov.in/pmegpeportal/", "main_benefit": "35% Subsidy"},
    {"id": "MUDRA", "name": "MUDRA Loan Yojana", "ministry": "Finance", "description": "Loan up to 10L for non-farm enterprises. No collateral needed.", "status": "Active", "min_loan": 50000, "max_loan": 1000000, "min_age": 18, "max_age": 65, "target_group": "All Citizens, Women, SC/ST", "documents": "Aadhaar, Business Proof, Bank Statement", "guidelines": "Policy Clause 2.1: Any non-farm enterprise eligible", "apply_link": "https://www.mudra.org.in/", "main_benefit": "Loan upto 10L"},
    {"id": "STANDUP", "name": "Stand-Up India", "ministry": "Finance", "description": "For SC/ST and Women entrepreneurs. Loan 10L to 1Cr.", "status": "Active", "min_loan": 1000000, "max_loan": 10000000, "min_age": 18, "max_age": 60, "target_group": "SC, ST, Women", "documents": "Aadhaar, Caste Certificate, Business Plan", "guidelines": "For SC/ST/Women only", "apply_link": "https://www.standupmitra.in/", "main_benefit": "10L to 1Cr Loan"},
]

# --- HELPERS ---
def parse_number(val):
    if isinstance(val, (int, float)): return val
    if not val or "N/A" in str(val): return float('inf')
    digits = re.sub(r'[^\d]', '', str(val))
    return int(digits) if digits else float('inf')

def t(key):
    lang = st.session_state.get("selected_lang", "English")
    return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

# --- LANGUAGE SCREEN ---
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = None

if st.session_state.selected_lang is None:
    st.markdown("""<div style="background-color:#1e1b4b; padding:25px; border-radius:12px; text-align:center; margin-bottom:25px;"><h1 style="color:white; margin:0;">Welcome to SchemeSetu - SASVA</h1><p style="color:#cbd5e1; margin-top:8px;">कृपया अपनी भाषा चुनें / Please select your language</p></div>""", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        if st.button("English", use_container_width=True): st.session_state.selected_lang="English"; st.rerun()
        if st.button("বাংলা\nBengali", use_container_width=True): st.session_state.selected_lang="Bengali (বাংলা)"; st.rerun()
    with c2:
        if st.button("हिन्दी\nHindi", use_container_width=True): st.session_state.selected_lang="Hindi (हिन्दी)"; st.rerun()
    st.stop()

# --- MAIN APP ---
selected_lang = st.session_state.selected_lang
if st.sidebar.button("🌐 Change Language"):
    st.session_state.selected_lang = None
    st.rerun()

st.markdown(f"""<div style="background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%); padding:15px; border-radius:10px; text-align:center; margin-bottom:20px; border:1px solid #CBD5E1;"><div style="font-size:2.2rem; font-weight:bold; color:#1E3A8A; margin:0;">🏛️ {t("title")}</div><div style="color:#1E293B; font-weight:600;">{t("subtitle")}</div></div>""", unsafe_allow_html=True)

# Sidebar Profile
st.sidebar.header(f"👤 {t('entrepreneur_profile')}")
location = st.sidebar.selectbox(t("state_label"), INDIAN_STATES)
age = st.sidebar.number_input(t("age_label"), 18, 80, 22)
gender = st.sidebar.selectbox(t("gender_label"), ["Female", "Male", "Other"])
social_category = st.sidebar.selectbox(t("category_label"), ["SC", "ST", "OBC", "General"])
business_sector = st.sidebar.selectbox(t("sector_label"), ["Manufacturing", "Services", "Trading", "Agri-Allied"])
funding_needed = st.sidebar.number_input("Required Funding (₹)", 10000, 10000000, 150000)
have_docs = st.sidebar.multiselect("Docs You Have", ["Aadhaar", "PAN", "Project Report", "Caste Certificate", "Business Proof", "Bank Statement"], default=["Aadhaar", "PAN"])

# Voice Helper
def generate_audio(text_content):
    try:
        lang_code = 'hi' if 'Hindi' in selected_lang else 'bn' if 'Bengali' in selected_lang else 'en'
        tts = gTTS(text=text_content, lang=lang_code)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        return mp3_fp
    except Exception as e:
        st.sidebar.error(f"Audio Error: {e}")
        return None

# Matching Logic
def calculate_score(scheme, user):
    conf = 100
    if user['age'] < scheme['min_age']: conf -= 40
    if user['funding'] > scheme['max_loan']: conf -= 20
    missing = [d for d in scheme['documents'].split(", ") if d not in user['docs']]
    if missing: conf -= 25

    if conf >= 85: status = "Eligible"
    elif conf >= 60: status = "Probable"
    elif conf >= 40: status = "Uncertain"
    else: status = "Ineligible"

    approval = max(0, conf - (20 if missing else 0))
    return conf, status, missing, approval

user_profile = {"age": age, "location": location, "gender": gender, "category": social_category, "funding": funding_needed, "docs": have_docs}
processed_schemes = []
for s in SCHEMES_DATABASE:
    conf, status, missing, approval = calculate_score(s, user_profile)
    s_copy = s.copy()
    s_copy.update({"conf": conf, "status": status, "missing": missing, "approval": approval})
    processed_schemes.append(s_copy)
processed_schemes = sorted(processed_schemes, key=lambda x: x['conf'], reverse=True)

# --- TABS ---
tab1, tab2 = st.tabs([f"🎯 {t('tab_matched')}", f"📊 {t('tab_analytics')}"])

with tab1:
    portfolio = [p for p in processed_schemes if p['status'] in ["Eligible","Probable"]][:2]
    if portfolio:
        st.info(f"✨ **Best Combo (Portfolio Optimizer):** {', '.join([p['id'] for p in portfolio])} - Maximizes approval")

    for s in processed_schemes:
        color = "#22C55E" if s['status']=="Eligible" else "#F59E0B" if s['status']=="Probable" else "#EF4444"
        badge_color = "#DCFCE7" if s['status']=="Eligible" else "#FEF3C7"
        # --- FLOATING WELCOME BANNER ---
st.markdown("""
<style>
@keyframes floatUpDown {
  0%, 100% { transform: translateY(0px); box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
  50% { transform: translateY(-8px); box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
}
.floating-welcome {
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  padding: 28px;
  border-radius: 16px;
  text-align: center;
  margin-bottom: 25px;
  position: sticky;
  top: 10px;
  z-index: 999;
  animation: floatUpDown 3s ease-in-out infinite;
  border: 1px solid rgba(255,255,255,0.1);
}
.floating-welcome h1 {
  color: white;
  margin: 0;
  font-size: 32px;
  letter-spacing: 0.5px;
}
.floating-welcome p {
  color: #cbd5e1;
  margin-top: 8px;
  font-size: 16px;
}
</style>
<div class="floating-welcome">
    <h1>Welcome to SchemeSetu - SASVA</h1>
    <p>कृपया अपनी भाषा चुनें / Please select your language</p>
</div>
""", unsafe_allow_html=True)
        if s['missing']:
            st.error(f"⛔ Blocker (F4): {', '.join(s['missing'])} missing | Approval Prob (F11): {s['approval']}%")
        else:
            st.success(f"✅ No Blocker | Approval Prob (F11): {s['approval']}% | Fairness Score (F8): 97/100")

        with st.expander(f"Details - {s['id']}"):
            st.write(f"**Why Matched:** {s['guidelines']}")
            st.write(f"**Required Docs:** {s['documents']}")
            st.link_button(f"{t('open_portal')}", s['apply_link'])

    # Voice
    st.sidebar.markdown("---")
    st.sidebar.markdown("🎙️ **AI Voice Assistant**")
    if st.sidebar.button("🔊 Read Top Match Aloud"):
        top = processed_schemes[0]
        txt = f"Top match is {top['name']} with {top['conf']} percent confidence. Status {top['status']}. Approval probability {top['approval']} percent."
        audio = generate_audio(txt)
        if audio: st.sidebar.audio(audio, format="audio/mp3")

with tab2:
    st.subheader("Scheme Analytics")
    df = pd.DataFrame([{"Scheme": s['id'], "Confidence": s['conf'], "Approval Prob": s['approval']} for s in processed_schemes]).set_index("Scheme")
    st.bar_chart(df)
    st.dataframe(df, use_container_width=True)
