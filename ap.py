import streamlit as st
import pandas as pd
import speech_recognition as sr

schemes = [
    {"name": "PM SVANidhi", "benefit": "Collateral-free loan up to Rs 10,000", "eligibility": "Street vendor with vending certificate", "for": "street vendor", "score": 95},
    {"name": "Stand-Up India", "benefit": "Loan Rs 10 Lakh to 1 Crore", "eligibility": "SC/ST or Woman entrepreneur", "for": "sc/st", "score": 50},
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

st.sidebar.header("Your Profile")
business_type = st.sidebar.selectbox("Business Type", ["SC/ST", "Farmer", "Street Vendor", "Small Business", "Tailor"])

st.write("### Find Schemes - Voice Search")
audio = st.audio_input("🎤 Speak Business Type - Click to record")

if audio:
    r = sr.Recognizer()
    with sr.AudioFile(audio) as source:
        audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data)
            st.session_state.voice_text = text
            st.success(f"You said: {text}")
        except:
            st.error("Could not understand audio, please try again.")

if st.button("Find Best Schemes"):
    search_term = st.session_state.voice_text if st.session_state.voice_text else business_type
    search_term = search_term.lower()
    
    filtered = df[df['for'].str.contains(search_term, case=False, na=False)]
    if filtered.empty:
        filtered = df.sort_values(by='score', ascending=False)

    for index, row in filtered.iterrows():
        st.subheader(row['name'])
        st.write(f"**Benefit:** {row['benefit']}")
        st.write(f"**Eligibility:** {row['eligibility']}")
        st.divider()
