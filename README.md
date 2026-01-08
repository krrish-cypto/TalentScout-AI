# TalentScout AI

> **High-Performance • Multilingual • Sentiment-Aware**

An intelligent AI-powered recruiting chatbot built with **Streamlit** and **Groq LLMs** for seamless candidate screening and evaluation.

## 🚀 Features

- **Multi-Phase Interview**: Automated info gathering → technical questioning
- **Multilingual Support**: English, Hindi, Spanish, French, German, Hinglish
- **Smart Validation**: Email and phone number verification
- **Dual Model Strategy**: 
    - Fast model (llama-3.1-8b) for chat speed
    - Smart model (llama-3.3-70b) for detailed analysis
- **Auto-Detection**: Hinglish language recognition
- **JSON Reports**: Structured candidate evaluation with scores and verdicts
- **Session Caching**: Optimized performance with Streamlit's `@st.cache_resource`

## 📋 Interview Flow

1. **Greeting** → Professional introduction
2. **Info Gathering** → Name, Email, Phone, Experience, Position, Location, Tech Stack
3. **Technical Round** → 3-4 dynamic questions based on candidate's stack
4. **Report Generation** → Automated evaluation with hiring recommendation

## 🛠️ Setup

```bash
# Install dependencies
pip install streamlit groq python-dotenv

# Create .env file
echo "GROQ_API_KEY=your_api_key_here" > .env

# Run app
streamlit run app.py
```

## 📊 Report Metrics

- **Technical Score**: 0-100
- **Communication Score**: 0-100
- **Sentiment Mood**: 1-word mood assessment
- **Verdict**: Hire / No Hire / Maybe
- **Strengths & Improvement Areas**: Detailed feedback

## 🌐 Supported Languages

🇺🇸 English | 🇮🇳 Hindi | 🇪🇸 Spanish | 🇫🇷 French | 🇩🇪 German | 🇮🇳 Hinglish

## 📥 Export

Download candidate reports as JSON for integration with your ATS or HR tools.
