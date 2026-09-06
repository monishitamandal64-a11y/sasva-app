import streamlit as st
import pandas as pd
import speech_recognition as sr
from fpdf import FPDF

translations = {
    "English": {"title": "Welcome to SASVA", "subtitle": "AI Scheme Finder for Marginalized Entrepreneurs", "profile": "Your Profile", "business": "Business Type", "state": "State", "income": "Monthly Income (Rs)", "find_btn": "Find Best Schemes", "found": "Found", "for_you": "best schemes!", "benefit": "Benefit", "eligibility": "Eligibility", "apply": "Apply Now", "download": "Download My Plan as PDF", "voice_title": "Voice Assistant", "voice_label": "Click mic & say farmer"},
    "বাংলা": {"title": "SASVA-তে স্বাগতম", "subtitle": "প্রান্তিক উদ্যোক্তাদের জন্য", "profile": "আপনার প্রোফাইল", "business": "ব্যবসার ধরন", "state": "রাজ্য", "income": "মাসিক আয়", "find_btn": "প্রকল্প খুঁজুন", "found": "পাওয়া গেছে", "for_you": "টি প্রকল্প!", "benefit": "সুবিধা", "eligibility": "যোগ্যতা", "apply": "আবেদন করুন", "download": "PDF ডাউনলোড", "voice_title": "ভয়েস সহকারী", "voice_label": "বলুন... কৃষক"},
    "हिंदी": {"title": "SASVA में आपका स्वागत है", "subtitle": "वंचित उद्यमियों के लिए", "profile": "प्रोफाइल", "business": "व्यवसाय", "state": "राज्य", "income": "मासिक आय", "find_btn": "योजना खोजें", "found": "मिला", "for_you": "योजनाएं!", "benefit": "लाभ", "eligibility": "पात्रता", "apply": "आवेदन करें", "download": "PDF डाउनलोड", "voice_title": "वॉयस असिस्टेंट", "voice_label": "बोलें... किसान"}
}

schemes = [
    {"name": "PM SVANidhi", "benefit": "Loan up to Rs 10,000", "eligibility": "Street vendor", "for": "street vendor", "score": 50},
    {"name": "PM Kisan", "benefit": "Rs 6000 yearly", "eligibility": "Small farmer", "for": "farmer", "score": 92},
    {"name": "Mudra Yojana", "benefit": "Loan up to Rs 10 Lakh", "eligibility": "Small business", "for": "small business", "score": 90},
]
df = pd.DataFrame(schemes)

if 'voice_text' not in st.session_state:
    st.session_state.voice_text = ""
if 'business_index' not in st.session_state:
    st.session_state.business_index = 0

st.set_page_config(page_title="SASVA")
lang = st.sidebar.selectbox("Language", ["English", "বাংলা", "हिंदी"])
t = translations[lang]

# --- EKHANEI MOVING WELCOME ---
st.markdown("""
<style>
.marquee { width: 100%; overflow: hidden; white-space: nowrap; }
.marquee span { display: inline-block; padding-left: 100%; animation: marquee 7s linear infinite; font-size: 42px; font-weight: bold; color: #2E86AB; }
@keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
</style>
""", unsafe_allow_html=True)
st.markdown(f'<div class="marquee"><span>✨ {t["title"]} ✨ {t["title"]} ✨ {t["title"]} ✨</span></div>', unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: center; color: grey;'>{t['subtitle']}</h4>", unsafe_allow_html=True)
st.write("---")

st.sidebar.title(t["profile"])
audio_file = st.sidebar.audio_input(t["voice_label"])
if audio_file:
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    recog = 'bn-IN' if lang=="বাংলা" else 'hi-IN' if lang=="हिंदी" else 'en-IN'
    try:
        text = r.recognize_google(audio, language=recog)
        st.session_state.voice_text = text
        st.sidebar.success(f"You said: {text}")
    except:
        st.sidebar.error("Abar bolo")

voice_lower = st.session_state.voice_text.lower()
options = ["SC/ST", "street vendor", "small business", "farmer", "tailor"]
idx = st.session_state.business_index
if any(x in voice_lower for x in ["street", "vendor", "হকার"]): idx=1
elif any(x in voice_lower for x in ["small", "business", "ব্যবসা"]): idx=2
elif any(x in voice_lower for x in ["farm", "kisan", "কৃষক", "ফার্মার"]): idx=3
elif any(x in voice_lower for x in ["tail", "দর্জি"]): idx=4
if st.session_state.voice_text!="": st.session_state.business_index=idx

business = st.sidebar.selectbox(t["business"], options, index=st.session_state.business_index)
state = st.sidebar.selectbox(t["state"], ["West Bengal", "All", "Bihar", "UP"])
income = st.sidebar.number_input(t["income"], value=1000)

if st.button(t["find_btn"]):
    filtered = df[df["for"].str.contains(business, case=False)]
    if filtered.empty: filtered=df
    st.success(f"{t['found']} {len(filtered)} {t['for_you']}")
    for _, row in filtered.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['name']} - {row['score']}/100")
            st.write(f"**{t['benefit']}:** {row['benefit']}")
            st.button(t["apply"], key=row['name'])
