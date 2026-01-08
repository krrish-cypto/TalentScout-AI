🤖 TalentScout AI - Intelligent Hiring Assistant

📌 Project Overview

TalentScout AI is a high-performance recruitment chatbot designed to automate the screening process for technical candidates. Built with Streamlit and Groq (LLaMA-3), it features a hybrid-model architecture to ensure instant responses while delivering deep analytical insights.

🚀 Key Features (Milestones Achieved)

Hybrid AI Architecture: * Chat Loop: Uses Llama-3.1-8b-Instant for ultra-low latency (<300ms) conversation.

Analysis Core: Uses Llama-3.3-70b-Versatile for generating complex candidate dossiers.

Multilingual Support: Conducts interviews in English, Hindi, Spanish, French, German, and Hinglish.

State-Driven Logic: Ensures all critical fields (Name, Email, Tech Stack) are gathered before the technical round begins.

Sentiment & Behavioral Analysis: Generates a JSON evaluation report assessing the candidate's confidence and technical depth.

🛠️ Installation & Setup

Clone the Repository

git clone <your-repo-link-here>
cd TalentScout-AI


Install Dependencies

pip install -r requirements.txt


Configure API Key
Create a file named .env in the root directory and add your Groq API key:

GROQ_API_KEY=gsk_yoursupersecretkey...


Run the Application

streamlit run app.py


🧠 Prompt Engineering Strategy

The chatbot uses a Role-Playing System Prompt with strict constraints:

Conciseness: The prompt restricts responses to 2-3 sentences to keep the chat fast.

Context Management: st.session_state is used to maintain conversation history, ensuring the AI remembers the candidate's name and tech stack throughout the session.

Security: Prompt injection protection is managed by validating inputs (e.g., email regex) before passing them to the model.

📁 Project Structure

app.py: Main application logic and UI.

requirements.txt: Python dependencies.

.env: Configuration for API keys (not included in repo).

Submitted for the AI/ML Intern Assignment.
