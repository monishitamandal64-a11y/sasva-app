import streamlit as st
import pandas as pd
import speech_recognition as sr
from fpdf import FPDF

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
st.title("SASVA: AI Scheme Finder")
st.write("For Marginalized Entrepreneurs")
st.sidebar.title("Your Profile")

# --- 1. BANGLA + ENGLISH VOICE ---
st.sidebar.write("🎤 Voice Assistant (Bangla/English)")
audio_file = st.sidebar.audio_input("Bolo... যেমন: আমি কৃষক / street vendor")

if audio_file:
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        # Prothome Bangla try korbe, na parle English
        try:
            text = r.recognize_google(audio, language='bn-IN')
        except:
            text = r.recognize_google(audio, language='en-IN')
        st.session_state.voice_text = text
        st.sidebar.success(f"You said: {st.session_state.voice_text}")
    except:
        st.sidebar.error("Bujhte parini, abar bolo")

voice_lower = st.session_state.voice_text.lower()
options = ["SC/ST", "street vendor", "small business", "farmer", "tailor"]
index = 0

# Bangla keyword o add korlam
if "street" in voice_lower or "vendor" in voice_lower or "হকার" in voice_lower:
    index = 1
elif "small" in voice_lower or "business" in voice_lower or "mudra" in voice_lower or "ব্যবসা" in voice_lower:
    index = 2
elif "farm" in voice_lower or "kisan" in voice_lower or "chash" in voice_lower or "কৃষক" in voice_lower or "চাষ" in voice_lower:
    index = 3
elif "tail" in voice_lower or "দর্জি" in voice_lower or "টেইলার" in voice_lower:
    index = 4
elif "sc" in voice_lower or "st" in voice_lower or "dalit" in voice_lower:
    index = 0

business = st.sidebar.selectbox("Business Type", options, index=index)
state = st.sidebar.selectbox("State", ["West Bengal", "All", "Bihar", "UP"])
income = st.sidebar.number_input("Monthly Income (Rs)", value=1000)

# --- PDF Function ---
def create_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="SASVA - Your Best Schemes", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for _, row in dataframe.iterrows():
        pdf.cell(200, 10, txt=f"{row['name']} - Score {row['score']}/100", ln=True)
        pdf.multi_cell(0, 8, txt=f"Benefit: {row['benefit']}\nEligibility: {row['eligibility']}\n")
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

if st.button("Find Best Schemes - Voice Search"):
    filtered = df[df["for"].str.contains(business, case=False)]
    if filtered.empty:
        filtered = df
    
    st.session_state.filtered_df = filtered # PDF er jonno save korlam
    st.success(f"Found {len(filtered)} best schemes for you!")

    for _, row in filtered.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['name']} - Score: {row['score']}/100")
            st.write(f"**Benefit:** {row['benefit']}")
            st.write(f"**Eligibility:** {row['eligibility']}")
            st.button("Apply Now", key=row['name'])

# --- 2. PDF DOWNLOAD BUTTON ---
if 'filtered_df' in st.session_state:
    pdf_bytes = create_pdf(st.session_state.filtered_df)
    st.download_button(
        label="📄 Download My Plan as PDF",
        data=pdf_bytes,
        file_name="SASVA_Schemes.pdf",
        mime="application/pdf"
    )
