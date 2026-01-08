import streamlit as st
import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Simple greetings set to detect casual 'hi' messages
GREETINGS = {"hi", "hello", "hey", "hii", "hiyo", "hiya"}
# Fields that deserve explicit reassurance when requested
SENSITIVE_FIELDS = {"Email Address", "Phone Number"}

# 1. Setup & Caching
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# --- PERFORMANCE OPTIMIZATION: CACHING ---
# We cache the client to prevent re-initialization on every script rerun.
# This ensures efficiency under "multiple user inputs".
@st.cache_resource
def get_groq_client():
    if not api_key:
        return None
    return Groq(api_key=api_key)

client = get_groq_client()

# --- PERFORMANCE OPTIMIZATION: HYBRID MODELS ---
# Use a lightweight, blazing fast model for the chat loop (Low Latency)
FAST_MODEL = "llama-3.1-8b-instant" 
# Use a heavy reasoning model for the final report (High Quality)
SMART_MODEL = "llama-3.3-70b-versatile"

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="TalentScout AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Optimized for Aesthetics) ---
st.markdown("""
    <style>
    .stApp {
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
    div.stButton > button:hover {
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

if not client:
    st.error("❌ Error: GROQ_API_KEY not found. Please check your .env file.")
    st.stop()

# Helper: clean assistant responses so chat doesn't display raw code blocks
def clean_response_text(text: str) -> str:
    if not text:
        return ""
    # Remove code fences like ``` or ```json
    text = re.sub(r"```(?:json)?\n?", "", text)
    text = text.replace('```', '')
    text = text.strip()
    # If text is JSON, pretty-print it for storage/display
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2)
    except Exception:
        return text


# --- Validation Helpers ---
def is_valid_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip()
    # Basic email regex: local@domain.tld (keeps it permissive)
    return re.match(r"^[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}$", email) is not None


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return False
    # Allow digits, spaces, dashes, parentheses and leading +
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15


# --- TRANSLATIONS ---
TRANSLATIONS = {
    "English": {
        "greeting": "Hello! I'm TalentScout, your hiring assistant. Nice to meet you. Before we begin, a quick note: your responses are confidential and used only to assess fit for the role. Could you please tell me your {field}?",
        "thanks_brief": "Thanks {name} — could you provide your {field}?",
        "thanks_sensitive": "Thanks {name} — to help me tailor the interview and evaluation to you, could you provide your {field}? I treat this information confidentially and only use it for this assessment.",
        "phase_transition": "Thank you {name} — that's very helpful. I will now ask a few technical questions based on your stack.",
        "invalid_email": "That doesn't look like a valid email address. Please enter it in the format name@example.com.",
        "invalid_phone": "That doesn't look like a valid phone number. Please enter digits only or include country code, e.g. +1-555-123-4567.",
    },
    "Hindi": {
        "greeting": "नमस्ते! मैं TalentScout हूँ, आपका भर्ती सहायक। आपसे मिलकर खुशी हुई। शुरुआत से पहले एक बात: आपकी प्रतिक्रियाएं गोपनीय हैं और केवल भूमिका के लिए फिट मूल्यांकन के लिए उपयोग की जाती हैं। कृपया मुझे अपना {field} बताएं?",
        "thanks_brief": "धन्यवाद {name} — क्या आप अपना {field} प्रदान कर सकते हैं?",
        "thanks_sensitive": "धन्यवाद {name} — आपकी प्राथमिकताओं के अनुसार साक्षात्कार तैयार करने के लिए, क्या आप अपना {field} दे सकते हैं? मैं इस जानकारी को गोपनीय रखता हूँ और केवल इस मूल्यांकन के लिए उपयोग करता हूँ।",
        "phase_transition": "धन्यवाद {name} — यह बहुत मददगार है। अब मैं आपके स्टैक के आधार पर कुछ तकनीकी प्रश्न पूछूंगा।",
        "invalid_email": "यह एक मान्य ईमेल पता नहीं लगता है। कृपया इसे name@example.com प्रारूप में दर्ज करें।",
        "invalid_phone": "यह एक मान्य फोन नंबर नहीं लगता है। कृपया केवल अंकों या देश कोड के साथ दर्ज करें, उदा. +1-555-123-4567।",
    },
    "Spanish": {
        "greeting": "¡Hola! Soy TalentScout, tu asistente de contratación. Me da gusto conocerte. Antes de comenzar, una nota: tus respuestas son confidenciales y se utilizan solo para evaluar tu compatibilidad con el puesto. ¿Podrías decirme tu {field}?",
        "thanks_brief": "Gracias {name} — ¿Podrías proporcionar tu {field}?",
        "thanks_sensitive": "Gracias {name} — para personalizar la entrevista y evaluación, ¿podrías proporcionar tu {field}? Trato tu información de forma confidencial y solo la utilizo para esta evaluación.",
        "phase_transition": "Gracias {name} — eso es muy útil. Ahora te haré algunas preguntas técnicas basadas en tu stack.",
        "invalid_email": "Eso no parece una dirección de correo válida. Por favor, ingrésala en el formato nombre@ejemplo.com.",
        "invalid_phone": "Eso no parece un número de teléfono válido. Por favor, ingresa solo dígitos o incluye el código de país, p. ej. +1-555-123-4567.",
    },
    "French": {
        "greeting": "Bonjour ! Je suis TalentScout, votre assistant de recrutement. Enchanté de vous rencontrer. Avant de commencer, une note : vos réponses sont confidentielles et utilisées uniquement pour évaluer votre adéquation au poste. Pouvez-vous me dire votre {field} ?",
        "thanks_brief": "Merci {name} — pourriez-vous fournir votre {field} ?",
        "thanks_sensitive": "Merci {name} — pour adapter l'entretien et l'évaluation à vous, pourriez-vous fournir votre {field} ? Je traite ces informations de manière confidentielle et ne les utilise que pour cette évaluation.",
        "phase_transition": "Merci {name} — c'est très utile. Je vais maintenant vous poser quelques questions techniques basées sur votre stack.",
        "invalid_email": "Cela ne semble pas être une adresse e-mail valide. Veuillez l'entrer au format nom@exemple.com.",
        "invalid_phone": "Cela ne semble pas être un numéro de téléphone valide. Veuillez entrer uniquement des chiffres ou inclure l'indicatif du pays, par ex. +1-555-123-4567.",
    },
    "German": {
        "greeting": "Hallo! Ich bin TalentScout, Ihr Einstellungsassistent. Freut mich, Sie kennenzulernen. Bevor wir beginnen, ein wichtiger Hinweis: Ihre Antworten sind vertraulich und werden nur zur Bewertung Ihrer Eignung für die Stelle verwendet. Könnten Sie mir Ihren {field} mitteilen?",
        "thanks_brief": "Danke {name} — könnten Sie Ihren {field} angeben?",
        "thanks_sensitive": "Danke {name} — um das Interview und die Bewertung auf Sie abzustimmen, könnten Sie Ihren {field} angeben? Ich behandle diese Informationen vertraulich und nutze sie nur für diese Bewertung.",
        "phase_transition": "Danke {name} — das ist sehr hilfreich. Ich werde Ihnen nun einige technische Fragen basierend auf Ihrem Stack stellen.",
        "invalid_email": "Das sieht nicht wie eine gültige E-Mail-Adresse aus. Bitte geben Sie sie im Format name@beispiel.com ein.",
        "invalid_phone": "Das sieht nicht wie eine gültige Telefonnummer aus. Bitte geben Sie nur Ziffern ein oder fügen Sie die Ländervorwahl hinzu, z. B. +1-555-123-4567.",
    },
    "Hinglish": {
        "greeting": "Hii! Main TalentScout hoon, aapka hiring assistant. Aapse milke bahut khushi hui! Shuru karne se pehle ek baat - aapke answers bilkul confidential hain aur sirf role ke liye aapka fit check karne ke liye use honge. Kya aap mujhe apna {field} bata sakte ho?",
        "thanks_brief": "Thanks {name} — aap apna {field} de sakte ho?",
        "thanks_sensitive": "Shukriya {name} — aapke liye interview ko tailor karne ke liye, aap apna {field} share kar sakte ho? Main aapki information ko confidential rakhta hoon aur sirf is assessment ke liye use karta hoon.",
        "phase_transition": "Shukriya {name} — ye bahut helpful tha! Ab main aapke stack ke based pe kuch technical questions puchta hoon.",
        "invalid_email": "Ye valid email address nahi lag raha. Kya aap ise name@example.com format mein daalenge?",
        "invalid_phone": "Ye valid phone number nahi lag raha. Kya aap country code ke saath digits daal sakte ho? Jaise +1-555-123-4567?",
    },
}


def get_translation(lang: str, key: str, field: str = "", name: str = "") -> str:
    """Get translation for a key in the given language. Fallback to English if not found."""
    if lang not in TRANSLATIONS:
        lang = "English"
    message = TRANSLATIONS[lang].get(key, TRANSLATIONS["English"][key])
    # Format with field and/or name; strip extra spaces if name is empty
    formatted = message.format(field=field, name=f"{name}" if name else "")
    return formatted.strip()


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
    return hinglish_word_count >= len(words) * 0.3  # 30% Hinglish words threshold


# --- HEADER ---
c1, c2, c3 = st.columns([1, 8, 1])
with c2:
    st.markdown('<div class="main-header">TalentScout AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">High-Performance • Multilingual • Sentiment-Aware</div>', unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.markdown("### ⚡ Performance Mode")
    
    # Language Selector
    language_options = {"English": "🇺🇸", "Hindi": "🇮🇳", "Spanish": "🇪🇸", "French": "🇫🇷", "German": "🇩🇪"}
    selected_lang = st.selectbox("Language", list(language_options.keys()), format_func=lambda x: f"{language_options[x]} {x}")
    
    st.divider()
    
    # Controls
    if st.button("🔄 Start New Interview", use_container_width=True):
        st.session_state.messages = []
        if "last_report" in st.session_state:
            del st.session_state.last_report
        st.rerun()

# --- SYSTEM PROMPT ---
system_prompt = f"""
You are 'TalentScout', an AI recruiter.
CURRENT LANGUAGE: {selected_lang} (Speak ONLY in {selected_lang}, unless user speaks English).

PROTOCOL:
1. **Greeting**: Brief & professional.
2. **Info Gathering**: Ask ONE BY ONE: Name, Email, Experience, Position, Tech Stack.
3. **Logic**:
   - Exp < 2y: Ask basics.
   - Exp > 5y: Ask architecture/advanced.
4. **Tech Round**: Ask 3-4 short, sharp technical questions based on stack.
5. **End**: If user says "exit" or "done", conclude.

KEEP RESPONSES CONCISE (Max 2-3 sentences) to ensure speed.
"""
# Ensure the session's system prompt always matches the selected language
if "messages" not in st.session_state or not st.session_state.messages:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
else:
    # update existing system message when language selection changes
    if st.session_state.messages[0].get("role") == "system" and st.session_state.messages[0].get("content") != system_prompt:
        st.session_state.messages[0]["content"] = system_prompt

# Initialize interview collection state
if "phase" not in st.session_state:
    st.session_state.phase = "gathering_info"  # gathering_info -> technical_interview
if "required_fields" not in st.session_state:
    st.session_state.required_fields = [
        "Full Name",
        "Email Address",
        "Phone Number",
        "Years of Experience",
        "Desired Position(s)",
        "Current Location",
        "Tech Stack",
    ]
if "info_index" not in st.session_state:
    st.session_state.info_index = 0
if "collected_info" not in st.session_state:
    st.session_state.collected_info = {}

# (No automatic first prompt so assistant can respond to user's initial greeting)

# --- MAIN CHAT LOOP ---
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] != "system":
            avatar = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

if prompt := st.chat_input("Type your response..."):
    # 1. User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Either handle info-gathering locally, or call the model for technical Q/A
    # If we're still gathering basic info, collect answers locally and prompt next field
    if st.session_state.phase == "gathering_info":
        idx = st.session_state.info_index
        fields = st.session_state.required_fields
        # Save user's answer for the current field — but ignore casual greetings at start
        current_field = fields[idx] if idx < len(fields) else None
        normalized = prompt.strip().lower()
        
        # Auto-detect Hinglish from user input
        detected_hinglish = detect_hinglish(prompt)
        lang_to_use = "Hinglish" if detected_hinglish else selected_lang
        
        if idx == 0 and normalized in GREETINGS:
            # User said 'hi' — respond with a friendly, reassuring greeting then ask for Full Name
            assistant_text = get_translation(lang_to_use, "greeting", current_field)
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(assistant_text)
        else:
            invalid = False
            # Allow skipping Full Name with "skip" or "next"
            skip_keywords = {"skip", "next", "continue", "proceed"}
            if current_field == "Full Name" and normalized in skip_keywords:
                # Skip name but advance to next field
                st.session_state.info_index = idx + 1
                if st.session_state.info_index < len(fields):
                    next_field = fields[st.session_state.info_index]
                    # Get the user's name from collected info if available
                    user_name = st.session_state.collected_info.get("Full Name", "")
                    if next_field in SENSITIVE_FIELDS:
                        assistant_text = get_translation(lang_to_use, "thanks_sensitive", next_field, user_name)
                    else:
                        assistant_text = get_translation(lang_to_use, "thanks_brief", next_field, user_name)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(assistant_text)
            else:
                # Validate sensitive fields before storing
                if current_field == "Email Address":
                    if not is_valid_email(prompt):
                        invalid = True
                        assistant_text = get_translation(lang_to_use, "invalid_email")
                        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(assistant_text)
                elif current_field == "Phone Number":
                    if not is_valid_phone(prompt):
                        invalid = True
                        assistant_text = get_translation(lang_to_use, "invalid_phone")
                        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(assistant_text)

                # If valid (or not a sensitive field), store and advance
                if not invalid:
                    if current_field:
                        st.session_state.collected_info[current_field] = prompt.strip()
                    # Advance to next field
                    st.session_state.info_index = idx + 1

                    # If there are more fields, ask next one
                    if st.session_state.info_index < len(fields):
                        next_field = fields[st.session_state.info_index]
                        # Get the user's name from collected info if available
                        user_name = st.session_state.collected_info.get("Full Name", "")
                        # Only add explicit confidentiality language for sensitive fields,
                        # otherwise keep the prompt concise and natural.
                        if next_field in SENSITIVE_FIELDS:
                            assistant_text = get_translation(lang_to_use, "thanks_sensitive", next_field, user_name)
                        else:
                            assistant_text = get_translation(lang_to_use, "thanks_brief", next_field, user_name)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(assistant_text)
                    else:
                        # All info collected -> switch phase
                        st.session_state.phase = "technical_interview"
                        user_name = st.session_state.collected_info.get("Full Name", "")
                        assistant_text = get_translation(lang_to_use, "phase_transition", name=user_name)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(assistant_text)
        # Do not call the model while gathering info
    else:
        with st.chat_message("assistant", avatar="🤖"):
            try:
                # We use the FAST_MODEL for instant feedback
                stream = client.chat.completions.create(
                    model=FAST_MODEL, 
                    messages=st.session_state.messages,
                    stream=True,
                    temperature=0.6,
                    max_tokens=250 # Limit output tokens for faster return
                )
                
                # Manually stream chunks so we can sanitize code fences as they arrive
                container = st.empty()
                full_text = ""
                try:
                    for chunk in stream:
                        # chunk may provide the content in choices[0].delta.content
                        try:
                            part = chunk.choices[0].delta.content or ""
                        except Exception:
                            part = str(chunk)
                        # Remove any code fences that would render as code blocks
                        part_clean = re.sub(r"```(?:json)?\n?", "", part)
                        part_clean = part_clean.replace('```', '')
                        full_text += part_clean
                        container.markdown(full_text)
                except Exception:
                    # Fallback: attempt to render with write_stream if manual iteration fails
                    raw_response = st.write_stream(stream)
                    full_text = raw_response or full_text

                cleaned = clean_response_text(full_text)
                st.session_state.messages.append({"role": "assistant", "content": cleaned})
                
            except Exception as e:
                st.error(f"Error: {e}")

# --- REPORT GENERATION (Optimized for Quality) ---
with st.sidebar:
    st.divider()
    st.markdown("### 📊 Evaluation")
    
    if st.button("📝 Generate Report", type="primary", use_container_width=True):
        if len(st.session_state.messages) < 6:
            st.toast("⚠️ Chat more to get a report!", icon="⚠️")
        else:
            with st.spinner("🧠 Analyzing profile with High-Reasoning Model..."):
                # Analysis Prompt
                analysis_prompt = st.session_state.messages + [{
                    "role": "user", 
                    "content": f"""
                    Generate JSON evaluation ({selected_lang} context).
                    Fields: name, position, tech_stack, technical_score (0-100), communication_score (0-100), 
                    sentiment_mood (1 word), strengths (list), improvement_areas (list), verdict ("Hire"/"No Hire"/"Maybe").
                    Return ONLY JSON.
                    """
                }]
                
                try:
                    # We switch to SMART_MODEL for the complex analysis task
                    completion = client.chat.completions.create(
                        model=SMART_MODEL,
                        messages=analysis_prompt,
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    
                    data = json.loads(completion.choices[0].message.content)
                    st.session_state.last_report = data
                    st.toast("Report Ready!", icon="✅")
                    
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

# --- DASHBOARD ---
if "last_report" in st.session_state:
    data = st.session_state.last_report
    st.markdown("---")
    st.subheader(f"📋 {data.get('name', 'Candidate')}")
    
    c1, c2, c3, c4 = st.columns(4)
    tech = data.get('technical_score')
    comm = data.get('communication_score')
    # Display as X/100 (handle missing values)
    c1.metric("Tech Score", f"{tech if tech is not None else 'N/A'}/100")
    c2.metric("Comm. Score", f"{comm if comm is not None else 'N/A'}/100")
    c3.metric("Mood", data.get('sentiment_mood'))

    # Overall score: average of available numeric scores (normalized to /100)
    numeric_scores = [s for s in (tech, comm) if isinstance(s, (int, float))]
    if numeric_scores:
        overall = round(sum(numeric_scores) / len(numeric_scores))
        c4.metric("Overall Score", f"{overall}/100")
        # Graphical progress bar (0-100)
        st.progress(int(overall))
        # Optionally show a colored badge for rating
        if overall >= 75:
            st.success(f"Performance: {overall}/100 — Strong")
        elif overall >= 50:
            st.info(f"Performance: {overall}/100 — Average")
        else:
            st.warning(f"Performance: {overall}/100 — Needs Improvement")
    else:
        c4.metric("Overall Score", "N/A")

    # Verdict displayed below metrics
    verdict = data.get('verdict', 'N/A')
    color = "green" if "Hire" in verdict else "red"
    st.markdown(f"**Verdict:** <span style='color:{color};font-weight:700'>{verdict}</span>", unsafe_allow_html=True)
    
    with st.expander("🔍 Detailed Analysis"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Strengths**")
            for s in data.get('strengths', []): st.write(f"• {s}")
        with c2:
            st.markdown("**Improvements**")
            for i in data.get('improvement_areas', []): st.write(f"• {i}")
            
    # Download
    st.download_button("📥 Download JSON", json.dumps(data, indent=2), "report.json", "application/json", type="secondary")