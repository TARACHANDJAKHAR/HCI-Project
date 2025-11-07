# Elderly Care Voice Assistant - Quick Summary

## What is This Project?

An **intelligent voice assistant** designed specifically for elderly users to help with:
- Daily reminders (medications, appointments)
- Emergency alerts (SOS via SMS)
- Information queries (time, weather, news)
- Health & wellness support
- Entertainment (jokes, stories)
- Natural conversation

---

## How It Works (Simple Explanation)

### User Interaction Flow:
1. **User speaks** → "set reminder for medicine at 3pm"
2. **Frontend** captures voice using Web Speech API
3. **Backend** receives command and routes it to appropriate processor
4. **Reminder Processor** parses time, saves reminder
5. **Response** sent back → "Reminder set for 3:00 PM: medicine"
6. **Frontend** displays and speaks the response

### Reminder Notification Flow:
1. **Background scheduler** checks reminders every 10 seconds
2. When reminder time arrives → notification triggered
3. **Frontend** polls for notifications every 5 seconds
4. Notification displayed and spoken to user

---

## Project Structure (3 Main Parts)

### 1. **Backend (Python/Flask)**
- **app.py**: Main server, handles HTTP requests
- **Command_Processor.py**: Routes commands to specialized processors
- **Storage_Manager.py**: Saves data (reminders, contacts) to JSON file
- **Processors**: Specialized handlers for different command types
  - Info (time, weather, news)
  - Reminders (set, list, delete)
  - Emergency (SOS alerts)
  - Health (exercise, motivation)
  - Entertainment (jokes, stories)
- **LLM_Responder.py**: Handles general conversation using AI

### 2. **Frontend (React)**
- **App.js**: Complete web interface
- Voice input (microphone)
- Text-to-speech output
- Chat interface
- Reminder/contact management UI
- News display

### 3. **Storage (JSON File)**
- `assistant_data.json`: Stores all data
  - Reminders (regular + scheduled)
  - Emergency contacts
  - User profile

---

## Key Features

### ✅ Voice Recognition
- Uses Web Speech API (browser-based)
- Supports Indian English
- Converts speech to text

### ✅ Text-to-Speech
- Speaks responses to user
- Clear, slow-paced speech

### ✅ Smart Command Processing
- Keyword-based routing to specialized processors
- Natural language understanding for reminders
- Falls back to AI (LLM) for general conversation

### ✅ Scheduled Reminders
- Set reminders with specific times
- Background scheduler checks every 10 seconds
- Notifications triggered automatically

### ✅ Emergency Assistance
- "Emergency" or "SOS" command
- Sends SMS to all emergency contacts (via Twilio)
- Works even if Twilio not configured (graceful degradation)

### ✅ Information Queries
- Current time and date
- Weather (using Open-Meteo API - free)
- News headlines (using NewsAPI - requires key)

### ✅ AI-Powered Conversation
- Uses Hugging Face models (local, free) or OpenAI (cloud, paid)
- Maintains conversation context
- Personalized based on user profile

---

## Technologies Used

**Backend:**
- Flask (web framework)
- SpeechRecognition (voice input)
- Twilio (SMS)
- Transformers/OpenAI (AI)
- Requests (API calls)

**Frontend:**
- React (UI framework)
- Web Speech API (voice)
- Tailwind CSS (styling)

**Storage:**
- JSON file (simple, no database needed)

---

## How to Run

### Backend:
```bash
python app.py
```
Runs on `http://localhost:5000`

### Frontend:
```bash
cd frontend
npm install
npm start
```
Runs on `http://localhost:3000`

---

## Design Highlights

1. **Modular Architecture**: Each feature in separate processor
2. **Error Handling**: Graceful degradation when APIs unavailable
3. **Real-time Updates**: Background scheduler for notifications
4. **User-Friendly**: Voice + text input, clear UI
5. **Extensible**: Easy to add new processors or features

---

## Example Commands

- "what time is it" → Current time
- "set reminder for medicine at 3pm" → Creates scheduled reminder
- "list reminders" → Shows all reminders
- "what's the weather" → Current weather
- "tell me a joke" → Random joke
- "emergency" → Sends SOS SMS
- "how are you" → AI conversation

---

## Data Storage

All data stored in `assistant_data.json`:
```json
{
  "reminders": [],
  "emergency_contacts": [
    {"name": "John", "phone": "+1234567890"}
  ],
  "scheduled_reminders": [
    {
      "id": "abc123",
      "text": "medicine",
      "time": "2024-01-15 15:00",
      "completed": false
    }
  ],
  "profile": {
    "name": "User",
    "preferences": {}
  }
}
```

---

## Key Files Explained

| File | Purpose |
|------|---------|
| `app.py` | Main server, API endpoints |
| `Command_Processor.py` | Routes commands to processors |
| `Storage_Manager.py` | Saves/loads data from JSON |
| `processors/*.py` | Specialized command handlers |
| `Notification_Scheduler.py` | Background reminder checker |
| `LLM_Responder.py` | AI conversation handler |
| `frontend/src/App.js` | React UI component |

---

## Summary

This is a **complete voice assistant system** with:
- ✅ Voice input/output
- ✅ Smart command processing
- ✅ Scheduled reminders with notifications
- ✅ Emergency assistance
- ✅ Information queries
- ✅ AI-powered conversation
- ✅ Modern web interface

**Perfect for elderly users** who need help with daily tasks, reminders, and companionship.

