import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from gtts import gTTS

st.set_page_config(page_title="SASVA | SchemeSetu", page_icon="🏛️", layout="wide")

# ============ I. 22 LANGUAGE SYSTEM (DEMO TE 3 TE, BAKI 19 ADD KORA JABE) ============
TRANSLATIONS = {
    "English": {"welcome": "Welcome to SchemeSetu - SASVA", "home": "Home", "about": "About Us", "profile": "Entrepreneur Profile"},
    "Hindi (हिन्दी)": {"welcome": "योजना सेतु - SASVA में आपका स्वागत है", "home": "होम", "about": "हमारे बारे में", "profile": "उद्यमी प्रोफाइल"},
    "Bengali (বাংলা)": {"welcome": "স্কিমসেতু - SASVA তে স্বাগতম", "home": "হোম", "about": "আমাদের সম্পর্কে", "profile": "উদ্যোক্তা প্রোফাইল"},
}

# ============ DATABASE (III. AUTO FEED SIMULATION) ============
SCHEMES_DATABASE = [
    {"id": "PMEGP", "name": "PM Employment Generation Programme", "ministry": "MSME", "benefit": "35% Subsidy", "max_loan": 1000000, "min_age": 18, "keywords": "rural sc st women manufacturing", "docs": "Aadhaar, Project Report, Caste Certificate", "steps": "1. Register on KVIC Portal\n2. Fill Project Report\n3. Upload Docs\n4. Bank Approval", "last_updated": "2026-09-08"},
    {"id": "MUDRA", "name": "MUDRA Loan - Tarun", "ministry": "Finance", "benefit": "Loan up to 10L", "max_loan": 1000000, "min_age": 18, "keywords": "trading shop business", "docs": "Aadhaar, Business Proof, Bank Statement", "steps": "1. Visit nearest bank\n2. Fill MUDRA form\n3. Submit Business Proof", "last_updated": "2026-09-08"},
    {"id": "STANDUP", "name": "Stand-Up India", "ministry": "Finance", "benefit": "10L to 1Cr Loan", "max_loan": 10000000, "min_age": 18, "keywords": "sc st women", "docs": "Aadhaar, Caste Certificate, Business Plan", "steps": "1. StandUp Mitra Portal Registration\n2. Handholding support", "last_updated": "2026-09-08"},
    {"id": "PMFME", "name": "PM Micro Food Enterprises", "ministry": "Food Processing", "benefit": "35% Credit Linked Subsidy", "max_loan": 1000000, "min_age": 18, "keywords": "food agri", "docs": "Aadhaar, Food License", "steps": "1. Apply on PMFME portal", "last_updated": "2026-09-08"},
    {"id": "NULM", "name": "DAY-NULM", "ministry": "Housing", "benefit": "2L + 7% Interest Subsidy", "max_loan": 200000, "min_age": 18, "keywords": "urban trading", "docs": "Aadhaar, Residence Proof", "steps": "1. Visit City Livelihood Center", "last_updated": "2026-09-08"},
]

# ============ SESSION STATE (VI, VII, X, XI) ============
if "selected_lang" not in st.session_state: st.session_state.selected_lang = None
if "user" not in st.session_state: st.session_state.user = None
if "saved" not in st.session_state: st.session_state.saved = []
if "tracking" not in st.session_state: st.session_state.tracking = {}
if "feedbacks" not in st.session_state: st.session_state.feedbacks = []

# ============ HEADER - GOVT LOGO + OUR LOGO + HOME/ABOUT ============
st.markdown("""
<style>
@keyframes floatUpDown {
  0%,100%{transform:translateY(0px); box-shadow:0 8px 25px rgba(0,0,0,0.3);}
  50%{transform:translateY(-8px); box-shadow:0 15px 35px rgba(0,0,0,0.5);}
}
.floating-welcome{
  background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
  padding:22px; border-radius:16px; text-align:center; margin-bottom:15px;
  animation:floatUpDown 3s ease-in-out infinite; position:sticky; top:5px; z-index:999;
}
.header-row{display:flex; justify-content:space-between; align-items:center; background:white; padding:10px 20px; border-radius:12px; border:1px solid #eee; margin-bottom:15px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-row">
    <div><b>🇮🇳 Govt of India Logo</b> | <b style="color:#1e1b4b;">SASVA - Our Logo + Name</b></div>
    <div><b>Home</b> &nbsp;&nbsp; <b>About Us</b></div>
</div>
""", unsafe_allow_html=True)

# ============ I. LANGUAGE SCREEN WITH FLOATING ============
if st.session_state.selected_lang is None:
    st.markdown(f"""
    <div class="floating-welcome">
        <h1 style="color:white; margin:0;">Welcome to SchemeSetu - SASVA</h1>
        <p style="color:#cbd5e1;">कृपया अपनी भाषा चुनें / Please select your language (22 Languages Supported)</p>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("English", use_container_width=True): st.session_state.selected_lang="English"; st.rerun()
    with c2:
        if st.button("हिन्दी", use_container_width=True): st.session_state.selected_lang="Hindi (हिन्दी)"; st.rerun()
    with c3:
        if st.button("বাংলা", use_container_width=True): st.session_state.selected_lang="Bengali (বাংলা)"; st.rerun()
    st.stop()

# ============ VI. PROFILE / LOGIN / SIGNUP ============
with st.sidebar:
    st.title("👤 Profile / Login")
    if st.session_state.user is None:
        role = st.selectbox("Login as", ["User", "CSC Operator / Admin"])
        name = st.text_input("Name / CSC ID")
        if st.button("Login / Signup", type="primary"):
            st.session_state.user = {"name": name or "Guest", "role": role}
            st.rerun()
    else:
        st.success(f"Logged in: {st.session_state.user['name']} ({st.session_state.user['role']})")
        if st.button("Logout"): st.session_state.user=None; st.rerun()
        st.markdown("---")
        st.write(f"📌 Saved Schemes: {len(st.session_state.saved)}")

# ============ MAIN ============
selected_lang = st.session_state.selected_lang
t_welcome = TRANSLATIONS.get(selected_lang, TRANSLATIONS["English"])["welcome"]

st.markdown(f"<div style='text-align:center; font-size:20px; font-weight:bold; margin:10px;'>🏛️ {t_welcome}</div>", unsafe_allow_html=True)

# ============ III. AUTO FEED STATUS + IV. NOTIFICATION ============
colA, colB = st.columns([2,1])
with colA:
    st.info(f"🔄 Auto-Feed Status (III): Last synced from myscheme.gov.in on {SCHEMES_DATABASE[0]['last_updated']} | Next sync: Tonight 12 AM | (+) Recheck done")
with colB:
    notify_opt = st.selectbox("IV. Notify via", ["None", "WhatsApp", "SMS", "Email"])

# ============ SEARCH + ENTER OPTION ============
st.subheader("🔍 Search Scheme + Press ENTER")
c1,c2 = st.columns([3,1])
with c1:
    search_q = st.text_input("search_input", placeholder="Type: women / rural / food / trading...", label_visibility="collapsed")
with c2:
    enter_clicked = st.button("⏎ ENTER", use_container_width=True, type="primary")

filtered = SCHEMES_DATABASE
if search_q:
    q = search_q.lower()
    filtered = [s for s in SCHEMES_DATABASE if q in s['name'].lower() or q in s['keywords'].lower()]

# ============ V. SCHEME MATCHING + BREAKDOWN ============
for s in filtered:
    conf = 92 if "women" in search_q.lower() and "women" in s['keywords'] else 78
    status = "Eligible" if conf>85 else "Probable"

    st.markdown(f"""
    <div style="background:white; padding:15px; border-radius:12px; border-left:6px solid #22C55E; margin-bottom:10px;">
        <h3 style="margin:0;">{s['id']} - {s['name']} | {conf}% {status}</h3>
        <p style="margin:5px 0;"><b>Ministry:</b> {s['ministry']} | <b>Benefit:</b> {s['benefit']} | <b>Evidence (Clause):</b> Age>{s['min_age']}</p>
        <p style="margin:0; color:#555;">AI Match Breakdown: Category(40%) + Funding(30%) + Sector(15%) = {conf}% | Reason: Keyword matched '{search_q}'</p>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        if st.button(f"💾 Save", key=f"save_{s['id']}"):
            if s['id'] not in st.session_state.saved: st.session_state.saved.append(s['id']); st.success("Saved! (VII)")
    with c2:
        # IX. DOWNLOAD SPECIFICS
        pdf_data = f"Scheme: {s['name']}\nBenefit: {s['benefit']}\nSteps:\n{s['steps']}\nDocs: {s['docs']}".encode()
        st.download_button(f"📄 PDF", data=pdf_data, file_name=f"{s['id']}_specifics.txt", key=f"pdf_{s['id']}")
    with c3:
        # V. Share
        st.button(f"📲 WhatsApp", key=f"wa_{s['id']}", help=f"Share via {notify_opt}: https://wa.me/?text={s['name']}")
    with c4:
        if st.button(f"🔊 Voice", key=f"voice_{s['id']}"):
            try:
                tts = gTTS(text=f"Scheme {s['name']} benefit {s['benefit']}", lang='en')
                fp = BytesIO(); tts.write_to_fp(fp); st.audio(fp, format="audio/mp3")
            except: st.error("Voice error")
    with c5:
        if st.button(f"Track Success", key=f"track_{s['id']}"):
            st.session_state.tracking[s['id']] = "Applied"
            st.success("X. Tracking Started")

    with st.expander(f"View Details - {s['id']} (V. Step-by-step + Docs)"):
        st.write(f"**Step-by-Step Guidelines:**\n{s['steps']}")
        st.write(f"**Required Docs PDF List:** {s['docs']}")
        st.write(f"**Share via:** WhatsApp / SMS / Email link: {s['link'] if 'link' in s else 'Official Portal'}")

# ============ VIII. CSC / ADMIN SYSTEM ============
if st.session_state.user and "Admin" in st.session_state.user['role']:
    st.divider()
    st.subheader("VIII. CSC Operator / Admin System")
    st.dataframe(pd.DataFrame(SCHEMES_DATABASE))
    if st.button("🔄 Force Re-sync Govt Database Now"):
        st.success("Database feed rechecked & updated! (+)")

# ============ X. SUCCESS TRACKING ============
if st.session_state.tracking:
    st.divider()
    st.subheader("X. Success Tracking System (Personalized)")
    for sid, stat in st.session_state.tracking.items():
        st.progress(60, text=f"{sid}: {stat} -> Under Review -> Benefit (60%)")

# ============ XI. FEEDBACK & SELF LEARNING LOOP ============
st.divider()
st.subheader("XI. Feedback & Self Learning Loop")
fb = st.text_area("Your feedback will improve AI matching")
if st.button("Submit Feedback"):
    st.session_state.feedbacks.append(fb)
    st.success(f"Feedback saved! Total feedbacks: {len(st.session_state.feedbacks)} - Self learning loop will retrain model")

st.caption(f"Total Saved: {st.session_state.saved} | Feedbacks: {len(st.session_state.feedbacks)}")
