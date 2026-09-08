import streamlit as st
import pandas as pd
import re
from io import BytesIO
from gtts import gTTS

st.set_page_config(page_title="SchemeSetu | SASVA", page_icon="🏛️", layout="wide")

# --- DATA ---
INDIAN_STATES = ["West Bengal", "Bihar", "Uttar Pradesh", "Maharashtra", "Delhi", "Rajasthan", "All India"]

TRANSLATIONS = {
    "English": {"title": "SchemeSetu - SASVA", "subtitle": "Your AI Scheme Assistant", "entrepreneur_profile": "Entrepreneur Profile", "state_label": "State", "age_label": "Age", "gender_label": "Gender", "category_label": "Category", "sector_label": "Sector", "tab_matched": "Matched Schemes", "tab_analytics": "Analytics", "ministry_label": "Ministry", "benefit_label": "Benefit", "open_portal": "Apply on Official Portal"},
    "Hindi (हिन्दी)": {"title": "योजना सेतु - SASVA", "subtitle": "आपका AI योजना सहायक", "entrepreneur_profile": "उद्यमी प्रोफाइल", "state_label": "राज्य", "age_label": "आयु", "gender_label": "लिंग", "category_label": "श्रेणी", "sector_label": "क्षेत्र", "tab_matched": "मिलान योजनाएं", "tab_analytics": "विश्लेषण", "ministry_label": "मंत्रालय", "benefit_label": "लाभ", "open_portal": "आधिकारिक पोर्टल पर आवेदन करें"},
    "Bengali (বাংলা)": {"title": "স্কিমসেতু - SASVA", "subtitle": "তোমার AI স্কিম সহকারী", "entrepreneur_profile": "উদ্যোক্তা প্রোফাইল", "state_label": "রাজ্য", "age_label": "বয়স", "gender_label": "লিঙ্গ", "category_label": "ক্যাটাগরি", "sector_label": "সেক্টর", "tab_matched": "মিলে যাওয়া স্কিম", "tab_analytics": "অ্যানালিটিক্স", "ministry_label": "মন্ত্রক", "benefit_label": "সুবিধা", "open_portal": "অফিসিয়াল পোর্টালে আবেদন"}
}

SCHEMES_DATABASE = [
    {"id": "PMEGP", "name": "PM Employment Generation Programme", "ministry": "MSME", "description": "35% subsidy for SC/ST/Women in rural areas.", "status": "Active", "min_loan": 50000, "max_loan": 1000000, "min_age": 18, "max_age": 60, "documents": "Aadhaar, Project Report, Caste Certificate", "guidelines": "Policy Clause 4.2: Age>18, Rural, Investment <10L", "apply_link": "https://www.kviconline.gov.in/pmegpeportal/", "main_benefit": "35% Subsidy"},
    {"id": "MUDRA", "name": "MUDRA Loan Yojana", "ministry": "Finance", "description": "Loan up to 10L for non-farm enterprises.", "status": "Active", "min_loan": 50000, "max_loan": 1000000, "min_age": 18, "max_age": 65, "documents": "Aadhaar, Business Proof, Bank Statement", "guidelines": "Policy Clause 2.1: Any non-farm enterprise", "apply_link": "https://www.mudra.org.in/", "main_benefit": "Loan upto 10L"},
]

def t(key):
    lang = st.session_state.get("selected_lang", "English")
    return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

# --- LANGUAGE SELECTION ---
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = None

if st.session_state.selected_lang is None:
    st.markdown("""
    <style>
    @keyframes floatUpDown {
      0%, 100% { transform: translateY(0px); box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
      50% { transform: translateY(-8px); box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
    }
    .floating-welcome {
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      padding:
