import streamlit as st
import pandas as pd
import speech_recognition as sr

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

# Voice Assistant - Cloud e cholar moto
st.sidebar.write("🎤 Voice Assistant")
audio_file = st.sidebar.audio_input("Bolo... SC/ST / farmer / street vendor")

if audio_file:
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        st.session_state.voice_text = r.recognize_google(audio)
        st.sidebar.success(f"You said: {st.session_state.voice_text}")
    except:
        st.sidebar.error("Bujhte parini, abar bolo")

voice_lower = st.session_state.voice_text.lower()
options = ["SC/ST", "street vendor", "small business", "farmer", "tailor"]
index = 0

if "street" in voice_lower or "vendor" in voice_lower:
    index = 1
elif "small" in voice_lower or "business" in voice_lower or "mudra" in voice_lower:
    index = 2
elif "farm" in voice_lower or "kisan" in voice_lower or "chash" in voice_lower:
    index = 3
elif "tail" in voice_lower:
    index = 4
elif "sc" in voice_lower or "st" in voice_lower or "dalit" in voice_lower:
    index = 0

business = st.sidebar.selectbox("Business Type", options, index=index)
state = st.sidebar.selectbox("State", ["West Bengal", "All", "Bihar", "UP"])
income = st.sidebar.number_input("Monthly Income (Rs)", value=1000)

if st.button("Find Best Schemes - Voice Search"):
    filtered = df[df["for"].str.contains(business, case=False)]
    if filtered.empty:
        filtered = df

    st.success(f"Found {len(filtered)} best schemes for you!")

    for _, row in filtered.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['name']} - Score: {row['score']}/100")
            st.write(f"**Benefit:** {row['benefit']}")
            st.write(f"**Eligibility:** {row['eligibility']}")
            st.button("Apply Now", key=row['name'])
