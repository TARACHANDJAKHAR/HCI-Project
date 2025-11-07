# Elderly Care Voice Assistant - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Backend Structure](#backend-structure)
4. [Frontend Structure](#frontend-structure)
5. [Data Flow](#data-flow)
6. [Key Components Explained](#key-components-explained)
7. [API Endpoints](#api-endpoints)
8. [Technologies Used](#technologies-used)

---

## Project Overview

This is an **Elderly Care Voice Assistant** designed to help elderly users with:
- **Voice-based interaction** (speech recognition and text-to-speech)
- **Reminder management** (set, list, delete reminders with scheduled notifications)
- **Emergency assistance** (SOS alerts via SMS)
- **Information queries** (time, date, weather, news)
- **Health & wellness** (exercise suggestions, motivation)
- **Entertainment** (jokes, stories, music suggestions)
- **Natural conversation** (using LLM for general chat)

The system consists of:
- **Backend**: Flask REST API server (Python)
- **Frontend**: React web application with voice capabilities
- **Storage**: JSON file-based persistence
- **AI**: LLM integration (Hugging Face or OpenAI) for natural conversation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  - Web Speech API (Voice Input)                             │
│  - Text-to-Speech (Voice Output)                            │
│  - Chat Interface                                            │
│  - Reminder/Contact Management UI                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
                       │ (JSON)
┌──────────────────────▼──────────────────────────────────────┐
│              Backend (Flask Server)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Command Processor (Router)                   │   │
│  │  Routes commands to specialized processors           │   │
│  └──────┬──────────┬──────────┬──────────┬─────────────┘   │
│         │          │          │          │                  │
│  ┌──────▼──┐ ┌─────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌────────┐ │
│  │  Info   │ │Reminder │ │Emergency│ │Health  │ │Entertain│ │
│  │Processor│ │Processor│ │Processor│ │Processor│ │Processor│ │
│  └─────────┘ └─────────┘ └─────────┘ └────────┘ └─────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         LLM Responder (Fallback)                      │   │
│  │  Handles general conversation when no processor       │   │
│  │  matches the command                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      Notification Scheduler (Background Thread)        │   │
│  │  Checks for due reminders every 10 seconds             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Storage Manager (JSON File)                  │   │
│  │  - Reminders                                           │   │
│  │  - Emergency Contacts                                  │   │
│  │  - User Profile                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Backend Structure

### 1. **app.py** - Main Flask Application
**Purpose**: Entry point for the backend server. Handles all HTTP requests and coordinates components.

**Key Responsibilities**:
- Initialize Flask app with CORS support
- Initialize all components (Storage, Command Processor, LLM, Notification Scheduler)
- Define REST API endpoints
- Handle audio processing (speech recognition)
- Manage notification queue for frontend polling

**Key Functions**:
- `process_command()`: Processes text commands from frontend
- `process_audio()`: Converts audio to text, then processes as command
- `get_reminders()`: Returns all reminders (regular + scheduled)
- `get_contacts()`: Returns emergency contacts
- `get_notifications()`: Returns pending notifications (polled by frontend)

**Notification System**:
- Background scheduler checks reminders every 10 seconds
- When reminder time arrives, `notify_user()` callback is triggered
- Notification is added to `pending_notifications` list
- Frontend polls `/api/notifications` every 5 seconds to retrieve them

---

### 2. **Command_Processor.py** - Command Router
**Purpose**: Routes user commands to appropriate specialized processors using Chain-of-Responsibility pattern.

**How It Works**:
1. User sends command (e.g., "what time is it")
2. CommandProcessor iterates through processors in order:
   - InfoProcessor (time, date, weather, news)
   - ReminderProcessor (reminders, meds, appointments)
   - EmergencyProcessor (emergency, SOS)
   - HealthProcessor (exercise, motivation)
   - EntertainmentProcessor (jokes, stories, music)
3. First processor that matches (via keywords) handles the command
4. If no processor matches, returns `None` → LLM handles it

**Key Features**:
- **Keyword Matching**: Each processor has a list of keywords (e.g., `["time", "date", "weather"]`)
- **Response Capture**: Captures all messages from processors to return to API
- **Speaker Function**: Optional TTS function (used in CLI mode, not in web mode)

**Example Flow**:
```
Command: "set reminder for medicine at 3pm"
→ ReminderProcessor.match() returns True (contains "reminder")
→ ReminderProcessor.handle() parses time, saves reminder
→ Returns: "Reminder set for 3:00 PM: medicine"
```

---

### 3. **Storage_Manager.py** - Data Persistence
**Purpose**: Manages all persistent data using JSON file (`assistant_data.json`).

**Data Structure**:
```json
{
  "reminders": [],                    // Simple text reminders (legacy)
  "emergency_contacts": [],           // {name, phone, previous_phone}
  "profile": {},                      // {name, preferences}
  "scheduled_reminders": []           // {id, text, time, completed}
}
```

**Key Methods**:
- `load(key)`: Load data for a key (e.g., "reminders")
- `save(key, value)`: Append value to a list
- `add_contact(name, phone)`: Add emergency contact (prevents duplicates)
- `save_scheduled_reminder(text, time)`: Save reminder with specific time
- `get_scheduled_reminders()`: Get all scheduled reminders
- `mark_reminder_completed(id)`: Mark reminder as notified

**Reminder Types**:
1. **Regular Reminders**: Simple text list (legacy, rarely used)
2. **Scheduled Reminders**: Have specific time, trigger notifications

---

### 4. **processors/Base_Processor.py** - Abstract Base Class
**Purpose**: Template for all specialized processors. Implements common functionality.

**Key Methods**:
- `match(command)`: Checks if any keyword appears in command
- `handle(command)`: Must be implemented by subclasses

**Design Pattern**: Template Method Pattern
- Base class defines structure (match → handle)
- Subclasses provide specific implementations

---

### 5. **processors/Info_Processor.py** - Information Queries
**Purpose**: Handles informational queries that don't require storage.

**Capabilities**:
- **Time**: Current time (HH:MM:SS format)
- **Date**: Current date (e.g., "January 15, 2024")
- **Weather**: Uses Open-Meteo API (free, no API key needed)
  - Geocoding: Converts location name to coordinates
  - Weather API: Fetches current temperature and conditions
  - Weather codes: Maps numeric codes to descriptions (e.g., 0 = "clear sky")
- **News**: Uses NewsAPI (requires `NEWS_API_KEY` env var)
  - Fetches top 5 headlines
  - Formats with numbering and newlines

**Error Handling**: Gracefully handles API failures with user-friendly messages.

---

### 6. **processors/Reminder_Processor.py** - Reminder Management
**Purpose**: Handles all reminder-related commands with natural language parsing.

**Features**:
- **Time Parsing**: Extracts time from natural language
  - Supports: "at 3pm", "at 3:30 pm", "tomorrow at 10am", "15:30"
  - Uses regex patterns to match various formats
  - Converts 12-hour to 24-hour format
  - Handles "tomorrow" keyword
- **Text Extraction**: Removes command phrases to get clean reminder text
  - "set reminder for medicine at 3pm" → "medicine"
- **List Reminders**: Shows all reminders (regular + scheduled) with formatted times
- **Delete Reminders**: Supports "delete all" or "delete reminder 1" (by index)
- **Count Reminders**: "how many reminders" returns total count

**Time Format**: Stores as `"YYYY-MM-DD HH:MM"` (e.g., "2024-01-15 15:00")

**Display Format**: Converts to human-readable:
- Today: "3:00 PM"
- Tomorrow: "Tomorrow at 10:00 AM"
- Future: "January 15 at 3:00 PM"

---

### 7. **processors/Emergency_Processor.py** - Emergency Assistance
**Purpose**: Handles emergency/SOS commands and sends SMS alerts.

**Features**:
- **SMS Sending**: Uses Twilio API to send SMS to all emergency contacts
- **Graceful Degradation**: If Twilio credentials missing, informs user (doesn't crash)
- **Smart Matching**: Only triggers on clear emergency intents (not "help me find X")

**Environment Variables Required**:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_PHONE`

**SMS Message**: "Emergency! I need help"

---

### 8. **processors/Health_Processor.py** - Health & Wellness
**Purpose**: Provides health-related responses.

**Capabilities**:
- Exercise suggestions: "Let's do some light stretching for 5 minutes."
- Motivational messages: "You are strong and doing great! Keep it up."

**Extensibility**: Can be extended with medication tracking, exercise routines, etc.

---

### 9. **processors/Entertainment_Processor.py** - Entertainment
**Purpose**: Provides light entertainment for companionship.

**Content**:
- **Jokes**: Collection of 20+ gentle, appropriate jokes
- **Stories**: 10+ short, uplifting stories
- **Music**: Suggestions for calming music

**Design**: All content is appropriate and gentle for elderly users.

---

### 10. **processors/Notification_Scheduler.py** - Background Scheduler
**Purpose**: Runs in background thread, checks for due reminders every 10 seconds.

**How It Works**:
1. Runs in daemon thread (doesn't block app shutdown)
2. Every 10 seconds:
   - Loads all scheduled reminders
   - Checks if any reminder's time has arrived (within -60 to +10 second window)
   - If due, calls `notify_callback(reminder_text, reminder_id)`
   - Marks reminder as `completed: true`
3. Continues running until app stops

**Time Window**: -60 to +10 seconds (accounts for 10-second check interval)

**Thread Safety**: Uses daemon thread so it doesn't prevent app shutdown.

---

### 11. **ai_modules/LLM_Responder.py** - Natural Language Generation
**Purpose**: Handles general conversation when no specialized processor matches.

**Providers**:
1. **Hugging Face (Local)**: 
   - Models: GPT-2, DistilGPT-2, TinyLlama, etc.
   - Runs on your machine (free, but slower)
   - Requires model download on first use
2. **OpenAI (Cloud)**:
   - Models: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
   - Requires API key (paid, but better quality)
   - Faster and more natural responses

**Configuration**:
- `LLM_PROVIDER`: "hf" or "openai"
- `LLM_MODEL`: Model name (e.g., "gpt2", "gpt-4o-mini")
- `OPENAI_API_KEY`: Required for OpenAI provider

**Features**:
- **Conversation History**: Maintains last 8 messages (4 turns) for context
- **Personalization**: Uses user profile (name, preferences) to customize responses
- **System Persona**: "You are a warm, gentle, and caring elderly companion..."
- **Lazy Loading**: Model only loads when first used (faster startup)
- **Error Handling**: Falls back to safe messages if model fails

**Response Generation**:
- Hugging Face: Tokenizes input → Generates tokens → Decodes to text
- OpenAI: Sends conversation context → Receives response
- Both limit response length (220 tokens) for concise answers

---

### 12. **Elderly_Voice_Assistant.py** - CLI Version
**Purpose**: Standalone terminal version for testing without web interface.

**Features**:
- Microphone input (speech recognition)
- Text-to-speech output (pyttsx3)
- Same command processing as web version

**Use Cases**:
- Testing without browser
- Running on devices without web interface
- Development and debugging

---

## Frontend Structure

### 1. **frontend/src/App.js** - Main React Component
**Purpose**: Complete web interface for the voice assistant.

**Key Features**:

#### State Management:
- `isListening`: Microphone active state
- `messages`: Chat message history
- `contacts`: Emergency contacts list
- `reminders`: Reminders list
- `voiceStatus`: 'idle' | 'listening' | 'processing' | 'speaking'

#### Voice Recognition:
- Uses Web Speech API (`SpeechRecognition` or `webkitSpeechRecognition`)
- Configured for Indian English (`en-IN`)
- Continuous: false (stops after one result)
- Interim results: false (only final results)

#### Text-to-Speech:
- Uses Web Speech Synthesis API
- Rate: 0.9 (slightly slower for clarity)
- Language: `en-IN`
- Cancels previous speech before starting new

#### Notification Polling:
- Polls `/api/notifications` every 5 seconds
- When notification arrives:
  - Displays in chat
  - Speaks the notification
  - Refreshes reminders list
- Refreshes reminders every 30 seconds (every 6th check)

#### UI Components:
- **Header**: Title and "Start Assistant" button
- **Quick Actions**: Buttons for Time, Weather, Reminders, Emergency
- **Chat Interface**: Message display with auto-scroll
- **Reminder Panel**: Collapsible list of reminders
- **Emergency Panel**: Collapsible list of contacts
- **News Panel**: Top headlines with refresh button
- **Floating Mic Button**: Large button for voice input (bottom-right)
- **Status Widgets**: Mood summary and voice status indicators

#### Data Fetching:
- `fetchContacts()`: GET `/api/contacts`
- `fetchReminders()`: GET `/api/reminders`
- `fetchNews()`: POST `/api/process-command` with "what is the news"

#### Command Processing:
- `handleCommand(command)`:
  1. Adds user message to chat
  2. POSTs to `/api/process-command`
  3. Displays response in chat
  4. Speaks the response
  5. Refreshes data if needed

---

## Data Flow

### Example: Setting a Reminder

```
1. User says: "set reminder for medicine at 3pm"
   ↓
2. Frontend: Web Speech API recognizes speech
   ↓
3. Frontend: POST /api/process-command
   {
     "command": "set reminder for medicine at 3pm"
   }
   ↓
4. Backend: CommandProcessor.process("set reminder for medicine at 3pm")
   ↓
5. CommandProcessor: Checks processors in order
   - InfoProcessor.match() → False
   - ReminderProcessor.match() → True (contains "reminder")
   ↓
6. ReminderProcessor.handle():
   - Parses time: "3pm" → "2024-01-15 15:00"
   - Extracts text: "medicine"
   - Calls storage.save_scheduled_reminder("medicine", "2024-01-15 15:00")
   - Returns: "Reminder set for 3:00 PM: medicine"
   ↓
7. Backend: Returns JSON response
   {
     "response": "Reminder set for 3:00 PM: medicine",
     "success": true
   }
   ↓
8. Frontend: Displays response in chat, speaks it, refreshes reminders list
```

### Example: Reminder Notification

```
1. Background: NotificationScheduler checks reminders every 10 seconds
   ↓
2. NotificationScheduler: Finds reminder due at "2024-01-15 15:00"
   Current time: "2024-01-15 15:00:05" (within -60 to +10 window)
   ↓
3. NotificationScheduler: Calls notify_user("medicine", "reminder_id")
   ↓
4. app.py: notify_user() adds to pending_notifications:
   {
     "id": "reminder_id",
     "text": "medicine",
     "message": "Reminder: medicine",
     "timestamp": "2024-01-15T15:00:05"
   }
   ↓
5. NotificationScheduler: Marks reminder as completed
   ↓
6. Frontend: Polls GET /api/notifications (every 5 seconds)
   ↓
7. Backend: Returns pending_notifications, then clears list
   ↓
8. Frontend: Displays notification in chat, speaks it
```

---

## API Endpoints

### POST `/api/process-command`
**Purpose**: Process text command from frontend.

**Request**:
```json
{
  "command": "what time is it"
}
```

**Response**:
```json
{
  "response": "The current time is 14:30:15",
  "success": true
}
```

**Flow**: Routes to appropriate processor or LLM.

---

### POST `/api/process-audio`
**Purpose**: Process audio input (base64 encoded).

**Request**:
```json
{
  "audio": "base64_encoded_audio_data"
}
```

**Response**:
```json
{
  "command": "what time is it",
  "response": "Command processed successfully.",
  "success": true
}
```

**Flow**: Decodes audio → Speech recognition → Processes as command.

---

### GET `/api/reminders`
**Purpose**: Get all reminders (regular + scheduled).

**Response**:
```json
{
  "reminders": [
    "take medicine",
    "drink water - 3:00 PM",
    "appointment - Tomorrow at 10:00 AM"
  ],
  "regular": ["take medicine"],
  "scheduled": ["drink water - 3:00 PM", "appointment - Tomorrow at 10:00 AM"]
}
```

---

### GET `/api/contacts`
**Purpose**: Get emergency contacts.

**Response**:
```json
{
  "contacts": [
    {
      "name": "John Doe",
      "phone": "+1234567890",
      "previous_phone": "+0987654321"
    }
  ]
}
```

---

### POST `/api/contacts`
**Purpose**: Add emergency contact.

**Request**:
```json
{
  "name": "John Doe",
  "phone": "+1234567890",
  "previous_phone": "+0987654321"  // optional
}
```

**Response**:
```json
{
  "success": true,
  "message": "Contact added"
}
```

---

### DELETE `/api/contacts/<phone>`
**Purpose**: Delete emergency contact by phone number.

**Response**:
```json
{
  "success": true,
  "message": "Contact removed"
}
```

---

### GET `/api/notifications`
**Purpose**: Get pending notifications (polled by frontend).

**Response**:
```json
{
  "notifications": [
    {
      "id": "reminder_id",
      "text": "medicine",
      "message": "Reminder: medicine",
      "timestamp": "2024-01-15T15:00:05"
    }
  ]
}
```

**Note**: Notifications are cleared after being read (one-time delivery).

---

### DELETE `/api/notifications/<reminder_id>`
**Purpose**: Dismiss a specific notification.

**Response**:
```json
{
  "success": true
}
```

---

### GET `/api/profile`
**Purpose**: Get user profile.

**Response**:
```json
{
  "profile": {
    "name": "John",
    "preferences": {
      "tone": "gentle"
    }
  }
}
```

---

### POST `/api/profile`
**Purpose**: Set or update user profile.

**Request**:
```json
{
  "name": "John",
  "preferences": {
    "tone": "gentle"
  }
}
```

**Response**:
```json
{
  "success": true
}
```

---

### GET `/api/llm-status`
**Purpose**: Get LLM status (for debugging).

**Response**:
```json
{
  "llm": {
    "provider": "hf",
    "model": "gpt2",
    "ready": true,
    "last_error": null
  }
}
```

---

### GET `/api/health`
**Purpose**: Health check endpoint.

**Response**:
```json
{
  "status": "healthy"
}
```

---

## Technologies Used

### Backend:
- **Flask**: Web framework for REST API
- **Flask-CORS**: Cross-origin resource sharing
- **SpeechRecognition**: Google Speech Recognition API wrapper
- **pyttsx3**: Text-to-speech (CLI mode only)
- **Twilio**: SMS sending for emergency alerts
- **transformers**: Hugging Face model loading
- **openai**: OpenAI API client
- **requests**: HTTP requests for weather/news APIs
- **geopy**: Geocoding (fallback for weather)
- **python-dotenv**: Environment variable management

### Frontend:
- **React**: UI framework
- **Web Speech API**: Voice recognition and text-to-speech
- **Tailwind CSS**: Styling
- **lucide-react**: Icons

### Storage:
- **JSON**: File-based storage (`assistant_data.json`)

### AI/ML:
- **Hugging Face Transformers**: Local LLM models
- **OpenAI API**: Cloud-based LLM models

---

## Key Design Patterns

1. **Chain of Responsibility**: CommandProcessor routes commands to first matching processor
2. **Template Method**: BaseProcessor defines structure, subclasses implement specifics
3. **Observer Pattern**: NotificationScheduler observes time and triggers callbacks
4. **Singleton Pattern**: StorageManager uses single JSON file instance
5. **Strategy Pattern**: LLM provider selection (HF vs OpenAI)

---

## Environment Variables

### Required (Optional - graceful degradation if missing):
- `NEWS_API_KEY`: For news headlines
- `TWILIO_ACCOUNT_SID`: For emergency SMS
- `TWILIO_AUTH_TOKEN`: For emergency SMS
- `TWILIO_FROM_PHONE`: Twilio phone number

### LLM Configuration:
- `LLM_PROVIDER`: "hf" (Hugging Face) or "openai" (default: "hf")
- `LLM_MODEL`: Model name (default: "gpt2")
- `OPENAI_API_KEY`: Required if using OpenAI provider

---

## File Structure Summary

```
Project/
├── app.py                          # Main Flask application
├── Elderly_Voice_Assistant.py     # CLI version
├── Command_Processor.py            # Command router
├── Storage_Manager.py              # Data persistence
├── assistant_data.json             # Data storage file
├── requirements.txt                # Python dependencies
├── processors/
│   ├── Base_Processor.py           # Abstract base class
│   ├── Info_Processor.py           # Time, date, weather, news
│   ├── Reminder_Processor.py       # Reminder management
│   ├── Emergency_Processor.py     # Emergency/SOS
│   ├── Health_Processor.py         # Health & wellness
│   ├── Entertainment_Processor.py  # Jokes, stories, music
│   └── Notification_Scheduler.py   # Background scheduler
├── ai_modules/
│   └── LLM_Responder.py           # Natural language generation
└── frontend/
    ├── package.json                # Node dependencies
    └── src/
        ├── App.js                   # Main React component
        └── index.js                 # React entry point
```

---

## Conclusion

This project implements a comprehensive voice assistant system for elderly care with:
- **Modular architecture** (processors for different functionalities)
- **Robust error handling** (graceful degradation when APIs unavailable)
- **Real-time notifications** (background scheduler for reminders)
- **Natural conversation** (LLM integration for general chat)
- **User-friendly interface** (voice + text input, clear UI)
- **Extensible design** (easy to add new processors or features)

The system is designed to be reliable, user-friendly, and maintainable, with clear separation of concerns and well-documented code.

