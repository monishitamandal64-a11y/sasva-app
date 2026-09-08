import streamlit as st
import pandas as pd
from gtts import gTTS
import os
from supabase import create_client, Client
from schemes_data import OFFICIAL_LANGUAGES_INDIA, INDIAN_STATES
import importlib
import translations
importlib.reload(translations)
from translations import TRANSLATIONS

# --- HELPER FUNCTIONS FOR FILTERING & SCORES ---
import re

def parse_number(val):
    if isinstance(val, (int, float)):
        return val
    if not val or "N/A" in str(val) or "No upper limit" in str(val):
        return float('inf')
    digits = re.sub(r'[^\d]', '', str(val))
    return int(digits) if digits else float('inf')

def filter_schemes(schemes, user_age, user_gender, user_income, user_funding):
    matched = []
    for s in schemes:
        # Age check
        min_age = parse_number(s.get("min_age", 0))
        max_age = parse_number(s.get("max_age", 100))
        if not (min_age <= user_age <= max_age):
            continue

        # Target Group / Gender check
        target = str(s.get("target_group", "") or s.get("target", "")).lower()
        gender = str(user_gender).lower()
        
        # If target group is empty or general, keep the scheme
        is_general = not target or "all" in target or "citizen" in target or "general" in target
        gender_match = is_general or (gender in target) or ("women" in target if gender == "female" else False)

        if gender_match:
            matched.append(s)
            
    # Fallback to returning all schemes if filter returns 0 matches
    return matched if len(matched) > 0 else schemes

def calculate_income_score(user_income, scheme_max_income_str):
    max_income = parse_number(scheme_max_income_str)
    if max_income == float('inf'):
        return 15, "No income ceiling limit (15% match)"
    if user_income <= max_income:
        ratio = user_income / max_income
        score = round(20 * (1 - (ratio * 0.5))) 
        return score, f"Income ₹{user_income:,} fits under limit of ₹{max_income:,} (+{score}%)"
    else:
        return 0, f"Income exceeds maximum limit of ₹{max_income:,} (+0%)"

def display_documents(docs):
    st.markdown("### 📄 Required Documents")
    if isinstance(docs, str):
        docs = [d.strip() for d in docs.split(",")]
    if isinstance(docs, list):
        for doc in docs:
            clean_doc = doc.replace("doc_", "").replace("_", " ").title()
            st.markdown(f"- {clean_doc}")
    elif isinstance(docs, dict):
        for key, val in docs.items():
            st.markdown(f"- **{key.replace('_', ' ').title()}**: {val}")

# Initialize processed_schemes at the top of app.py
processed_schemes = []

# Supabase Database Connection
SUPABASE_URL = "https://eqlefszucdkwlydcrtdx.supabase.co"
SUPABASE_KEY = "sb_publishable_gAjPwCPA24E9BNMMPBOrDQ_qRSS3RA_"  # Paste your sb_publishable key here

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

from schemes_data import SCHEMES_DATABASE as LOCAL_SCHEMES

@st.cache_data(ttl=3600)
def load_schemes():
    try:
        response = supabase.table("schemes").select("*").execute()
        return response.data if response.data else []
    except Exception:
        return []

# Fetch Supabase schemes and combine them with local schemes_data.py
db_schemes = load_schemes()
existing_ids = {s.get("id") for s in db_schemes if s.get("id")}

SCHEMES_DATABASE = list(db_schemes)
for item in LOCAL_SCHEMES:
    if item.get("id") not in existing_ids:
        SCHEMES_DATABASE.append(item)

# Page Configuration
st.set_page_config(page_title="SchemeSetu | Govt Scheme AI Matcher", page_icon="🏛️", layout="wide")

# Force visible scrollbar on all dropdown select menus
st.markdown(
    """
    <style>
    /* Target Streamlit selectbox dropdown lists */
    div[data-baseweb="popover"] ul {
        max-height: 250px !important;
        overflow-y: scroll !important;
    }
    
    /* Styling the visible scrollbar */
    div[data-baseweb="popover"] ul::-webkit-scrollbar {
        width: 10px !important;
        display: block !important;
    }
    div[data-baseweb="popover"] ul::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 5px;
    }
    div[data-baseweb="popover"] ul::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 5px;
    }
    div[data-baseweb="popover"] ul::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state for language selection
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = None

# =========================================================
# 1. FULL-PAGE LANGUAGE SELECTION SCREEN
# =========================================================
if st.session_state.selected_lang is None:
    # Header Banner
    st.markdown(
        """
        <div style="background-color: #1e1b4b; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0;">Welcome to SchemeSetu</h1>
            <p style="color: #cbd5e1; margin-top: 8px; font-size: 16px;">
                कृपया अपनी भाषा चुनें / Please select your language
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Language Button Grid (2 Columns)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("English", use_container_width=True, key="btn_en"):
            st.session_state.selected_lang = "English"
            st.rerun()
            
        if st.button("বাংলা\n\nBengali", use_container_width=True, key="btn_bn"):
            st.session_state.selected_lang = "Bengali (বাংলা)"
            st.rerun()

    with col2:
        if st.button("हिन्दी\n\nHindi", use_container_width=True, key="btn_hi"):
            st.session_state.selected_lang = "Hindi (हिन्दी)"
            st.rerun()

    # Halt execution so the main dashboard details do NOT render yet
    st.stop()

# =========================================================
# 2. MAIN APPLICATION (Runs only after language selection)
# =========================================================
selected_lang = st.session_state.selected_lang

# Sidebar Option to Switch Language Later
if st.sidebar.button("🌐 Change Language"):
    st.session_state.selected_lang = None
    st.rerun()

def t(key):
    return TRANSLATIONS.get(selected_lang, TRANSLATIONS["English"]).get(key, key)

# =========================================================
# 2. DYNAMIC APPLICATION INTERFACE (LOADED AFTER SELECTION)
# =========================================================


# Session State Initializations
if "notifications" not in st.session_state:
    st.session_state.notifications = []

# --- ACCESSIBILITY & STYLING CONTROLS ---
st.sidebar.markdown("### ♿ Accessibility & Display Tools")
font_size = st.sidebar.slider("Text Size (px)", min_value=14, max_value=24, value=16)
highlight_links = st.sidebar.checkbox("Highlight External Links")

link_style = "background-color: #FEF08A; font-weight: bold; padding: 2px 6px; border-radius: 4px;" if highlight_links else ""

st.markdown(f"""
    <style>
    html, body, [class*="css"] {{ font-size: {font_size}px !important; }}
    .header-banner {{
        background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;
        border: 1px solid #CBD5E1;
    }}
    .national-emblem {{ font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin: 0; }}
    .card {{ background-color: #FFFFFF !important; padding: 20px; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 15px; color: #0F172A !important; }}
    .card h3, .card p, .card span, .card strong {{ color: #0F172A !important; }}
    .closed-badge {{ background-color: #FEE2E2; color: #991B1B; padding: 6px 12px; border-radius: 6px; font-weight: bold; display: inline-block; }}
    .active-badge {{ background-color: #DCFCE7; color: #166534; padding: 6px 12px; border-radius: 6px; font-weight: bold; display: inline-block; }}
    </style>
""", unsafe_allow_html=True)

# --- HEADER WITH TRICOLOR & ASHOK STAMBHA BRANDING ---
st.markdown(f"""
<div class="header-banner">
    <div class="national-emblem">🏛️ {t("title")}</div>
    <div style="color: #1E293B; font-weight: 600;">{t("subtitle")}</div>
</div>
""", unsafe_allow_html=True)

# Direct Scheme Lookup
direct_search_query = st.text_input(t("search_placeholder"), value="", key="direct_search_input_key")

if direct_search_query:
    q = direct_search_query.strip().lower()
    
    found_schemes = []
    for s in SCHEMES_DATABASE:
        combined_text = " ".join([
            str(s.get("scheme_name", "")),
            str(s.get("name", "")),
            str(s.get("description", "")),
            str(s.get("ministry_or_department", "")),
            str(s.get("ministry", "")),
            str(s.get("target_group", ""))
        ]).lower()
        
        if q in combined_text:
            found_schemes.append(s)
    
    if found_schemes:
        st.success(f"Found {len(found_schemes)} scheme(s) matching '{direct_search_query}'")
        for s in found_schemes:
            s_name = s.get("scheme_name") or s.get("name") or "Scheme"
            s_ministry = s.get("ministry_or_department") or s.get("ministry") or "N/A"
            s_desc = s.get("description", "No description available.")
            s_status = s.get("status", "Active")
            min_loan = s.get("min_loan", 0)
            max_loan = s.get("max_loan", 0)
            apply_url = s.get("apply_link") or s.get("official_website_link") or "#"

            if str(s_status).lower() == 'closed':
                st.markdown(f"""
                <div class="card" style="border-left: 6px solid #EF4444; padding: 15px; margin-bottom: 10px;">
                    <h3>{s_name}</h3>
                    <p><strong>Ministry:</strong> {s_ministry}</p>
                    <div class="closed-badge">⚠️ SCHEME CLOSED</div>
                    <p style="margin-top: 10px; color: #991B1B;"><strong>Closure Notice:</strong> This scheme was officially closed.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card" style="border-left: 6px solid #22C55E; padding: 15px; margin-bottom: 10px;">
                    <h3>{s_name}</h3>
                    <p><strong>Ministry:</strong> {s_ministry}</p>
                    <div class="active-badge"> ACTIVE SCHEME</div>
                    <p style="margin-top: 10px;">{s_desc}</p>
                    <p><strong>Funded Range:</strong> {min_loan} to {max_loan}</p>
                    <a href="{apply_url}" target="_blank">Official Application Portal 🔗</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning(f"No scheme found matching '{direct_search_query}'.")

st.divider()

# --- SIDEBAR ENTREPRENEUR PROFILE ---
st.sidebar.header(f"👤 {t('entrepreneur_profile')}")
location = st.sidebar.selectbox(t("state_label"), INDIAN_STATES)
age = st.sidebar.number_input(t("age_label"), min_value=18, max_value=80, value=25)
gender = st.sidebar.selectbox(t("gender_label"), ["Female", "Male", "Transgender / Non-Binary"])
social_category = st.sidebar.selectbox(t("category_label"), ["SC", "ST", "OBC", "EWS", "UR", "Minority", "General"])
business_sector = st.sidebar.selectbox(t("sector_label"), ["Manufacturing", "Services", "Trading", "Agri-Allied", "Artisan"])
funding_needed = st.sidebar.number_input("Required Funding Amount (₹)", min_value=10000, max_value=10000000, value=500000, step=50000)
annual_income = st.sidebar.number_input("Annual Household Income (₹)", min_value=0, max_value=5000000, value=250000, step=25000)

search_clicked = st.sidebar.button("🔍 Find Matching Schemes", type="primary", use_container_width=True)

# --- REAL AI VOICE ASSISTANT ---
st.sidebar.markdown("---")
st.sidebar.markdown("🎙️ **AI Voice Assistant**")

# 1. Built-in Voice Input
audio_value = st.sidebar.audio_input("Record Voice Query")

if audio_value:
    st.sidebar.success("Voice recording captured!")

# 2. Text-to-Speech Audio Narration
def generate_audio(text_content):
    tts = gTTS(text=text_content, lang='hi' if selected_lang == 'Hindi' else 'en')
    tts.save("narration.mp3")

if st.sidebar.button("🔊 Read Top Match Aloud"):
    if processed_schemes:
        top_scheme = processed_schemes[0]
        narration_text = f"Top match is {top_scheme['name']}. {top_scheme['description']}"
        generate_audio(narration_text)
        st.sidebar.audio("narration.mp3", format="audio/mp3", autoplay=True)
    else:
        st.sidebar.warning("No schemes found to read.")


# --- AI MATCHING LOGIC WITH DETAILED REASONING ---
def calculate_breakdown(scheme, user):
    reasons = []
    
    # 1. Category Score (Safe lookup across multiple potential key names)
    raw_cats = scheme.get('eligible_categories') or scheme.get('eligibility_category') or scheme.get('target_group') or ""
    cats_str = str(raw_cats).lower()
    
    user_cat = str(user.get('category', '')).lower()
    user_gen = str(user.get('gender', '')).lower()
    
    cat_match = user_cat in cats_str if user_cat else False
    women_match = (user_gen == 'female' and ('women' in cats_str or 'female' in cats_str))
    general_match = ('all' in cats_str or 'general' in cats_str or not cats_str)
    
    if cat_match or women_match or general_match:
        category_score = 40
        reasons.append("Category eligible")
    else:
        category_score = 0

    # 2. Funding Score
    min_loan = parse_number(scheme.get('min_loan', 0)) if 'parse_number' in globals() else 0
    max_loan = parse_number(scheme.get('max_loan', float('inf'))) if 'parse_number' in globals() else float('inf')
    user_funding = user.get('funding', 0)
    
    try:
        user_funding_num = float(user_funding)
    except (ValueError, TypeError):
        user_funding_num = 0
        
    if min_loan <= user_funding_num <= max_loan or user_funding_num == 0:
        funding_score = 30
        reasons.append("Funding within range")
    else:
        funding_score = 10

    # 3. Sector Score
    scheme_sector = str(scheme.get('business_sector', scheme.get('sector', ''))).lower()
    user_sector = str(user.get('sector', '')).lower()
    
    if not scheme_sector or 'all' in scheme_sector or user_sector in scheme_sector:
        sector_score = 15
        reasons.append("Sector match")
    else:
        sector_score = 5

    # 4. Income Score
    income_str = str(scheme.get('max_income', 'No Income Bar'))
    user_income = user.get('income', 0)
    
    if 'no income' in income_str.lower():
        income_score = 15
        reasons.append("Income compliant")
    else:
        income_score = 15

    total_score = category_score + funding_score + sector_score + income_score
    return total_score, category_score, funding_score, sector_score, income_score, reasons

user_profile = {"age": age, "gender": gender, "category": social_category, "sector": business_sector, "funding": funding_needed, "income": annual_income, "location": location}

# AUTOMATIC FILTERING & ELIMINATION
active_schemes = [s for s in SCHEMES_DATABASE if str(s.get('status', 'Active')).lower() == 'active']

# Retrieve user inputs safely
ann_income = locals().get('annual_income', locals().get('income', 0))
req_funding = locals().get('funding_amount', locals().get('required_funding', 0))

# Filter schemes safely
filtered_schemes = filter_schemes(
    active_schemes, 
    user_age=user_profile.get("age", 25), 
    user_gender=user_profile.get("gender", "Female"), 
    user_income=ann_income, 
    user_funding=req_funding
)

processed_schemes = []
for scheme in filtered_schemes:
    tot, cat, fund, sec, inc, reasons = calculate_breakdown(scheme, user_profile)
    entry = scheme.copy()
    entry.update({"total_score": tot, "cat_score": cat, "fund_score": fund, "inc_score": inc, "reasons": reasons})
    processed_schemes.append(entry)

# Sort highest score first
processed_schemes = sorted(processed_schemes, key=lambda x: x.get('total_score', 0), reverse=True)

# --- MAIN TAB NAVIGATION ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"🎯 {t('tab_matched')}",
    f"📊 {t('tab_analytics')}",
    f"🤖 {t('tab_chatbot')}",
    f"❓ {t('tab_faqs')}",
    f"🔔 {t('tab_notifications')}"
])

with tab1:
    st.subheader(f"{t('active_schemes_title')} ({user_profile['category']} / {user_profile['gender']} - {user_profile['location']})")

    for idx, scheme in enumerate(processed_schemes):
        scheme_id = scheme.get('id', f"SCH_{idx}")
        # Resolve fields safely across both naming styles
        s_name = scheme.get('name') or scheme.get('scheme_name') or 'Scheme'
        s_ministry = scheme.get('ministry') or scheme.get('ministry_or_department') or 'N/A'
        s_desc = scheme.get('description', '')
        s_benefit = scheme.get('subsidy') or scheme.get('main_benefit') or 'N/A'

        min_val = scheme.get('min_loan', 0)
        max_val = scheme.get('max_loan', 0)
        
        try:
            min_str = f"₹{int(float(str(min_val).replace('₹','').replace(',',''))):,}"
        except (ValueError, TypeError):
            min_str = str(min_val)
            
        try:
            max_str = f"₹{int(float(str(max_val).replace('₹','').replace(',',''))):,}"
        except (ValueError, TypeError):
            max_str = str(max_val)

        st.markdown(f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between">
                <h3>{s_name}</h3>
                <span class="active-badge">{scheme.get('total_score', 0)}% {t('match_label')}</span>
            </div>
            <p style="color: #64748B;"><strong>{t('ministry_label')}:</strong> {s_ministry}</p>
            <p>{s_desc}</p>
            <p><strong>{t('benefit_label')}:</strong> {s_benefit}</p>
            <p><strong>{t('loan_range_label')}:</strong> {min_str} - {max_str}</p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander(f"📌 {t('expander_title')} ({s_name})"):

            st.markdown(f"#### {t('match_reasons_title')}")
            for r in scheme.get('reasons', []):
                st.write(f"- {r}")

            st.markdown(f"#### {t('guidelines_title')}")
            st.info(scheme.get('guidelines', ''))

            # Clean document display using the helper function
            display_documents(scheme.get('documents', []))

            if scheme.get('apply_link'):
                st.markdown(f"[{t('open_portal')} - ({scheme.get('name', '')})]({scheme['apply_link']})")

            # Unique key fix for WhatsApp share button using index
            st.button(f"📲 {t('share_whatsapp')} {scheme.get('name', '')}", key=f"share_{scheme_id}_{idx}")

with tab2:
    st.subheader(f"{t('tab_analytics_title')}")
    
    if processed_schemes:
        # Build structured analytics data using flexible key lookup
        analytics_list = []
        for s in processed_schemes:
            scheme_title = s.get("scheme_name") or s.get("name") or "Unknown Scheme"
            analytics_list.append({
                "Scheme": scheme_title,
                "Total Match Score (%)": s.get("total_score", 0),
                "Category Score": s.get("cat_score", 0),
                "Funding Score": s.get("fund_score", 0),
                "Income Score": s.get("inc_score", 0)
            })
            
        chart_df = pd.DataFrame(analytics_list)
        
        # Safely check column existence before setting index
        if "Scheme" in chart_df.columns:
            chart_df = chart_df.set_index("Scheme")
            
            st.markdown("### 📊 Scheme Match Breakdown")
            st.bar_chart(chart_df["Total Match Score (%)"])
            st.dataframe(chart_df, use_container_width=True)
    else:
        st.info("No scheme data available for analytics.")

with tab3:
    st.subheader(f"🤖 {t('tab_chatbot_title')}")
    st.write
