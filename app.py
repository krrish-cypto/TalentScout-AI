import streamlit as st
import os
import json
import re
import tempfile
from groq import Groq
from dotenv import load_dotenv
import PyPDF2
import docx
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURATION ---
GREETINGS = {"hi", "hello", "hey", "hii", "hiyo", "hiya", "hola", "namaste"}
SENSITIVE_FIELDS = {"Email Address", "Phone Number"}
FAST_MODEL = "llama-3.1-8b-instant"
SMART_MODEL = "llama-3.3-70b-versatile"

# --- CRITICAL FIX: PAGE CONFIG MUST BE FIRST ---
st.set_page_config(
    page_title="TalentScout AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NOW LOAD ENV AND CLIENT ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

@st.cache_resource
def get_groq_client():
    if not api_key: return None
    return Groq(api_key=api_key)

client = get_groq_client()

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

# --- TRANSLATIONS & LANGUAGE HELPERS ---
TRANSLATIONS = {
    "English": {
        "greeting": "Hello! I'm TalentScout. Nice to meet you. Before we begin, a quick note: your responses are confidential. Could you please tell me your {field}?",
        "thanks_brief": "Thanks {name} — could you provide your {field}?",
        "thanks_sensitive": "Thanks {name} — to help me tailor the interview, could you provide your {field}? (Confidential)",
        "phase_transition": "Thank you {name}. I have your details. I will now ask a few technical questions based on your stack: {stack}.",
        "invalid_email": "That doesn't look like a valid email address.",
        "invalid_phone": "That doesn't look like a valid phone number.",
    },
    "Hindi": {
        "greeting": "नमस्ते! मैं TalentScout हूँ। शुरुआत से पहले: आपकी प्रतिक्रियाएं गोपनीय हैं। कृपया मुझे अपना {field} बताएं?",
        "thanks_brief": "धन्यवाद {name} — क्या आप अपना {field} प्रदान कर सकते हैं?",
        "thanks_sensitive": "धन्यवाद {name} — क्या आप अपना {field} दे सकते हैं? यह गोपनीय है।",
        "phase_transition": "धन्यवाद {name}। अब मैं आपके स्टैक के आधार पर कुछ तकनीकी प्रश्न पूछूंगा: {stack}।",
        "invalid_email": "यह मान्य ईमेल नहीं है।",
        "invalid_phone": "यह मान्य फोन नंबर नहीं है।",
    },
    "Spanish": {
        "greeting": "¡Hola! Soy TalentScout. Tus respuestas son confidenciales. ¿Podrías decirme tu {field}?",
        "thanks_brief": "Gracias {name} — ¿Podrías proporcionar tu {field}?",
        "thanks_sensitive": "Gracias {name} — ¿Podrías proporcionar tu {field}? Es confidencial.",
        "phase_transition": "Gracias {name}. Ahora haré preguntas técnicas basadas en tu stack: {stack}.",
        "invalid_email": "Correo no válido.",
        "invalid_phone": "Teléfono no válido.",
    },
    "French": {
        "greeting": "Bonjour ! Je suis TalentScout. Vos réponses sont confidentielles. Pouvez-vous me dire votre {field} ?",
        "thanks_brief": "Merci {name} — pourriez-vous fournir votre {field} ?",
        "thanks_sensitive": "Merci {name} — pourriez-vous fournir votre {field} ? C'est confidentiel.",
        "phase_transition": "Merci {name}. Je vais maintenant poser des questions techniques sur votre stack : {stack}.",
        "invalid_email": "E-mail non valide.",
        "invalid_phone": "Numéro de téléphone non valide.",
    },
    "German": {
        "greeting": "Hallo! Ich bin TalentScout. Ihre Antworten sind vertraulich. Könnten Sie mir Ihren {field} mitteilen?",
        "thanks_brief": "Danke {name} — könnten Sie Ihren {field} angeben?",
        "thanks_sensitive": "Danke {name} — könnten Sie Ihren {field} angeben? Dies ist vertraulich.",
        "phase_transition": "Danke {name}. Ich werde nun technische Fragen zu Ihrem Stack stellen: {stack}.",
        "invalid_email": "Ungültige E-Mail.",
        "invalid_phone": "Ungültige Telefonnummer.",
    },
    "Hinglish": {
        "greeting": "Hii! Main TalentScout hoon. Start karne se pehle - aapke answers confidential hain. Kya aap mujhe apna {field} bata sakte ho?",
        "thanks_brief": "Thanks {name} — aap apna {field} de sakte ho?",
        "thanks_sensitive": "Shukriya {name} — aap apna {field} share kar sakte ho? Ye confidential hai.",
        "phase_transition": "Shukriya {name}! Ab main aapke stack ke based pe technical questions puchta hoon: {stack}.",
        "invalid_email": "Ye valid email nahi lag raha.",
        "invalid_phone": "Ye valid phone number nahi lag raha.",
    },
}

def get_translation(lang: str, key: str, field: str = "", name: str = "", stack: str = "") -> str:
    """Get translation for a key in the given language. Fallback to English if not found."""
    if lang not in TRANSLATIONS:
        lang = "English"
    message = TRANSLATIONS[lang].get(key, TRANSLATIONS["English"].get(key, ""))
    
    # Safely format the message with available placeholders
    return message.format(field=field, name=name, stack=stack)

def detect_hinglish(text: str) -> bool:
    """Detect if text is in Hinglish (Roman-script Hindi with English words)."""
    hinglish_indicators = {
        "haan", "nahi", "theek", "ok", "okk", "shukriya", "thanks",
        "kya", "aap", "mujhe", "apna", "kar", "sakte", "daal", "acha", "chalega",
        "baat", "karo", "bol", "samajh", "dekh", "main", "maine", "hoon", "ho",
        "ke", "ka", "ki", "se", "par", "aur", "ya", "toh", "bas", "tha",
        "sey", "mein", "woh", "ye", "voh", "inko", "unko", "humein", "unhein"
    }
    words = text.lower().split()
    hinglish_word_count = sum(1 for w in words if any(w.startswith(h) or w.endswith(h) for h in hinglish_indicators))
    return hinglish_word_count >= len(words) * 0.3

# --- RESUME PARSING ---
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def parse_resume_with_ai(text):
    # NOTE: "Desired Position" is EXCLUDED here so the bot asks for it later.
    prompt = f"""
    Extract the following fields from the resume text below.
    Return ONLY valid JSON.
    Keys: "Full Name", "Email Address", "Phone Number", "Years of Experience", "Current Location", "Tech Stack".
    
    IMPORTANT: 
    - DO NOT extract "Desired Position". We will ask the user for this.
    - If "Tech Stack" is scattered, combine it into a comma-separated string.
    - If a field is missing, use null.
    
    Resume Text:
    {text[:4000]}
    """
    try:
        completion = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"} 
        )
        content = completion.choices[0].message.content
        content = clean_response_text(content)
        return json.loads(content)
    except Exception as e:
        st.error(f"Resume Parsing Error: {e}")
        return {}

# --- INTELLIGENT INPUT PROCESSOR ---
def process_user_input(user_input, current_field, language="English"):
    prompt = f"""
    You are an AI Interviewer ({language}). 
    We are currently asking the candidate for: "{current_field}".
    User Input: "{user_input}"
    
    TASK:
    1. If the user is providing the answer, extract ONLY the value. Set "is_answer": true.
    2. If the user is asking a QUESTION (e.g., "Why do you need this?", "What is this for?"):
       - Explain the reason professionally.
       - Set "is_answer": false.
    3. If user says "skip", extracted_value: "Skipped".
    
    RETURN JSON ONLY:
    {{
        "is_answer": boolean,
        "extracted_value": string or null,
        "response_message": string (required if is_answer is false)
    }}
    """
    try:
        completion = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except:
        return {"is_answer": True, "extracted_value": user_input}

# --- PDF & GRAPH ---
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='#4A90E2', alpha=0.15)
    ax.plot(angles, values, color='#4A90E2', linewidth=2)
    
    # Simplified Graph Scale (0-100)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], color="grey", size=8)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    
    temp_chart = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_chart.name, format='png', bbox_inches='tight')
    plt.close()
    return temp_chart.name

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TalentScout AI - Candidate Evaluation', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(data):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Details
    pdf.cell(0, 10, f"Candidate Name: {str(data.get('name', 'N/A')).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
    pdf.cell(0, 10, f"Position: {str(data.get('position', 'N/A')).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
    
    # Tech Stack (wrapped with multi_cell)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Tech Stack:", ln=True)
    pdf.set_font("Arial", size=11)
    tech_stack_text = str(data.get('tech_stack', 'N/A')).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, tech_stack_text)
    
    pdf.ln(5)
    
    # Verdict
    verdict = data.get('verdict', 'Pending')
    color = (0, 128, 0) if "Hire" in verdict else (255, 0, 0)
    pdf.set_text_color(*color)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"VERDICT: {verdict}", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Graph + Summary
    scores = {
        "Tech": data.get("technical_score", 0),
        "Comm": data.get("communication_score", 0),
        "Prob Solv": data.get("problem_solving_score", 0),
        "Exp Fit": data.get("experience_relevance", 0)
    }
    chart_path = create_radar_chart(scores)
    
    # Add Chart
    pdf.image(chart_path, x=60, y=None, w=90)
    os.unlink(chart_path)
    
    # Add Graph Summary (New Feature)
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 11)
    pdf.set_text_color(100, 100, 100) # Grey color for explanation
    summary_text = f"Graph Interpretation: {data.get('graph_summary', 'Analysis of core competencies.')}"
    # Clean unicode for PDF
    summary_text = str(summary_text).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, summary_text, align='C')
    pdf.set_text_color(0, 0, 0) # Reset color
    
    # Strengths
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Strengths:", ln=True)
    pdf.set_font("Arial", size=11)
    for s in data.get('strengths', []): 
        s = str(s).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 7, f"- {s}", ln=True)
    
    # Improvements
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Improvements:", ln=True)
    pdf.set_font("Arial", size=11)
    for i in data.get('improvement_areas', []): 
        i = str(i).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 7, f"- {i}", ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# --- SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "phase" not in st.session_state: st.session_state.phase = "gathering_info"
if "collected_info" not in st.session_state: st.session_state.collected_info = {}
if "resume_uploaded" not in st.session_state: st.session_state.resume_uploaded = False

REQUIRED_FIELDS = ["Full Name", "Email Address", "Phone Number", "Years of Experience", "Desired Position(s)", "Current Location", "Tech Stack"]

# --- HELPER: FIND NEXT MISSING FIELD ---
def get_next_missing_field():
    for field in REQUIRED_FIELDS:
        if field not in st.session_state.collected_info:
            return field
    return None

# --- HEADER ---
c1, c2, c3 = st.columns([1, 8, 1])
with c2:
    st.markdown('<div class="main-header">TalentScout AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">High-Performance • Multilingual • Resume Parsing</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    
    language_options = {"English": "🇺🇸", "Hindi": "🇮🇳", "Spanish": "🇪🇸", "French": "🇫🇷", "German": "🇩🇪"}
    selected_lang = st.selectbox("Language", list(language_options.keys()), format_func=lambda x: f"{language_options[x]} {x}")
    
    st.divider()
    st.markdown("### 📄 Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
    
    if uploaded_file and not st.session_state.resume_uploaded:
        with st.spinner("Parsing resume with AI..."):
            try:
                # Text Extraction
                file_text = ""
                if uploaded_file.type == "application/pdf":
                    file_text = extract_text_from_pdf(uploaded_file)
                elif "wordprocessingml" in uploaded_file.type:
                    file_text = extract_text_from_docx(uploaded_file)
                else:
                    file_text = str(uploaded_file.read(), "utf-8")
                
                # AI Parsing
                extracted_data = parse_resume_with_ai(file_text)
                
                # Fill Info
                if extracted_data:
                    found_fields = []
                    for key, value in extracted_data.items():
                        if value and str(value).lower() != "null" and key in REQUIRED_FIELDS:
                            st.session_state.collected_info[key] = str(value)
                            found_fields.append(key)
                    
                    st.session_state.resume_uploaded = True
                    st.success(f"✅ Extracted: {', '.join(found_fields[:3])}...")
            except Exception as e:
                st.error(f"Error parsing file: {e}")

    st.divider()
    if st.button("🔄 Start New Interview", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- SYSTEM PROMPT ---
info_summary = ", ".join([f"{k}: {v}" for k, v in st.session_state.collected_info.items()])
next_missing = get_next_missing_field()

system_prompt = f"""
You are 'TalentScout', an AI recruiter.
CURRENT LANGUAGE: {selected_lang}.
CANDIDATE INFO KNOWN: {info_summary}
PROTOCOL:
1. If all info is known (Tech Stack, etc), START TECHNICAL INTERVIEW immediately.
2. If info is missing ({next_missing}), ask for it specifically.
3. If technical interview, ask questions based on: {st.session_state.collected_info.get('Tech Stack', 'General')}.
KEEP RESPONSES CONCISE.
"""

if not st.session_state.messages:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
else:
    st.session_state.messages[0]["content"] = system_prompt

# --- MAIN CHAT UI ---
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] != "system":
            avatar = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

# --- RESUME TRANSITION LOGIC ---
if st.session_state.resume_uploaded and len(st.session_state.messages) == 1:
    next_field = get_next_missing_field()
    name = st.session_state.collected_info.get("Full Name", "Candidate")
    
    if next_field:
        st.session_state.phase = "gathering_info"
        msg = get_translation(selected_lang, "greeting", field=next_field, name=name)
    else:
        st.session_state.phase = "technical_interview"
        stack = st.session_state.collected_info.get("Tech Stack", "")
        msg = get_translation(selected_lang, "phase_transition", name=name, stack=stack)
    
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.rerun()

# --- INPUT HANDLER ---
if prompt := st.chat_input("Type your response..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)

    # 1. INFO GATHERING
    if st.session_state.phase == "gathering_info":
        current_field = get_next_missing_field()
        lang_to_use = selected_lang
        if detect_hinglish(prompt): lang_to_use = "Hinglish"

        # Handle Start (No Resume)
        if not st.session_state.collected_info and prompt.lower() in GREETINGS:
             assistant_text = get_translation(lang_to_use, "greeting", current_field)
             st.session_state.messages.append({"role": "assistant", "content": assistant_text})
             with st.chat_message("assistant", avatar="🤖"): st.markdown(assistant_text)
        else:
            # INTELLIGENT PROCESSING
            processed = process_user_input(prompt, current_field, lang_to_use)
            
            if not processed["is_answer"]:
                response = processed["response_message"]
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant", avatar="🤖"): st.markdown(response)
            else:
                answer_val = processed.get("extracted_value", prompt)
                
                # Validate
                invalid = False
                if current_field == "Email Address" and not is_valid_email(answer_val):
                    invalid = True
                    msg = get_translation(lang_to_use, "invalid_email")
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    with st.chat_message("assistant", avatar="🤖"): st.markdown(msg)
                elif current_field == "Phone Number" and not is_valid_phone(answer_val):
                    invalid = True
                    msg = get_translation(lang_to_use, "invalid_phone")
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    with st.chat_message("assistant", avatar="🤖"): st.markdown(msg)
                
                if not invalid:
                    if current_field: st.session_state.collected_info[current_field] = answer_val
                    
                    next_f = get_next_missing_field()
                    if next_f:
                        name = st.session_state.collected_info.get("Full Name", "")
                        key = "thanks_sensitive" if next_f in SENSITIVE_FIELDS else "thanks_brief"
                        msg = get_translation(lang_to_use, key, field=next_f, name=name)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                        with st.chat_message("assistant", avatar="🤖"): st.markdown(msg)
                    else:
                        st.session_state.phase = "technical_interview"
                        name = st.session_state.collected_info.get("Full Name", "")
                        stack = st.session_state.collected_info.get("Tech Stack", "")
                        msg = get_translation(lang_to_use, "phase_transition", name=name, stack=stack)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                        with st.chat_message("assistant", avatar="🤖"): st.markdown(msg)

    # 2. TECHNICAL INTERVIEW
    else:
        with st.chat_message("assistant", avatar="🤖"):
            placeholder = st.empty()
            full_resp = ""
            try:
                stream = client.chat.completions.create(
                    model=FAST_MODEL,
                    messages=st.session_state.messages,
                    stream=True,
                    temperature=0.6,
                    max_tokens=250
                )
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_resp += content
                        placeholder.markdown(full_resp + "▌")
                placeholder.markdown(full_resp)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
            except Exception as e:
                st.error(f"Error: {e}")

# --- REPORT SECTION ---
with st.sidebar:
    st.divider()
    st.markdown("### 📊 Evaluation")
    if st.button("📝 Generate Report", type="primary"):
        if len(st.session_state.messages) < 4:
            st.toast("⚠️ Chat more to get a report!", icon="⚠️")
        else:
            with st.spinner("Analyzing candidate..."):
                prompt_text = """
                Generate JSON evaluation.
                Fields: name, position, tech_stack, 
                technical_score (0-100), communication_score (0-100), problem_solving_score (0-100), experience_relevance (0-100),
                verdict (Hire/No Hire/Maybe), strengths (list), improvement_areas (list),
                graph_summary (1 brief sentence explaining what the scores mean for this candidate).
                """
                msgs = st.session_state.messages + [{"role": "user", "content": prompt_text}]
                try:
                    res = client.chat.completions.create(
                        model=SMART_MODEL,
                        messages=msgs,
                        response_format={"type": "json_object"}
                    )
                    report = json.loads(res.choices[0].message.content)
                    st.session_state.last_report = report
                    st.toast("Report Ready!", icon="✅")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

# --- DASHBOARD & PDF DOWNLOAD ---
if "last_report" in st.session_state:
    r = st.session_state.last_report
    st.markdown("---")
    st.subheader(f"Evaluation: {r.get('name', 'Candidate')}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tech Score", r.get('technical_score'))
    c2.metric("Comm Score", r.get('communication_score'))
    c3.metric("Verdict", r.get('verdict'))
    
    try:
        pdf_bytes = generate_pdf_report(r)
        d1, d2 = st.columns(2)
        d1.download_button("📥 Download JSON", json.dumps(r, indent=2), "report.json", "application/json")
        d2.download_button("📄 Download PDF Report", pdf_bytes, "candidate_report.pdf", "application/pdf")
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")