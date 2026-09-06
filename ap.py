import streamlit as st
import pandas as pd
import speech_recognition as sr
from fpdf import FPDF

# --- TRANSLATION DICTIONARY ---
translations = {
    "English": {
        "title": "SASVA: AI Scheme Finder",
        "subtitle": "For Marginalized Entrepreneurs",
        "profile": "Your Profile",
        "lang_label": "🌐 Language",
        "business": "Business Type",
        "state": "State",
        "income": "Monthly Income (Rs)",
        "find_btn": "Find Best Schemes - Voice Search",
        "found": "Found",
        "for_you": "best schemes for you!",
        "benefit": "Benefit",
        "eligibility": "Eligibility",
        "apply": "Apply Now",
        "download": "📄 Download My Plan as PDF",
        "voice_title": "🎤 Voice Assistant (Bangla/English)",
        "voice_label": "Bolo... যেমন: আমি কৃষক / street vendor"
    },
    "বাংলা": {
        "title": "SASVA: AI প্রকল্প সন্ধানকারী",
        "subtitle": "প্রান্তিক উদ্যোক্তাদের জন্য",
        "profile": "আপনার প্রোফাইল",
        "lang_label": "🌐 ভাষা",
        "business": "ব্যবসার ধরন",
        "state": "রাজ্য",
        "income": "মাসিক আয় (টাকা)",
        "find_btn": "সেরা প্রকল্প খুঁজুন - ভয়েস সার্চ",
        "found": "পাওয়া গেছে",
        "for_you": "টি সেরা প্রকল্প!",
        "benefit": "সুবিধা",
        "eligibility": "যোগ্যতা",
        "apply": "এখন আবেদন করুন",
        "download": "📄 আমার পরিকল্পনা PDF ডাউনলোড করুন",
        "voice_title": "🎤 ভয়েস সহকারী (বাংলা/English)",
        "voice_label": "বলুন... যেমন: আমি কৃষক / আমি দর্জি"
    },
    "हिंदी": {
        "title": "SASVA: AI योजना खोजक",
        "subtitle": "वंचित उद्यमियों के लिए",
        "profile": "आपकी प्रोफाइल",
        "lang_label": "🌐 भाषा",
        "business": "व्यवसाय प्रकार",
        "state": "राज्य",
        "income": "मासिक आय (रु)",
        "find_btn": "सर्वोत्तम योजना खोजें - वॉयस सर्च",
        "found": "मिला",
        "for_you": "सर्वोत्तम योजनाएं!",
        "benefit": "लाभ",
        "eligibility": "पात्रता",
        "apply": "अभी आवेदन करें",
        "download": "📄 मेरी योजना PDF डाउनलोड करें",
        "voice_title": "🎤 वॉयस असिस्टेंट (Bangla/English)",
        "voice_label": "बोलें... जैसे: किसान / दर्जी"
    }
}

schemes = [
    {"name": "PM SVANidhi", "benefit": "Collateral-free loan up to Rs 10,000", "eligibility": "Street vendor with vending certificate", "for": "street vendor", "score": 50},
    {"name": "Stand-Up India", "benefit": "Loan Rs 10 Lakh to 1 Crore", "eligibility": "SC/ST or Woman entrepreneur", "for": "SC/ST", "score": 50},
    {"name": "PM Kisan", "benefit": "Rs 6000 yearly support", "eligibility": "Small and marginal farmer", "for": "farmer", "score": 92},
    {"name": "Mudra Yojana", "benefit": "Loan up to Rs 10 Lakh", "eligibility": "Small business owner", "for": "small business", "score": 90},
    {"name": "Tailor Support", "benefit": "Free machine + loan", "eligibility": "Tailor with low income", "for": "tailor", "score": 88},
]
df = pd.DataFrame(schemes)

if 'voice_text' not in st.session_state:
    st.session_state.voice_text = ""

st.set_page_config(page_title="SASVA: AI Scheme Finder")

# --- LANGUAGE SELECTOR ---
lang = st.sidebar.selectbox("🌐 Language / ভাষা / भाषा", ["English", "বাংলা", "हिंदी"])
t = translations[lang]

st.title(t["title"])
st.write(t["subtitle"])
st.sidebar.title(t["profile"])
st.sidebar.write(t["voice_title"])

audio_file = st.sidebar.audio_input(t["voice_label"])

if audio_file:
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        try:
            text = r.recognize_google(audio, language='bn-IN')
        except:
            text = r.recognize_google(audio, language='en-IN')
        
