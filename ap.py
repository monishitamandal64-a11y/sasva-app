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
    {"name": "PM SVANidhi", "benefit": "Loan up to Rs 50,000 without guarantee", "eligibility": "Street vendor / Hawker", "for": "street vendor", "score": 95, "link": "https://pmsvanidhi.mohua.gov.in"},
    {"name": "PM Vishwakarma", "benefit": "Free toolkit + Rs 3 Lakh loan @5% interest", "eligibility": "Tailor, Barber, Carpenter, Goldsmith (18 trades)", "for": "tailor", "score": 96, "link": "https://pmvishwakarma.gov.in"},
    {"name": "Stand-Up India", "benefit": "Loan Rs 10 Lakh to 1 Crore for startup", "eligibility": "SC/ST or Woman entrepreneur", "for": "SC/ST", "score": 94, "link": "https://www.standupmitra.in"},
    {"name": "MUDRA Yojana - Shishu", "benefit": "Loan up to Rs 50,000", "eligibility": "Any small shop / business starter", "for": "small business", "score": 92, "link": "https://www.mudra.org.in"},
    {"name": "MUDRA Yojana - Kishor", "benefit": "Loan Rs 50,001 to Rs 5 Lakh", "eligibility": "Existing small business", "for": "small business", "score": 90, "link": "https://www.mudra.org.in"},
    {"name": "PM Kisan Samman Nidhi", "benefit": "Rs 6000 per year in 3 installments", "eligibility": "All small & marginal farmers", "for": "farmer", "score": 93, "link": "https://pmkisan.gov.in"},
    {"name": "Kisan Credit Card (KCC)", "benefit": "Crop loan up to Rs 3 Lakh @4% interest", "eligibility": "Farmer, Fisherman, Animal husbandry", "for": "farmer", "score": 91, "link": "https://pmkisan.gov.in"},
    {"name": "PMEGP", "benefit": "Subsidy 15% to 35% + Loan up to Rs 50 Lakh", "eligibility": "Anyone 18+ for manufacturing/service unit", "for": "small business", "score": 89, "link": "https://www.kviconline.gov.in/pmegpeportal/"},
    {"name": "DAY-NRLM", "benefit": "Revolving fund Rs 20k-30k to SHG + Bank loan", "eligibility": "Women Self Help Group (SHG)", "for": "SC/ST", "score": 88, "link": "https://aajeevika.gov.in"},
    {"name": "PM Formalization of Micro Food (PMFME)", "benefit": "Subsidy 35% up to Rs 10 Lakh", "eligibility": "Food processing - pickle, papad, bakery", "for": "small business", "score": 87, "link": "https://pmfme.mofpi.gov.in"},
    {"name": "Weaver Mudra / Handloom Package", "benefit": "Loan up to Rs 10 Lakh + Free loom", "eligibility": "Handloom weaver", "for": "tailor", "score": 86, "link": "https://handlooms.nic.in"},
    {"name": "National SC/ST Hub", "benefit": "Marketing + Rs 25 Lakh subsidy support", "eligibility": "SC/ST MSME business", "for": "SC/ST", "score": 85, "link": "https://www.scsthub.in"},
    {"name": "Pradhan Mantri Matsya Sampada", "benefit": "60% subsidy for fish farming", "eligibility": "Fish farmer", "for": "farmer", "score": 84, "link": "https://pmmsy.dof.gov.in"},
    {"name": "Dairy Entrepreneurship Scheme", "benefit": "33% subsidy for Dairy farm", "eligibility": "Farmer / Small business", "for": "farmer", "score": 83, "link": "https://dahd.nic.in"},
    {"name": "Antyodaya Saral - Beauty Parlour Scheme", "benefit": "Free training + Rs 1 Lakh kit", "eligibility": "Woman / SC", "for": "small business", "score": 82, "link": "https://saralharyana.gov.in"},
]

df = pd.DataFrame(schemes)

# --- PDF FUNCTION FIX ---
def create_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="SASVA - Your Best Schemes", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 11)
    for i, row in dataframe.iterrows():
        name = str(row['name']).encode('latin-1', 'replace').decode('latin-1')
        benefit = str(row['benefit']).encode('latin-1', 'replace').decode('latin-1')
        eligibility = str(row['eligibility']).encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, txt=f"{i+1}. {name} - Score {row['score']}/100", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, txt=f"Benefit: {benefit}\nEligibility: {eligibility}\nLink: {row['link']}\n")
        pdf.ln(3)
    out = pdf.output(dest='S')
    if isinstance(out, str):
        return out.encode('latin-1', 'replace')
    else:
        return bytes(out)

if 'voice_text' not in st.session_state:
    st.session_state.voice_text = ""
if 'business_index' not in st.session_state:
    st.session_state.business_index = 0
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = pd.DataFrame()

st.set_page_config(page_title="SASVA")
lang = st.sidebar.selectbox("Language", ["English", "বাংলা", "हिंदी"])
t = translations[lang]

# --- MOVING WELCOME ---
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

if 'business_value'not in st.session_state:
    st.sessioj_state.business_value="SC/ST"
voice_lower = st.session_state.voice_text.lower()
options = ["SC/ST", "street vendor", "small business", "farmer", "tailor"]
new_business=st.session_state.business_value
if any(x in voice_lower for x in ["street", "vendor", "হকার"]): 
    new_business="street vendor"
elif any(x in voice_lower for x in ["small", "business", "ব্যবসা"]): 
     new_business="small business"
elif any(x in voice_lower for x in ["farm", "kisan", "কৃষক", "ফার্মার"]): 
     new_business="farmer"
elif any(x in voice_lower for x in ["tail", "দর্জি"]): 
     new_business="tailor"
elif any(x in voice_lower for x in ["sc", "st"]): 
     new_business="SC/ST"
if st.session_state.voice_text!=""and new_business!= st.session_state.business_value:
    st.session_state.business_value = new_business
    st.toast(f"Voice detected: {new_business} ✅")
    st.rerun()


business = st.sidebar.selectbox(t["business"], options, index=st.session_state.business_index)
state = st.sidebar.selectbox(t["state"], ["West Bengal", "All", "Bihar", "UP"])
income = st.sidebar.number_input(t["income"], value=1000)

if st.button(t["find_btn"]):
    filtered = df[df["for"].str.contains(business, case=False)]
    if filtered.empty:
        filtered = df.sort_values(by="score", ascending=False).head(3)
    # Atleast 3 guarantee
    if len(filtered) < 3:
        filtered = df.sort_values(by="score", ascending=False).head(3)

    filtered = filtered.sort_values(by="score", ascending=False)
    st.session_state.filtered_df = filtered
    st.success(f"{t['found']} {len(filtered)} {t['for_you']}")
    for _, row in filtered.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['name']} - {row['score']}/100")
            st.write(f"**{t['benefit']}:** {row['benefit']}")
            st.write(f"**{t['eligibility']}:** {row['eligibility']}")
            st.link_button(t["apply"], row['link'])

# --- PDF DOWNLOAD BUTTON ---
if not st.session_state.filtered_df.empty:
    st.write("---")
    pdf_bytes = create_pdf(st.session_state.filtered_df)
    st.download_button(
        label=t["download"],
        data=pdf_bytes,
        file_name="SASVA_Schemes.pdf",
        mime="application/pdf"
    )
