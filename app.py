import streamlit as st
import os
import json
import re
import tempfile
# 1. Force Page Config to be the VERY FIRST Streamlit command
st.set_page_config(
    page_title="TalentScout AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Fix Matplotlib for Cloud (Must be before importing pyplot)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from groq import Groq
from dotenv import load_dotenv
import PyPDF2
import docx
from fpdf import FPDF

# --- SETUP & SECRETS ---
load_dotenv()

# Robust API Key Retrieval
def get_api_key():
    # Try local .env
    key = os.getenv("GROQ_API_KEY")
    # Try Streamlit Secrets
    if not key:
        try:
            key = st.secrets["GROQ_API_KEY"]
        except:
            pass
    return key

api_key = get_api_key()

# --- CACHING & CLIENT SETUP ---
@st.cache_resource
def get_groq_client(key):
    if not key: return None
    return Groq(api_key=key)

client = get_groq_client(api_key)


# --- CUSTOM CSS (Professional Theme) ---
st.markdown("""
    <style>
    .stApp {
# ... rest of your code remains exactly the same ...
        background: linear-gradient(to bottom right, #f8f9fa, #eef2f3);
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #4A90E2, #6DD5FA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
    }
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    </style>
""", unsafe_allow_html=True)

if not client:
    st.error("❌ Error: GROQ_API_KEY not found. Please check your .env file.")
    st.stop()

# --- HELPER FUNCTIONS ---
def clean_response_text(text: str) -> str:
    """Smartly extracts JSON from mixed text."""
    if not text: return ""
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)
    else:
        text = re.sub(r"```(?:json)?\n?", "", text)
        text = text.replace('```', '')
    return text.strip()

def is_valid_email(email: str) -> bool:
    if not email: return False
    return re.match(r"^[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}$", email.strip()) is not None

def is_valid_phone(phone: str) -> bool:
    if not phone: return False
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "English": {
        "greeting": "Hello! I'm TalentScout. Please provide your {field}.",
        "thanks_brief": "Thanks {name} — provide {field}.",
        "thanks_sensitive": "Thanks {name} — provide {field}? (Confidential)",
        "phase_transition": "Thanks {name}. Asking questions for: {stack}.",
        "invalid_email": "Invalid email.",
        "invalid_phone": "Invalid phone.",
    }
}
# Fallback for other languages
for lang in ["Hindi", "Spanish", "French", "German", "Hinglish"]:
    TRANSLATIONS[lang] = TRANSLATIONS["English"]

def get_translation(lang: str, key: str, field: str = "", name: str = "", stack: str = "") -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["English"])
    msg = lang_dict.get(key, TRANSLATIONS["English"][key])
    return msg.format(field=field, name=name, stack=stack)

def detect_hinglish(text: str) -> bool:
    hinglish_indicators = {"haan", "nahi", "theek", "ok", "shukriya", "kya", "aap", "mujhe", "karo"}
    words = text.lower().split()
    return sum(1 for w in words if any(w.startswith(h) for h in hinglish_indicators)) >= len(words) * 0.3

# --- RESUME PARSING ---
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "".join([p.extract_text() for p in pdf.pages])

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_resume_with_ai(text):
    if not client: return {}
    prompt = f"""
    Extract JSON: "Full Name", "Email Address", "Phone Number", "Years of Experience", "Current Location", "Tech Stack".
    Resume: {text[:4000]}
    """
    try:
        res = client.chat.completions.create(model=FAST_MODEL, messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
        return json.loads(clean_response_text(res.choices[0].message.content))
    except: return {}

# --- INTELLIGENT INPUT ---
def process_user_input(user_input, current_field, language="English"):
    if not client: return {"is_answer": True, "extracted_value": user_input}
    prompt = f"""
    Context: Asking for "{current_field}". User said: "{user_input}".
    Return JSON: {{"is_answer": bool, "extracted_value": string, "response_message": string}}
    """
    try:
        res = client.chat.completions.create(model=FAST_MODEL, messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"is_answer": True, "extracted_value": user_input}

# --- PDF REPORT ---
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values()) + [list(scores.values())[0]]
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist() + [0]
    
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='#4A90E2', alpha=0.15)
    ax.plot(angles, values, color='#4A90E2', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=8)
    
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp.name, format='png', bbox_inches='tight')
    plt.close()
    return tmp.name

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Candidate Evaluation', 0, 1, 'C')
        self.ln(5)

def generate_pdf_report(data):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    clean = lambda t: str(t).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"Name: {clean(data.get('name'))}", ln=True)
    pdf.multi_cell(0, 7, f"Stack: {clean(data.get('tech_stack'))}")
    pdf.ln(5)
    
    # Chart
    scores = {"Tech": data.get("technical_score",0), "Comm": data.get("communication_score",0), "Prob": data.get("problem_solving_score",0)}
    chart = create_radar_chart(scores)
    pdf.image(chart, x=70, w=70)
    os.unlink(chart)
    
    return pdf.output(dest="S").encode("latin-1")

# --- APP LOGIC ---
if "messages" not in st.session_state: st.session_state.messages = []
if "phase" not in st.session_state: st.session_state.phase = "gathering_info"
if "collected_info" not in st.session_state: st.session_state.collected_info = {}
if "resume_uploaded" not in st.session_state: st.session_state.resume_uploaded = False

REQUIRED_FIELDS = ["Full Name", "Email Address", "Phone Number", "Years of Experience", "Desired Position(s)", "Tech Stack"]

def get_next_missing_field():
    for f in REQUIRED_FIELDS:
        if f not in st.session_state.collected_info: return f
    return None

# --- UI LAYOUT ---
st.title("TalentScout AI ⚡")

with st.sidebar:
    st.header("Controls")
    lang = st.selectbox("Language", ["English", "Hindi", "Spanish"])
    
    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
    if uploaded_file and not st.session_state.resume_uploaded:
        with st.spinner("Parsing..."):
            text = ""
            if uploaded_file.type == "application/pdf": text = extract_text_from_pdf(uploaded_file)
            elif "wordprocessing" in uploaded_file.type: text = extract_text_from_docx(uploaded_file)
            else: text = str(uploaded_file.read(), "utf-8")
            
            data = parse_resume_with_ai(text)
            if data:
                for k, v in data.items():
                    if k in REQUIRED_FIELDS and v: st.session_state.collected_info[k] = str(v)
                st.session_state.resume_uploaded = True
                st.success("Resume Parsed!")
                st.rerun()

    if st.button("Reset Interview"):
        st.session_state.clear()
        st.rerun()

# --- CHAT LOGIC ---
# System Prompt Update
missing = get_next_missing_field()
sys_prompt = f"Recruiter AI. Language: {lang}. Missing Info: {missing}. If missing, ask for it. If done, ask technical question based on stack."

if not st.session_state.messages:
    st.session_state.messages.append({"role": "system", "content": sys_prompt})
else:
    st.session_state.messages[0]["content"] = sys_prompt

# Display Chat
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): st.markdown(m["content"])

# Handle Input
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Info Gathering Phase
    if st.session_state.phase == "gathering_info":
        curr = get_next_missing_field()
        if not curr:
            st.session_state.phase = "technical"
            st.rerun()
        
        # Simple processing
        st.session_state.collected_info[curr] = prompt
        
        # Check next
        next_f = get_next_missing_field()
        if next_f:
            resp = get_translation(lang, "thanks_brief", field=next_f, name=st.session_state.collected_info.get("Full Name", ""))
        else:
            st.session_state.phase = "technical"
            resp = get_translation(lang, "phase_transition", name=st.session_state.collected_info.get("Full Name", ""), stack=st.session_state.collected_info.get("Tech Stack", ""))
        
        st.session_state.messages.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"): st.markdown(resp)

    # Technical Phase
    else:
        if client:
            try:
                stream = client.chat.completions.create(model=FAST_MODEL, messages=st.session_state.messages, stream=True)
                with st.chat_message("assistant"):
                    resp = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": resp})
            except Exception as e:
                st.error(f"API Error: {e}")

# --- REPORT GENERATION ---
with st.sidebar:
    if st.button("Generate Report"):
        if not client:
            st.error("API Key missing")
        elif len(st.session_state.messages) < 4:
            st.warning("Chat more first!")
        else:
            with st.spinner("Analyzing..."):
                prompt = "Generate JSON: name, tech_stack, technical_score(0-100), communication_score(0-100), problem_solving_score(0-100), verdict, graph_summary."
                msgs = st.session_state.messages + [{"role":"user", "content":prompt}]
                try:
                    res = client.chat.completions.create(model=SMART_MODEL, messages=msgs, response_format={"type":"json_object"})
                    rep = json.loads(res.choices[0].message.content)
                    st.session_state.last_report = rep
                except Exception as e:
                    st.error(f"Failed: {e}")

if "last_report" in st.session_state:
    rep = st.session_state.last_report
    st.write("---")
    st.subheader(f"Report: {rep.get('name')}")
    col1, col2 = st.columns(2)
    col1.metric("Tech Score", rep.get('technical_score'))
    col2.metric("Verdict", rep.get('verdict'))
    
    pdf = generate_pdf_report(rep)
    st.download_button("Download PDF", pdf, "report.pdf", "application/pdf")