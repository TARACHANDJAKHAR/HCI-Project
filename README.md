# Elderly Voice Assistant

## Backend (Flask)

### Setup
1. Create and activate venv
```bash
python3 -m venv .venv && source .venv/bin/activate
```
2. Install deps
```bash
pip install -r requirements.txt
```
3. Env vars (optional but recommended)
```bash
# News API (https://newsapi.org)
export NEWS_API_KEY=your_key
# Twilio (https://twilio.com)
export TWILIO_ACCOUNT_SID=AC...
export TWILIO_AUTH_TOKEN=...
export TWILIO_FROM_PHONE=+1...
# LLM model (defaults to gpt2). Examples:
# export LLM_MODEL=distilgpt2
# export LLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
export LLM_MODEL=gpt2
# Use OpenAI (GPT-4 class models) instead of local HF:
# export LLM_PROVIDER=openai
# export OPENAI_API_KEY=sk-...
# export LLM_MODEL=gpt-4o-mini  # or gpt-4o, o3-mini, etc.
```
4. Run
```bash
python app.py
```

## Frontend (React)
```bash
cd frontend
npm install
npm start
```
Frontend expects backend at http://localhost:5000.

## Notes
- If Twilio vars are missing, Emergency SMS is disabled gracefully.
- If NEWS_API_KEY is missing, news feature informs the user.
- LLM model loads on first use; if loading fails, a safe fallback response is used.

