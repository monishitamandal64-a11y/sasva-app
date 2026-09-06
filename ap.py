import streamlit as st
import pandas as pd
import speech_recognition as sr
from fpdf import FPDF

# --- TRANSLATION ---
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
        "for_you": "best schemes for you!",
        "benefit": "Benefit",
        "eligibility": "Eligibility",
        "apply": "Apply Now",
        "download": "Download My Plan as PDF",
        "voice_title": "Voice Assistant (Bangla/English)",
        "voice_label": "say... farmer / street vendor"
    },
    "বাংলা": {
        "title": "SASVA: AI প্রকল্প সন্ধানকারী",
        "subtitle": "প্রান্তিক উদ্যোক্তাদের জন্য",
        "profile": "আপনার প্রোফাইল",
        "business": "ব্যবসার ধরন",
        "state": "রাজ্য",
        "income": "মাসিক আয় (টাকা)",
        "find_btn": "সেরা প্রকল্প খুঁজুন",
        "found": "পাওয়া গেছে",
        "for_you": "টি সেরা প্রকল্প!",
        "benefit": "সুবিধা",
        "eligibility": "যোগ্যতা",
        "apply": "আবেদন করুন",
        "download": "PDF ডাউনলোড করুন",
        "voice_title": "ভয়েস সহকারী",
        "voice_label": "বলুন..."
    },
    "हिंदी": {
        "title": "SASVA: AI योजना खोजक",
        "subtitle": "वंचित उद्यमियों के लिए",
        "profile": "आपकी प्रोफाइल",
        "business": "व्यवसाय प्रकार",
        "state": "राज्य",
        "income": "मासिक आय (रु)",
        "find_btn": "सर्वोत्तम योजना खोजें",
        "found": "मिला",
        "for_you": "सर्वोत्तम योजनाएं!",
        "benefit": "लाभ",
        "eligibility": "पात्रता",
        "apply": "आवेदन करें",
        "download": "PDF डाउनलोड करें",
        "voice_title": "वॉयस असिस्टेंट",
        "voice_label": "बोलें... किसान"
    }
}

schemes = [
    {"name": "PM SVANidhi", "benefit": "Loan up to Rs 10,000", "eligibility": "Street vendor certificate", "for": "street vendor", "score": 50},
    {"name": "Stand-Up India", "benefit": "Loan Rs 10 Lakh to 1 Crore", "eligibility": "SC/ST or Woman", "for": "SC/ST", "score": 50},
    {"name": "PM Kisan", "benefit": "Rs 6000 yearly support", "eligibility": "Small farmer", "for": "farmer", "score": 92},
    {"name": "Mudra Yojana", "benefit": "Loan up to Rs 10 Lakh", "eligibility": "Small business", "for": "small business", "score": 90},
    {"name": "Tailor Support", "benefit": "Free machine + loan", "eligibility": "Tailor low income", "for": "tailor", "score": 88},
]
df = pd.DataFrame(schemes)

if 'voice_text' not in st.session_state:
    st.session_state.voice_text = ""

st.set_page_config(page_title="SASVA")

lang = st.sidebar.selectbox("Language / ভাষা / भाषा", ["English", "বাংলা", "हिंदी"])
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
        text = r.recognize_google(audio, language='bn-IN')
        st.session_state.voice_text = text
        st.sidebar.success(f"You said: {text}")
    except:
        try:
            text2 = r.recognize_google(audio, language='en-IN')
            st.session_state.voice_text = text2
            st.sidebar.success(f"You said: {text2}")
        except:
            st.sidebar.error("Bujhte parini, abar bolo")

voice_lower = st.session_state.voice_text.lower()
options = ["SC/ST", "street vendor", "small business", "farmer", "tailor"]
index = 0

if "street" in voice_lower or "vendor" in voice_lower or "হকার" in voice_lower:
    index = 1
elif "small" in voice_lower or "business" in voice_lower or "ব্যবসা" in voice_lower:
    index = 2
elif "farm" in voice_lower or "kisan" in voice_lower or "কৃষক" in voice_lower or "চাষ" in voice_lower:
    index = 3
elif "tail" in voice_lower or "দর্জি" in voice_lower:
    index = 4

business = st.sidebar.selectbox(t["business"], options, index=index)
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
    st.download_button(
        label=t["download"],
        data=pdf_bytes,
        file_name="SASVA_Schemes.pdf",
        mime="application/pdf"
    )
