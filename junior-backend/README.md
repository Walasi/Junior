# 🌸 Junior – Your Always-There Friend

**Junior** is an AI companion designed to help you navigate life’s challenges with empathy, psychological depth, and practical guidance. Inspired by the movie *Ron’s Gone Wrong*, Junior is more than a chatbot – it’s a trusted friend who listens, remembers, and grows with you.

## ✨ Features

- **Onboarding** – gets to know you before chatting.
- **Fear Reframing** – gently shifts anxious thoughts.
- **Triad Thinking** – connects thoughts, emotions, and behaviours.
- **Age Group Adaptation** – tone and advice match your life stage.
- **Complaint Tracking** – notices repetitive negativity and redirects to solutions.
- **Web Search** – real‑time factual answers via Tavily.
- **7‑Why Game** – uncovers your core motivations.
- **Memory Moments** – captures and recalls achievements.
- **Humor Detection** – shares a playful laugh when you say something naive.
- **Self‑Validation** – encourages you to trust your own judgment.
- **Dark / Light Mode** – comfortable for any time of day.

## 🛠 Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **Database**: SQLite (via SQLAlchemy)
- **LLM**: OpenRouter (Qwen‑VL‑235B)
- **Search**: Tavily API
- **Sentiment**: TextBlob
- **Embeddings**: Sentence‑Transformers

## 🚀 Run Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload