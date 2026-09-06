import streamlit as st
import pandas as pd
import speech_recognition as sr
from fpdf import FPDF

translations = {
    "English": {
        "title": "SASVA: AI Scheme Finder",
        "subtitle": "For Marginalized Entrepreneurs",
        "profile": "Your Profile",
        "business": "Business Type",
        "state": "State",
        "income": "Monthly Income (Rs)",
        "find_btn": "Find Best Schemes - Voice Search",
        "found": "Found",
        "for_you": "best schemes!",
        "benefit": "Benefit",
        "eligibility": "Eligibility",
        "apply": "Apply Now",
        "download": "Download My Plan as PDF",
        "voice_title": "Voice Assistant",
        "voice_label": "say... farmer / street vendor"
    },
    "বাংলা": {
        "title": "SASVA: AI প্রকল্প সন্ধানকারী",
        "subtitle": "প্রান্তিক উদ্যোক্তাদের জন্য",
        "profile": "আপনার প্রোফাইল",
        "business": "ব্যবসার ধরন",
        "state": "রাজ্য",
        "income": "মাসিক আয়",
        "find_btn": "সেরা প্রকল্প খুঁজুন",
        "found": "পাওয়া গেছে",
        "for_you": "টি সেরা প্রকল্প!",
        "benefit": "সুবিধা",
        "eligibility": "যোগ্যতা",
        "apply": "আবেদন করুন",
        "download": "PDF ডাউনলোড করুন",
        "voice_title": "ভয়েস সহকারী",
        "voice_label": "বলুন... আমি কৃষক"
    },
    "हिंदी": {
        "title": "SASVA: योजना खोजक",
        "subtitle": "वंचित उद्यमियों के लिए",
        "profile": "आपकी प्रोफाइल",
        "business": "व्यवसाय",
        "state": "राज्य",
        "income": "मासिक आय",
        "find_btn": "योजना खोजें",
        "found": "मिला",
        "for_you": "योजनाएं!",
        "benefit": "लाभ",
        "eligibility": "पात्रता",
        "apply": "आवेदन करें",
        "download": "PDF डाउनलोड करें",
        "voice_title": "वॉयस असिस्टेंट",
        "voice_label": "बोलें... किसान"
    }
}

schemes = [
    {"name": "PM SVANidhi", "benefit": "Loan up to Rs 10,000", "eligibility": "Street vendor", "for": "street vendor", "score": 50},
    {"name": "Stand-Up India", "benefit": "Loan Rs 10 Lakh to 1 Crore", "eligibility": "SC/ST or Woman", "for": "SC/ST", "score": 50},
    {"name": "PM Kisan", "benefit": "Rs 6000 yearly", "eligibility": "Small farmer", "for": "farmer", "score": 92},
    {"name": "Mudra Yojana", "benefit": "Loan up to Rs 10 Lakh", "eligibility": "Small business", "for": "small business", "score": 90},
    {"name": "Tailor Support", "benefit": "Free machine + loan", "eligibility": "Tailor", "for": "tailor", "score": 88},
]
df = pd.DataFrame(schemes)

if 'voice_text' not in st.session_state:
    st.session_state.voice_text = ""
if 'business_index' not in st.session_state:
    st.session_state.business_index = 0

st.set_page_config(page_title="SASVA")
lang = st.sidebar.selectbox("Language / ভাষা", ["English", "বাংলা", "हिंदी"])
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
    if lang == "বাংলা":
        recog_lang = 'bn-IN'
    elif lang == "हिंदी":
        recog_lang = 'hi-IN'
    else:
        recog_lang = 'en-IN'
    try:
        text = r.recognize_google(audio, language=recog_lang)
        st.session_state.voice_text = text
        st.sidebar.success(f"You said: {text}")
    except:
        st.sidebar.error("repeat/abar bolun/phirse boliyen")

voice_lower = st.session_state.voice_text.lower()
options = ["SC/ST", "street vendor", "small business", "farmer", "tailor"]
idx = st.session_state.business_index

if any(x in voice_lower for x in ["street", "vendor", "হকার", "ভেন্ডর"]):
    idx = 1
elif any(x in voice_lower for x in ["small", "business", "ব্যবসা"]):
    idx = 2
elif any(x in voice_lower for x in ["farm", "kisan", "কৃষক", "চাষ", "ফার্মার", "ফার্ম"]):
    idx = 3
elif any(x in voice_lower for x in ["tail", "দর্জি", "টেইলার", "সেলাই"]):
    idx = 4

if st.session_state.voice_text!= "":
    st.session_state.business_index = idx

business = st.sidebar.selectbox(t["business"], options, index=st.session_state.business_index)
state = st.sidebar.selectbox(t["state"], ["West Bengal", "All", "Bihar", "UP"])
income = st.sidebar.number_input(t["income"], value=1000)

def create_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="SASVA - Your Best Schemes", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for _, row in dataframe.iterrows():
        pdf.cell(200, 10, txt=f"{row['name']} - Score {row['score']}/100", ln=True)
        pdf.multi_cell(0, 8, txt=f"Benefit: {row['benefit']} \nEligibility: {row['eligibility']} \n")
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

if st.button(t["find_btn"]):
    filtered = df[df["for"].str.contains(business, case=False)]
    if filtered.empty:
        filtered = df
    st.session_state.filtered_df = filtered
    st.success(f"{t['found']} {len(filtered)} {t['for_you']}")
    for _, row in filtered.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['name']} - Score: {row['score']}/100")
            st.write(f"**{t['benefit']}:** {row['benefit']}")
            st.write(f"**{t['eligibility']}:** {row['eligibility']}")
            st.button(t["apply"], key=row['name'])

if 'filtered_df' in st.session_state:
    pdf_bytes = create_pdf(st.session_state.filtered_df)
    st.download_button(label=t["download"], data=pdf_bytes, file_name="SASVA_Schemes.pdf", mime="application/pdf")
