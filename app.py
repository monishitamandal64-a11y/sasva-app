"""SASVA - AI driven scheme matching for marginalised entrepreneurs.

Team NEXUS | SIH 2026 | Problem ID SIH26092 | IIC_TMSL_P9_S10

Streamlit client. Talks to the FastAPI server when it is reachable and falls
back to the local matching engine when it is not, so the demo always runs.

    streamlit run client/app.py
"""

from __future__ import annotations

import io
import json
import os
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

# Make the shared engine importable whether we run from the repo root or /client
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
   sys.path.insert(0, str(ROOT))
import engine  # noqa: E402  (path set above)

API_BASE = os.getenv("SASVA_API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="SASVA | SchemeSetu",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================================
# STYLE
# ==========================================================================

CSS = """
<style>
#MainMenu, header[data-testid="stHeader"], footer {visibility: hidden; height: 0;}
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1180px;}
html, body, [class*="st-"] {font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;}

.sasva-header {
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 18px;
  padding: 14px 22px; display: flex; align-items: center; gap: 16px;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.06); margin-bottom: 18px;
}
.sasva-header .emblem {
  width: 46px; height: 46px; border-radius: 12px; flex: 0 0 46px;
  background: linear-gradient(160deg, #ff9933 0%, #ffffff 50%, #138808 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; border: 1px solid #e2e8f0;
}
.sasva-header .mark {
  width: 46px; height: 46px; border-radius: 12px; flex: 0 0 46px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff; font-weight: 800; font-size: 15px; letter-spacing: .5px;
  display: flex; align-items: center; justify-content: center;
}
.sasva-header h1 {font-size: 20px; margin: 0; color: #0f172a; font-weight: 800; line-height: 1.2;}
.sasva-header p {margin: 2px 0 0; font-size: 12.5px; color: #64748b;}
.sasva-header .nav {margin-left: auto; font-size: 13px; color: #475569; font-weight: 600;}
.sasva-header .nav span {opacity: .45; padding: 0 8px;}

@keyframes floatUpDown {
  0%   {transform: translateY(0);}
  50%  {transform: translateY(-14px);}
  100% {transform: translateY(0);}
}
.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff; max-width: 800px; margin: 8px auto 22px; padding: 34px 28px;
  border-radius: 24px; text-align: center;
  box-shadow: 0 22px 50px rgba(102, 126, 234, 0.32);
  animation: floatUpDown 3.5s ease-in-out infinite;
}
.welcome-card h2 {margin: 0; font-size: 31px; font-weight: 800; letter-spacing: -.4px;}
.welcome-card p {margin: 10px 0 0; font-size: 16px; opacity: .93;}
.welcome-card .pill {
  display: inline-block; margin-top: 16px; padding: 7px 18px; border-radius: 999px;
  background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.35);
  font-size: 13.5px; font-weight: 600;
}

.sync-strip {
  max-width: 800px; margin: 0 auto 8px; padding: 11px 18px; border-radius: 14px;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
  border: 1px solid #bbf7d0; color: #14532d; font-size: 13px; text-align: center;
}
.sync-strip b {color: #166534;}
.sync-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: #22c55e; margin-right: 7px; animation: floatUpDown 2s ease-in-out infinite;
}

.scheme-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  padding: 20px; border-radius: 16px; border: 1px solid #e2e8f0;
  border-left: 6px solid #22C55E; box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  transition: transform .18s ease, box-shadow .18s ease; margin-bottom: 6px;
}
.scheme-card:hover {transform: translateY(-3px); box-shadow: 0 14px 34px rgba(15,23,42,.10);}
.scheme-card.warn {border-left-color: #f59e0b;}
.scheme-card h3 {margin: 0 0 2px; font-size: 18.5px; color: #0f172a; font-weight: 750;}
.scheme-card .sub {font-size: 12.5px; color: #64748b; margin-bottom: 12px;}
.scheme-card .benefit {font-size: 14.5px; color: #1e293b; line-height: 1.55;}

.badge {
  display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: 12px;
  font-weight: 700; margin: 0 6px 8px 0;
}
.badge-green {background: #dcfce7; color: #15803d; border: 1px solid #86efac;}
.badge-amber {background: #fef3c7; color: #b45309; border: 1px solid #fcd34d;}
.badge-blue  {background: #e0e7ff; color: #4338ca; border: 1px solid #c7d2fe;}
.badge-grey  {background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;}

.bd-wrap {margin-top: 14px; padding-top: 12px; border-top: 1px dashed #e2e8f0;}
.bd-title {font-size: 11.5px; font-weight: 800; color: #475569; margin-bottom: 8px;}
.bd-row {display: flex; align-items: center; gap: 10px; margin-bottom: 5px;}
.bd-label {width: 168px; font-size: 12px; color: #475569; flex: 0 0 168px;}
.bd-track {flex: 1; height: 8px; border-radius: 999px; background: #eef2f7; overflow: hidden;}
.bd-fill {height: 8px; border-radius: 999px; background: linear-gradient(90deg, #667eea, #764ba2);}
.bd-val {width: 66px; text-align: right; font-size: 12px; font-weight: 700; color: #334155;}

.section-title {
  font-size: 19px; font-weight: 800; color: #0f172a;
  margin: 26px 0 10px; padding-left: 12px; border-left: 5px solid #667eea;
}
.soft-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px 20px;
  box-shadow: 0 4px 18px rgba(15,23,42,.05);
}
.blocker {font-size: 12.5px; color: #b45309; margin-top: 8px;}
.foot {text-align: center; color: #94a3b8; font-size: 12px; margin-top: 34px; line-height: 1.7;}

div.stButton > button {
  border-radius: 12px; font-weight: 650; border: 1px solid #e2e8f0;
  transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
}
div.stButton > button:hover {
  transform: translateY(-2px); box-shadow: 0 10px 22px rgba(102,126,234,.25);
  border-color: #667eea; color: #4338ca;
}
div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none; color: #fff;
}
div.stDownloadButton > button {border-radius: 12px; font-weight: 650;}
div.stDownloadButton > button:hover {transform: translateY(-2px); border-color: #667eea;}

@media (max-width: 780px) {
  .block-container {padding-left: .8rem; padding-right: .8rem;}
  .sasva-header {flex-wrap: wrap; gap: 10px; padding: 12px 14px;}
  .sasva-header .nav {margin-left: 0; width: 100%;}
  .welcome-card {padding: 24px 18px; border-radius: 20px;}
  .welcome-card h2 {font-size: 23px;}
  .bd-label {width: 118px; flex: 0 0 118px; font-size: 11px;}
  .scheme-card {padding: 16px;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def H(markup: str) -> None:
    """Render HTML without Streamlit treating indented lines as code."""
    lines = [ln.strip() for ln in textwrap.dedent(markup).strip().splitlines()]
    st.markdown("".join(lines), unsafe_allow_html=True)


# ==========================================================================
# LANGUAGE
# ==========================================================================

T = {
    "English": {
        "welcome": "Welcome to SchemeSetu - SASVA",
        "tagline": "Find the government scheme that actually fits you, in one minute.",
        "langs": "22 Languages Supported",
        "pick": "Choose your language",
        "search_ph": "Type: women / rural / food / trading...",
        "enter": "⏎ ENTER",
        "results": "Matched schemes",
        "no_results": "Nothing matched that. Try women, rural, food, artisan or trading.",
        "eligible": "Eligible",
        "breakdown": "AI MATCH BREAKDOWN",
        "guide": "Step-by-step application guide and document list",
        "steps": "How to apply",
        "docs": "Documents you need to keep ready",
        "save": "💾 Save",
        "pdf": "📄 Real PDF",
        "wa": "📲 WhatsApp",
        "voice": "🔊 Voice",
        "track": "📈 Track Success",
        "tracking": "X. Success Tracking",
        "feedback": "Feedback and self learning loop",
        "notify": "Notification preference",
    },
    "हिन्दी": {
        "welcome": "स्कीमसेतु - सास्वा में आपका स्वागत है",
        "tagline": "एक मिनट में वह सरकारी योजना खोजें जो आप पर लागू होती है।",
        "langs": "22 भाषाओं में उपलब्ध",
        "pick": "अपनी भाषा चुनें",
        "search_ph": "लिखें: महिला / ग्रामीण / खाद्य / व्यापार...",
        "enter": "⏎ खोजें",
        "results": "आपके लिए योजनाएँ",
        "no_results": "कुछ नहीं मिला। महिला, ग्रामीण, खाद्य या व्यापार लिखकर देखें।",
        "eligible": "पात्रता",
        "breakdown": "एआई मैच विश्लेषण",
        "guide": "आवेदन की चरणबद्ध जानकारी और दस्तावेज़",
        "steps": "आवेदन कैसे करें",
        "docs": "आवश्यक दस्तावेज़",
        "save": "💾 सेव",
        "pdf": "📄 पीडीएफ",
        "wa": "📲 व्हाट्सएप",
        "voice": "🔊 आवाज़",
        "track": "📈 प्रगति",
        "tracking": "X. सफलता ट्रैकिंग",
        "feedback": "प्रतिक्रिया और सेल्फ लर्निंग लूप",
        "notify": "सूचना का माध्यम",
    },
    "বাংলা": {
        "welcome": "স্কিমসেতু - সাসভা তে স্বাগতম",
        "tagline": "এক মিনিটে আপনার জন্য উপযুক্ত সরকারি প্রকল্প খুঁজুন।",
        "langs": "২২টি ভাষা সমর্থিত",
        "pick": "আপনার ভাষা বাছুন",
        "search_ph": "লিখুন: মহিলা / গ্রামীণ / খাদ্য / ব্যবসা...",
        "enter": "⏎ খুঁজুন",
        "results": "আপনার জন্য প্রকল্প",
        "no_results": "কিছু মেলেনি। মহিলা, গ্রামীণ, খাদ্য বা ব্যবসা লিখে দেখুন।",
        "eligible": "যোগ্যতা",
        "breakdown": "এআই ম্যাচ বিশ্লেষণ",
        "guide": "আবেদনের ধাপ ও নথির তালিকা",
        "steps": "কীভাবে আবেদন করবেন",
        "docs": "প্রয়োজনীয় নথি",
        "save": "💾 সেভ",
        "pdf": "📄 পিডিএফ",
        "wa": "📲 হোয়াটসঅ্যাপ",
        "voice": "🔊 কণ্ঠ",
        "track": "📈 ট্র্যাক",
        "tracking": "X. সফলতা ট্র্যাকিং",
        "feedback": "মতামত ও সেলফ লার্নিং লুপ",
        "notify": "বিজ্ঞপ্তির মাধ্যম",
    },
}
GTTS_LANG = {"English": "en", "हिन्दी": "hi", "বাংলা": "bn"}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "English")
    return T.get(lang, T["English"]).get(key, T["English"][key])


# ==========================================================================
# API LAYER (server first, local engine as fallback)
# ==========================================================================


def _api(path: str, payload: Dict[str, Any] | None = None, timeout: int = 4) -> Any:
    url = f"{API_BASE}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_alive() -> bool:
    """Probe the server once per session, then remember the answer.

    Without this every rerun would pay the connection timeout when the client
    is deployed alone, for example on Streamlit Cloud.
    """
    if "_api_ok" not in st.session_state:
        try:
            _api("/health", timeout=2)
            st.session_state["_api_ok"] = True
        except Exception:
            st.session_state["_api_ok"] = False
    return bool(st.session_state["_api_ok"])


def fetch_matches(profile: Dict[str, Any], query: str, limit: int = 12) -> List[Dict[str, Any]]:
    if api_alive():
        try:
            return _api("/match", {"profile": profile, "query": query, "limit": limit})["schemes"]
        except Exception:
            st.session_state["_api_ok"] = False
    return engine.match_schemes(profile, query=query, limit=limit)


def fetch_sync() -> Dict[str, str]:
    if api_alive():
        try:
            return _api("/sync")
        except Exception:
            st.session_state["_api_ok"] = False
    return engine.sync_status()


def do_resync() -> Dict[str, str]:
    if api_alive():
        try:
            return _api("/resync?role=Admin", {})
        except Exception:
            st.session_state["_api_ok"] = False
    return engine.force_resync()


def push_feedback(entry: Dict[str, Any]) -> Dict[str, Any]:
    if api_alive():
        try:
            return _api("/feedback", entry)
        except Exception:
            st.session_state["_api_ok"] = False
    return engine.save_feedback(entry)


# ==========================================================================
# SESSION STATE
# ==========================================================================

DEFAULTS = {
    "lang": "English",
    "page": "Home",
    "role": "User",
    "user_name": "",
    "logged_in": False,
    "query": "",
    "ran_search": False,
    "saved": [],
    "tracking": {},
    "feedback": [],
    "notify": "None",
    "audio": {},
    "profile": dict(engine.DEFAULT_PROFILE),
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


# ==========================================================================
# PDF / VOICE / SHARE
# ==========================================================================

_PDF_MAP = {
    "₹": "Rs. ", "–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
    "•": "-", "→": "->", "…": "...", "\u00a0": " ",
}


def _ascii(text: str) -> str:
    out = str(text)
    for bad, good in _PDF_MAP.items():
        out = out.replace(bad, good)
    return out.encode("latin-1", "replace").decode("latin-1")


@st.cache_data(show_spinner=False)
def build_pdf(scheme_id: str, applicant: str, eligible_pct: int) -> bytes:
    """Real PDF via fpdf2, returned as bytes for st.download_button."""
    from fpdf import FPDF

    s = engine.get_scheme(scheme_id) or {}
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    pdf.set_fill_color(102, 126, 234)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 19)
    pdf.set_xy(14, 7)
    pdf.cell(0, 8, _ascii("SASVA | SchemeSetu"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, _ascii("AI driven scheme matching for marginalised entrepreneurs"))

    pdf.set_text_color(15, 23, 42)
    pdf.set_xy(14, 36)
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(182, 7, _ascii(s.get("name", scheme_id)))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(182, 5.5, _ascii(f"{s.get('ministry', '')}  |  Scheme code {scheme_id}"))
    pdf.ln(2)

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        182, 5.5,
        _ascii(
            f"Prepared for: {applicant or 'Applicant'}    "
            f"Eligibility match: {eligible_pct}%    "
            f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        ),
    )
    pdf.ln(3)

    def block(title: str, lines: List[str], numbered: bool = False) -> None:
        pdf.set_font("Helvetica", "B", 11.5)
        pdf.set_fill_color(238, 242, 247)
        pdf.cell(182, 8, _ascii("  " + title), new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(1.5)
        pdf.set_font("Helvetica", "", 10)
        for i, line in enumerate(lines, start=1):
            prefix = f"{i}. " if numbered else "-  "
            pdf.multi_cell(182, 5.4, _ascii(prefix + line))
        pdf.ln(3)

    block("Benefit", [s.get("benefit", "")])
    block(
        "Eligibility snapshot",
        [
            "Categories: " + ", ".join(s.get("categories", [])),
            "Sectors: " + ", ".join(s.get("sectors", [])),
            "Area: " + ", ".join(s.get("regions", [])),
            f"Age: {s.get('age_min', 18)} to {s.get('age_max', 70)} years",
            f"Funding band: Rs {s.get('funding_min', 0):,} to Rs {s.get('funding_max', 0):,}",
        ],
    )
    block("Documents required", s.get("docs", []))
    block("Application steps", s.get("steps", []), numbered=True)
    block("Where to apply", [s.get("link", ""), "Helpline: " + s.get("helpline", "")])

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 130, 145)
    pdf.multi_cell(
        182, 4.6,
        _ascii(
            "Figures are taken from the public scheme page at the time of data "
            "collection and must be verified on the ministry portal before "
            "applying. Generated by SASVA, Team NEXUS, SIH 2026, SIH26092."
        ),
    )
    return bytes(pdf.output())


def build_voice(scheme_id: str, eligible_pct: int) -> bytes | None:
    """gTTS narration. Returns None when the network is unavailable."""
    from gtts import gTTS

    s = engine.get_scheme(scheme_id) or {}
    lang = st.session_state.get("lang", "English")
    if lang == "हिन्दी":
        script = (
            f"{s.get('short', '')} योजना. मंत्रालय {s.get('ministry', '')}. "
            f"आपकी पात्रता {eligible_pct} प्रतिशत है. लाभ: {s.get('benefit', '')}"
        )
    elif lang == "বাংলা":
        script = (
            f"{s.get('short', '')} প্রকল্প. মন্ত্রক {s.get('ministry', '')}. "
            f"আপনার যোগ্যতা {eligible_pct} শতাংশ. সুবিধা: {s.get('benefit', '')}"
        )
    else:
        script = (
            f"{s.get('name', '')}, run by the {s.get('ministry', '')}. "
            f"Your eligibility match is {eligible_pct} percent. "
            f"Benefit: {s.get('benefit', '')}"
        )
    try:
        buf = io.BytesIO()
        gTTS(text=script, lang=GTTS_LANG.get(lang, "en"), slow=False).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


def whatsapp_link(scheme: Dict[str, Any], eligible_pct: int) -> str:
    msg = (
        f"*{scheme.get('name')}*\n"
        f"Ministry: {scheme.get('ministry')}\n"
        f"Eligibility match: {eligible_pct}%\n"
        f"Benefit: {scheme.get('benefit')}\n"
        f"Apply: {scheme.get('link')}\n\n"
        f"Shared via SASVA SchemeSetu"
    )
    return "https://wa.me/?text=" + urllib.parse.quote(msg)


# ==========================================================================
# I. HEADER
# ==========================================================================

head_left, head_right = st.columns([7, 2.4], vertical_alignment="center")
with head_left:
    H(
        """
        <div class="sasva-header">
        <div class="emblem">🇮🇳</div>
        <div class="mark">SAS<br>VA</div>
        <div>
        <h1>SASVA &nbsp;·&nbsp; SchemeSetu</h1>
        <p>Government of India scheme discovery for marginalised entrepreneurs &nbsp;|&nbsp; Team NEXUS &nbsp;|&nbsp; SIH26092</p>
        </div>
        <div class="nav">Home <span>|</span> About Us</div>
        </div>
        """
    )
with head_right:
    nav_a, nav_b = st.columns(2)
    if nav_a.button("Home", use_container_width=True, key="nav_home"):
        st.session_state.page = "Home"
    if nav_b.button("About Us", use_container_width=True, key="nav_about"):
        st.session_state.page = "About"

# ==========================================================================
# IV. SIDEBAR: LOGIN, ROLE, PROFILE
# ==========================================================================

with st.sidebar:
    st.markdown("### 🔐 Login")
    role = st.selectbox("Login as", ["User", "CSC Operator", "Admin"], key="role_pick")
    name = st.text_input("Your name", value=st.session_state.user_name, key="name_in")
    if st.button("Login / Update", type="primary", use_container_width=True, key="login_btn"):
        st.session_state.role = role
        st.session_state.user_name = name.strip()
        st.session_state.logged_in = bool(name.strip())
        st.rerun()

    if st.session_state.logged_in:
        st.success(f"{st.session_state.user_name} · {st.session_state.role}")
    else:
        st.info("Browsing as guest. Add a name to save schemes.")

    st.markdown("---")
    st.markdown("### 👤 Entrepreneur profile")
    p = st.session_state.profile
    p["category"] = st.selectbox(
        "Social category", ["General", "SC", "ST", "OBC", "Minority", "PwD"],
        index=["General", "SC", "ST", "OBC", "Minority", "PwD"].index(p["category"]),
        key="p_cat",
    )
    p["gender"] = st.selectbox(
        "Gender", ["Female", "Male", "Other"],
        index=["Female", "Male", "Other"].index(p["gender"]), key="p_gender",
    )
    p["age"] = st.number_input("Age", 18, 75, int(p["age"]), key="p_age")
    p["sector"] = st.selectbox(
        "Business sector",
        ["Food Processing", "Manufacturing", "Services", "Trading",
         "Handicraft", "Agriculture Allied", "Technology"],
        index=["Food Processing", "Manufacturing", "Services", "Trading",
               "Handicraft", "Agriculture Allied", "Technology"].index(p["sector"]),
        key="p_sector",
    )
    p["funding_need"] = st.number_input(
        "Funding needed (Rs)", 10000, 50000000, int(p["funding_need"]), step=10000, key="p_fund",
    )
    p["region"] = st.radio("Area", ["Rural", "Urban"],
                           index=0 if p["region"] == "Rural" else 1,
                           horizontal=True, key="p_region")
    p["state"] = st.text_input("State", value=p.get("state", ""), key="p_state")
    p["name"] = st.session_state.user_name
    st.session_state.profile = p

    st.markdown("---")
    st.caption(f"API: {'🟢 connected' if api_alive() else '🟡 offline, using local engine'}")
    st.caption(f"💾 Saved: {len(st.session_state.saved)}  ·  📈 Tracked: {len(st.session_state.tracking)}")


# ==========================================================================
# ABOUT PAGE
# ==========================================================================

if st.session_state.page == "About":
    H('<div class="section-title">About SASVA</div>')
    H(
        """
        <div class="soft-card">
        <p style="margin-top:0"><b>SASVA</b> is a scheme matching layer for entrepreneurs who lose money and time
        to the wrong application. Women, SC and ST founders, street vendors, artisans and micro food units are
        eligible for schemes they never hear about, and apply for ones they can never qualify for.</p>
        <p>SASVA reads a short profile, scores every scheme in the catalogue on four auditable weights, and returns
        a ranked shortlist with the documents, the steps and the portal link. Every card can leave the app as a real
        PDF, a WhatsApp message or spoken audio, so a CSC operator can hand it to someone who does not read English.</p>
        <p style="margin-bottom:0"><b>Team NEXUS</b> &nbsp;·&nbsp; Smart India Hackathon 2026 &nbsp;·&nbsp;
        Problem ID SIH26092 &nbsp;·&nbsp; Theme Smart Automation &nbsp;·&nbsp; Team ID IIC_TMSL_P9_S10</p>
        </div>
        """
    )
    s = engine.stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Schemes live", s["schemes_live"])
    c2.metric("In sync pipeline", s["schemes_in_pipeline"])
    c3.metric("Ministries covered", len(s["ministries"]))
    c4.metric("Languages", s["languages_supported"])
    H('<div class="section-title">Languages in the roadmap</div>')
    st.write(" · ".join(engine.LANGUAGES))
    H('<div class="foot">SASVA · Team NEXUS · SIH 2026</div>')
    st.stop()


# ==========================================================================
# II. FLOATING WELCOME + LANGUAGE
# ==========================================================================

H(
    f"""
    <div class="welcome-card">
    <h2>{t('welcome')}</h2>
    <p>{t('tagline')}</p>
    <div class="pill">🌐 {t('langs')}</div>
    </div>
    """
)

lang_cols = st.columns(3)
for col, label in zip(lang_cols, ["English", "हिन्दी", "বাংলা"]):
    picked = st.session_state.lang == label
    if col.button(
        f"{'✅ ' if picked else '🌐 '}{label}",
        use_container_width=True,
        type="primary" if picked else "secondary",
        key=f"lang_{label}",
    ):
        st.session_state.lang = label
        st.rerun()

# ==========================================================================
# III. AUTO-FEED SIMULATION
# ==========================================================================

sync = fetch_sync()
H(
    f"""
    <div class="sync-strip">
    <span class="sync-dot"></span>
    Last synced from <b>myscheme.gov.in</b> on <b>{sync['last_synced']}</b>
    &nbsp;|&nbsp; Next sync: <b>Tonight 12 AM</b>
    &nbsp;|&nbsp; {sync['schemes_live']} schemes live, {sync['schemes_in_pipeline']} in the crawl pipeline
    </div>
    """
)

if st.session_state.role == "Admin":
    _, mid, _ = st.columns([1, 2, 1])
    if mid.button("🔄 Force Re-sync Govt Database Now", type="primary",
                  use_container_width=True, key="resync_btn"):
        new = do_resync()
        st.success(f"Re-sync complete. Feed timestamp is now {new['last_synced']}.")

# ==========================================================================
# V. SEARCH + ENTER
# ==========================================================================

H('<div class="section-title">Find your scheme</div>')
s_col, b_col = st.columns([5, 1.2], vertical_alignment="bottom")
query = s_col.text_input(
    "Search", value=st.session_state.query, placeholder=t("search_ph"),
    label_visibility="collapsed", key="search_in",
)
if b_col.button(t("enter"), type="primary", use_container_width=True, key="enter_btn"):
    st.session_state.query = query
    st.session_state.ran_search = True
    st.rerun()

quick = st.columns(5)
for col, chip in zip(quick, ["women", "rural", "food", "trading", "artisan"]):
    if col.button(chip, use_container_width=True, key=f"chip_{chip}"):
        st.session_state.query = chip
        st.session_state.ran_search = True
        st.rerun()

active_query = st.session_state.query
results = fetch_matches(st.session_state.profile, active_query, limit=12)

# ==========================================================================
# VI + VII + VIII. CARDS, ACTIONS, EXPANDER
# ==========================================================================

label = f'{t("results")} · {len(results)}'
if active_query:
    label += f' · "{active_query}"'
H(f'<div class="section-title">{label}</div>')

if not results:
    st.warning(t("no_results"))

for s in results:
    m = s["match"]
    pct = m["eligible_pct"]
    tone = "badge-green" if pct >= 75 else "badge-amber" if pct >= 55 else "badge-grey"
    card_class = "scheme-card" if pct >= 55 and not m["blockers"] else "scheme-card warn"

    rows = "".join(
        f'<div class="bd-row">'
        f'<div class="bd-label">{k.title()} ({m["weights"][k]}%)</div>'
        f'<div class="bd-track"><div class="bd-fill" style="width:{(v / m["weights"][k]) * 100:.0f}%"></div></div>'
        f'<div class="bd-val">{v} / {m["weights"][k]}</div>'
        f'</div>'
        for k, v in m["breakdown"].items()
    )
    blockers = (
        '<div class="blocker">⚠️ ' + " · ".join(m["blockers"]) + "</div>"
        if m["blockers"] else ""
    )

    # Module 3 (Personal Rank Recommendation): tier badge + 2-line explainer.
    # Reuses existing badge/sub classes only, no new CSS added.
    tier = m.get("tier", "")
    tier_tone = {
        "Highly Recommended": "badge-green",
        "Also Eligible": "badge-blue",
        "Not Eligible": "badge-grey",
    }.get(tier, "badge-grey")
    tier_badge = f'<span class="badge {tier_tone}">⭐ {tier}</span>' if tier else ""
    why_lines = m.get("why", [])
    why_html = (
        '<div class="sub" style="margin-top:6px;">' + "<br>".join(why_lines) + "</div>"
        if why_lines else ""
    )

    H(
        f"""
        <div class="{card_class}">
        <h3>{s['name']}</h3>
        <div class="sub">{s.get('short', '')} &nbsp;·&nbsp; Rs {s['funding_min']:,} to Rs {s['funding_max']:,}</div>
        <div>
        <span class="badge {tone}">{pct}% {t('eligible')}</span>
        <span class="badge badge-blue">🏛️ {s['ministry']}</span>
        <span class="badge badge-grey">{m['verdict']}</span>
        {tier_badge}
        </div>
        <div class="benefit">{s['benefit']}</div>
        {why_html}
        <div class="bd-wrap">
        <div class="bd-title">{t('breakdown')}</div>
        {rows}
        </div>
        {blockers}
        </div>
        """
    )

    a1, a2, a3, a4, a5 = st.columns(5)
    sid = s["id"]

    # 1. Save
    if a1.button(t("save"), use_container_width=True, key=f"save_{sid}"):
        if sid not in st.session_state.saved:
            st.session_state.saved.append(sid)
        st.toast(f"Saved {s.get('short', sid)}", icon="💾")

    # 2. Real PDF
    with a2:
        st.download_button(
            t("pdf"),
            data=build_pdf(sid, st.session_state.user_name, pct),
            file_name=f"SASVA_{sid}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"pdf_{sid}",
        )

    # 3. WhatsApp
    a3.link_button(t("wa"), whatsapp_link(s, pct), use_container_width=True)

    # 4. Voice
    if a4.button(t("voice"), use_container_width=True, key=f"voice_{sid}"):
        audio = build_voice(sid, pct)
        if audio:
            st.session_state.audio[sid] = audio
        else:
            st.session_state.audio.pop(sid, None)
            st.warning("Voice needs an internet connection for the Google TTS call.")

    # 5. Track Success
    if a5.button(t("track"), use_container_width=True, key=f"track_{sid}"):
        st.session_state.tracking[sid] = {
            "name": s.get("short", sid),
            "pct": 65,
            "stage": "Documents verified, awaiting bank appraisal",
            "started": datetime.now().strftime("%d %b %Y"),
        }
        st.toast(f"Tracking {s.get('short', sid)}", icon="📈")

    if sid in st.session_state.audio:
        st.audio(st.session_state.audio[sid], format="audio/mp3")

    with st.expander(f"📋 {t('guide')} · {s.get('short', sid)}"):
        g1, g2 = st.columns([1.25, 1])
        with g1:
            st.markdown(f"**{t('steps')}**")
            for i, step in enumerate(s.get("steps", []), start=1):
                st.markdown(f"{i}. {step}")
            st.markdown(f"[Open the official portal]({s.get('link', '')})")
        with g2:
            st.markdown(f"**{t('docs')}**")
            for d in s.get("docs", []):
                st.markdown(f"- {d}")
            st.caption(f"Helpline: {s.get('helpline', '')}")
    st.write("")

# ==========================================================================
# SAVED SHORTLIST
# ==========================================================================

if st.session_state.saved:
    H('<div class="section-title">💾 Your saved shortlist</div>')
    saved_rows = []
    for sid in st.session_state.saved:
        sch = engine.get_scheme(sid)
        if sch:
            saved_rows.append({
                "Scheme": sch["name"],
                "Ministry": sch["ministry"],
                "Funding band": f"Rs {sch['funding_min']:,} - Rs {sch['funding_max']:,}",
            })
    st.dataframe(pd.DataFrame(saved_rows), use_container_width=True, hide_index=True)
    if st.button("Clear shortlist", key="clear_saved"):
        st.session_state.saved = []
        st.rerun()

# ==========================================================================
# IX. SUCCESS TRACKING
# ==========================================================================

H(f'<div class="section-title">{t("tracking")}</div>')
if not st.session_state.tracking:
    st.info("Nothing tracked yet. Press Track Success on any scheme card above.")
else:
    for sid, tr in st.session_state.tracking.items():
        box = st.container()
        with box:
            top, right = st.columns([4, 1])
            top.markdown(f"**{tr['name']}** · {tr['stage']}")
            right.markdown(f"**{tr['pct']}%**")
            st.progress(tr["pct"])
            st.caption(f"Started {tr['started']} · application id SASVA-{sid}-{tr['started'].replace(' ', '')}")
    if st.button("Reset tracking", key="reset_track"):
        st.session_state.tracking = {}
        st.rerun()

# ==========================================================================
# XI. NOTIFICATION PREFERENCE
# ==========================================================================

H('<div class="section-title">🔔 XI. Notifications</div>')
n1, n2 = st.columns([1, 2])
st.session_state.notify = n1.selectbox(
    t("notify"), ["None", "WhatsApp", "SMS", "Email"],
    index=["None", "WhatsApp", "SMS", "Email"].index(st.session_state.notify),
    key="notify_pick",
)
if st.session_state.notify == "None":
    n2.info("No alerts. New matching schemes will only appear inside the app.")
else:
    n2.success(
        f"{st.session_state.notify} alerts on. You get a message when the nightly "
        f"sync finds a new scheme that matches your profile."
    )

# ==========================================================================
# X. FEEDBACK AND SELF LEARNING LOOP
# ==========================================================================

H(f'<div class="section-title">💬 X. {t("feedback")}</div>')
f1, f2 = st.columns([2, 1])
with f1:
    fb_scheme = st.selectbox(
        "Which scheme is this about?",
        ["General feedback"] + [s["id"] for s in results],
        key="fb_scheme",
    )
    fb_text = st.text_area(
        "Tell us what was wrong or missing",
        placeholder="The subsidy amount for my district was different, or this scheme did not fit me because...",
        key="fb_text",
    )
    helpful = st.radio("Was the match helpful?", ["Yes", "No"], horizontal=True, key="fb_helpful")
    if st.button("Submit feedback", type="primary", key="fb_submit"):
        if not fb_text.strip():
            st.warning("Add a line of feedback first.")
        else:
            res = push_feedback({
                "name": st.session_state.user_name,
                "role": st.session_state.role,
                "scheme_id": None if fb_scheme == "General feedback" else fb_scheme,
                "helpful": helpful == "Yes",
                "comment": fb_text.strip(),
            })
            st.session_state.feedback.append({"scheme": fb_scheme, "comment": fb_text.strip()})
            st.success("Self-learning loop updated!")
            st.caption(
                f"{res.get('signal', {}).get('tokens_learned', 0)} keyword signals queued "
                f"for the nightly retrain · {res.get('total_feedback', 1)} responses in this session"
            )
with f2:
    H(
        """
        <div class="soft-card">
        <b>How the loop works</b>
        <ol style="padding-left:18px; margin:8px 0 0; font-size:13.5px; color:#475569; line-height:1.7">
        <li>Your comment is tokenised into keyword signals.</li>
        <li>Signals adjust the scheme keyword weights.</li>
        <li>The nightly job re-ranks the catalogue.</li>
        <li>Next visit, the shortlist reflects it.</li>
        </ol>
        </div>
        """
    )

# ==========================================================================
# ADMIN / OPERATOR DASHBOARD
# ==========================================================================

if st.session_state.role in ("Admin", "CSC Operator"):
    H(f'<div class="section-title">🛠️ {st.session_state.role} dashboard</div>')
    stats = engine.stats()
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Schemes live", stats["schemes_live"])
    d2.metric("Crawl pipeline", stats["schemes_in_pipeline"])
    d3.metric("Feedback this session", len(st.session_state.feedback))
    d4.metric("Applications tracked", len(st.session_state.tracking))

    catalogue = pd.DataFrame([
        {
            "ID": s["id"],
            "Scheme": s["name"],
            "Ministry": s["ministry"],
            "Min (Rs)": s["funding_min"],
            "Max (Rs)": s["funding_max"],
            "Categories": ", ".join(s["categories"]),
            "Sectors": ", ".join(s["sectors"]),
            "Area": ", ".join(s["regions"]),
        }
        for s in engine.all_schemes()
    ])
    st.dataframe(catalogue, use_container_width=True, hide_index=True, height=330)

    if st.session_state.role == "Admin":
        st.caption("Ministry spread")
        st.dataframe(
            pd.DataFrame(stats["ministries"], columns=["Ministry", "Schemes"]),
            use_container_width=True, hide_index=True,
        )
        if st.session_state.feedback:
            st.caption("Feedback captured in this session")
            st.dataframe(pd.DataFrame(st.session_state.feedback),
                         use_container_width=True, hide_index=True)

# ==========================================================================
# FOOTER
# ==========================================================================

H(
    """
    <div class="foot">
    <b>SASVA · SchemeSetu</b> · AI driven scheme matching for marginalised entrepreneurs<br>
    Team NEXUS · Smart India Hackathon 2026 · Problem ID SIH26092 · Theme Smart Automation · Team ID IIC_TMSL_P9_S10<br>
    Scheme figures are seeded from public government pages and must be verified on the ministry portal before applying.
    </div>
    """
)
