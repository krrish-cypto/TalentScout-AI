# TalentScout AI

> **High-Performance • Multilingual • Resume Parsing • PDF Reports**

An intelligent AI-powered recruiting chatbot built with **Streamlit** and **Groq LLMs** for seamless candidate screening and evaluation.

## 📖 Project Overview

**TalentScout AI** is a next-generation hiring assistant designed to automate the initial screening phase of recruitment. The chatbot conducts natural, multi-language conversations to gather candidate information, validates data against uploaded resumes, assesses technical skills through dynamic questioning, and generates structured evaluation reports in both JSON and PDF formats.

### Key Capabilities

- **Resume Parsing**: Auto-extracts candidate details from PDF/DOCX/TXT files to streamline data collection.
- **Intelligent Inquiry Handling**: Distinguishes between candidate answers and questions (e.g., handles "Why do you need this?" professionally).
- **Adaptive Questioning**: Tapers technical questions based on experience level and tech stack.
- **Multilingual Excellence**: Seamless support for 6+ languages with auto-detection.
- **PDF & JSON Reports**: Generates professional PDF decrees with Radar Charts and performance summaries.
- **Professional UI**: Clean, responsive interface with smooth animations and polished aesthetics.

## 🚀 Features

- **Smart Resume Parser**: Reads PDF/DOCX files to pre-fill information (Name, Email, Stack) but verifies critical fields like "Desired Position".
- **Multi-Phase Interview**: Resume Analysis → Info Verification → Technical Questioning.
- **Dual Model Strategy**: 
    - Fast model (llama-3.1-8b-instant) for chat speed, input processing, and validation.
    - Smart model (llama-3.3-70b-versatile) for resume parsing and final candidate analysis.
- **Intelligent Input Processor**: Detects if a user is providing an answer or asking a clarifying question, ensuring a natural dialogue flow.
- **Visual Analytics**: Generates a **Radar Chart** (Spider Graph) visualizing candidate competencies across 4 axes.
- **Multilingual Support**: English, Hindi, Spanish, French, German, Hinglish.
- **Auto-Detection**: Hinglish language recognition with seamless code-switching.
- **Session Caching**: Optimized performance with Streamlit's `@st.cache_resource`.

## 📋 Interview Flow

1. **Resume Upload** → User uploads a CV; AI extracts key details (Name, Contact, Stack) to skip redundant questions.
2. **Greeting & Verification** → Professional introduction; AI verifies missing info and explicitly asks for "Desired Position" to ensure intent accuracy.
3. **Smart Interaction** → If user asks "Why do you need my phone number?", AI explains the reason before proceeding.
4. **Technical Round** → 3-4 dynamic questions based on the candidate's specific Tech Stack.
5. **Report Generation** → Generates a detailed JSON file and a visual PDF Report with a verdict.

---

## 📖 Usage Guide

### Starting an Interview

1. **Launch the app** and select your preferred language from the sidebar.
2. **Upload Resume** (Optional) via the sidebar to auto-fill details.
3. **Greet the assistant** or answer the initial verification questions.
4. **Interact naturally**:
   - Answer questions.
   - Ask clarifying questions (e.g., "Why is this needed?").
   - Type "skip" if you wish to bypass a non-mandatory field.
5. **Generate Report** by clicking "📝 Generate Report" in the sidebar.

### Key Interactions

- **Upload Resume**: Supports `.pdf`, `.docx`, `.txt`.
- **Clarification**: Ask the bot questions; it will answer and then gently guide you back to the interview.
- **Download**: Get a structured **JSON** file or a professional **PDF** with charts.

### Example Conversation Flow

User uploads resume... Bot: Hello! I'm TalentScout. I've reviewed your resume. Welcome, John. I need to clarify a few details. Could you please tell me your Desired Position? You: Senior Backend Engineer

Bot: Thanks John. I see you use Python and Django. Let's dive into the technical round. Explain how you handle database migrations in a production environment? You: [Answer]

Bot: [Generates evaluation with Radar Chart and PDF download]


---

## 🛠️ Technical Details

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Frontend** | Streamlit | 1.28+ | Web UI & real-time interactions |
| **LLM Provider** | Groq | 0.4+ | Fast API access to Llama models |
| **Parsing** | PyPDF2, python-docx | Latest | Extract text from uploaded resumes |
| **Reporting** | FPDF, Matplotlib | Latest | Generate PDF reports and Radar Charts |
| **Environment** | Python-dotenv | 1.0+ | Secure API key management |

### AI Models

1. **Fast Model**: `llama-3.1-8b-instant`
   - Use Case: Chat loop, input classification (Answer vs. Question), regex validation.
   - Response Time: <500ms.
   - Temperature: 0.6 (balanced creativity).

2. **Smart Model**: `llama-3.3-70b-versatile`
   - Use Case: Resume Parsing, Final Analysis, JSON Report Generation.
   - Response Time: 1-3s.
   - Response Format: JSON-only for structured output.

### Architecture

┌───────────────────────────────────────────────────┐
│              Streamlit Frontend UI                │
│       (Sidebar, Chat Interface, File Uploader)    │
└────────────────────────┬──────────────────────────┘
                         │
           ┌─────────────▼─────────────┐
           │      Resume Parsing       │
           │   (PyPDF2 / python-docx)  │
           └─────────────┬─────────────┘
                         │
                  ┌──────▼──────┐
                  │ Intelligent │
                  │ Input Logic │◄─── Checks: Is it an answer
                  └──────┬──────┘       or a clarification?
                         │
        ┌────────────────▼────────────────┐
        │     Groq API (Hybrid Models)    │
        ├────────────────┬────────────────┤
        │  Fast Model    │  Smart Model   │
        │ (Chat/Intent)  │ (Parse/Report) │
        └───────┬────────┴───────┬────────┘
                │                │
┌───────────────▼────────────────▼────────────────┐
│            Report Generation Engine             │
│   • Matplotlib (Radar Charts for Skills)        │
│   • FPDF (PDF Document Creation)                │
└─────────────────────────────────────────────────┘

## 💡 Prompt Design

### Core Strategy

The prompt engineering approach now includes **Contextual Intent Detection** and **Strict JSON Parsing** for resumes.

### 1. Intelligent Input Processor

Before accepting user input as an answer, the system evaluates intent:

TASK:
1. If user answers, extract value. Set "is_answer": true.
2. If user asks (Why?), explain reason. Set "is_answer": false.
3. If "skip", value: "Skipped".
This prevents the bot from blindly saving "Why do you need this?" as a user's phone number.

2. Resume Parsing Strategy
The Resume Parser is instructed to ignore specific fields to force verification:

"Extract keys: Name, Email, Stack...
IMPORTANT: DO NOT extract 'Desired Position'. We will ask the user for this."
This ensures the candidate confirms the specific role they are applying for, rather than the bot guessing from a generic resume summary.

3. PDF & Graph Generation
Visuals: A Radar Chart is generated using matplotlib to visualize Technical vs. Communication vs. Experience scores on a 0-100 scale.

Summary: The AI generates a 1-sentence "Graph Interpretation" summary included in the PDF to explain the metrics to human recruiters.

🎨 UI/UX Features
Professional Theme: Clean gradient backgrounds (#f8f9fa to #eef2f3) for a modern corporate look.

Sidebar Controls: Integrated Resume Uploader and Language Selector.

Dynamic Feedback: Toast notifications ("Report Ready!", "Resume Parsed!") for system status.

Responsive Charts: Radar charts that simplify complex scoring into visual polygons.

Error Handling: Graceful handling of invalid file types or API timeouts.

🛠️ Setup
Prerequisites
Python 3.8+

Groq API Key

Libraries: streamlit, groq, python-dotenv, PyPDF2, python-docx, fpdf, matplotlib

Installation Instructions
Step 1: Clone the repository

Bash

git clone [https://github.com/yourusername/TalentScout_Chatbot.git](https://github.com/yourusername/TalentScout_Chatbot.git)
cd TalentScout_Chatbot
Step 2: Install dependencies

Bash

pip install -r requirements.txt
Step 3: Configure API Key Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here
Step 4: Run the application

Bash

streamlit run app.py
📊 Report Metrics
Radar Chart: Visualizes balance between Tech, Comm, Problem Solving, and Fit.

Technical Score: 0-100 (coding skills, stack depth).

Communication Score: 0-100 (clarity, articulation).

Verdict: Hire / No Hire / Maybe.

Graph Summary: AI-generated insight explaining the scores.

Report Output Example (PDF)
Header: Candidate Name & Position

Body: Detailed Tech Stack (text-wrapped)

Visual: Blue Polygon Radar Chart

Analysis: Strengths, Improvements, and Hiring Verdict

🧠 Challenges & Solutions
Challenge 1: Resume "Blindness" regarding Intent
Problem: Resumes list history, not necessarily the next role the candidate wants. Solution: The parser explicitly excludes "Desired Position," forcing the chatbot to ask, "Which position are you applying for?" This ensures the interview context is accurate.

Challenge 2: PDF Text Overflow
Problem: Long Tech Stacks (e.g., "Python, Java, React, Docker, Kubernetes...") would cut off the page in standard PDF generation. Solution: Switched from cell() to multi_cell() in FPDF, allowing dynamic text wrapping and automatic line breaks for content-heavy sections.

Challenge 3: Handling User Curiosity
Problem: Users asking "Why do you need my phone number?" were previously ignored or treated as providing invalid data. Solution: Implemented an intermediate LLM check (process_user_input) that classifies the user's message. If it's a question, the bot answers it without advancing the interview stage.

👤 Author
TalentScout AI Development Team

Github: github.com/talentscout-ai

📄 License
This project is licensed under the MIT License.