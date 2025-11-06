"""
Elderly Care Assistant - Main Flask Application
This module serves as the backend API server for the voice assistant.
Handles HTTP requests, command processing, and notification management.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io
import speech_recognition as sr
from datetime import datetime, timedelta
from Command_Processor import CommandProcessor
from Storage_Manager import StorageManager
from processors.Notification_Scheduler import NotificationScheduler
from dotenv import load_dotenv
from ai_modules.LLM_Responder import LLMResponder

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend communication

# Initialize LLM responder for generating natural language responses
llm = LLMResponder()

# ============================================================================
# Component Initialization
# ============================================================================

# Initialize storage manager for persistent data (reminders, contacts, profile)
storage = StorageManager()

# Initialize speech recognizer for audio processing
recognizer = sr.Recognizer()

def speak_response(text):
    """
    Placeholder function for text-to-speech.
    Returns text to be spoken by frontend TTS engine.
    
    Args:
        text (str): Text to be spoken
        
    Returns:
        str: Same text (for frontend processing)
    """
    return text

# Initialize command processor with storage
command_processor = CommandProcessor(storage)

# Load user profile from storage and update LLM if available
try:
    llm.update_profile(storage.get_profile())
except Exception:
    pass  # Profile loading is optional, continue if it fails

# ============================================================================
# Notification System
# ============================================================================

# Global list to store pending notifications for frontend polling
pending_notifications = []

def notify_user(reminder_text: str, reminder_id: str):
    """
    Callback function called by NotificationScheduler when a reminder is due.
    Stores notification in pending_notifications for frontend to retrieve.
    
    Args:
        reminder_text (str): The reminder message text
        reminder_id (str): Unique identifier for the reminder
    """
    global pending_notifications
    notification = {
        "id": reminder_id,
        "text": reminder_text,
        "message": f"Reminder: {reminder_text}",
        "timestamp": datetime.now().isoformat()
    }
    pending_notifications.append(notification)
    print(f"NOTIFICATION: {reminder_text}")

# Initialize and start background notification scheduler
# Checks for due reminders every 10 seconds
scheduler = NotificationScheduler(storage, notify_user)
scheduler.start()

# ============================================================================
# API Routes
# ============================================================================

@app.route('/api/process-command', methods=['POST'])
def process_command():
    """
    Process text command from frontend.
    Routes command to appropriate processor or LLM for response.
    
    Request Body:
        {
            "command": "what time is it"
        }
    
    Returns:
        JSON response with assistant's reply or error
    """
    try:
        data = request.json
        command = data.get('command', '').lower()
        
        # Validate command exists
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        # Handle exit/bye commands
        if "exit" in command or "bye" in command:
            return jsonify({
                'response': 'Take care, I am always here when you need me.',
                'exit': True
            })
        
        # Process command through processor chain
        result = command_processor.process(command)
        
        # If no processor handled it, use LLM for general conversation
        if result is None:
            response_text = llm.generate(command)
        else:
            # Processor already generated response via speaker()
            response_text = result
        
        return jsonify({
            'response': response_text,
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """
    Process audio input from frontend (Web Speech API or recorded audio).
    Converts audio to text, then processes as command.
    
    Request Body:
        {
            "audio": "base64_encoded_audio_data"
        }
    
    Returns:
        JSON with recognized command and processing result
    """
    try:
        data = request.json
        audio_base64 = data.get('audio')
        
        if not audio_base64:
            return jsonify({'error': 'No audio provided'}), 400
        
        # Decode base64 audio to bytes
        audio_bytes = base64.b64decode(audio_base64)
        audio_file = io.BytesIO(audio_bytes)
        
        # Recognize speech using Google Speech Recognition
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            command = recognizer.recognize_google(audio_data, language="en-in").lower()
        
        # Process the recognized command
        result = command_processor.process(command)
        
        return jsonify({
            'command': command,
            'response': 'Command processed successfully.' if result else "I didn't understand that.",
            'success': True
        })
    
    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand audio'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    """
    Get all reminders (both regular and scheduled).
    Formats scheduled reminders with readable time display.
    
    Returns:
        JSON with combined reminders list, plus separate regular/scheduled lists
    """
    try:
        # Load both types of reminders
        regular_reminders = storage.load("reminders")
        scheduled_reminders = storage.get_scheduled_reminders()
        
        # Filter out completed scheduled reminders
        active_scheduled = [r for r in scheduled_reminders if not r.get("completed", False)]
        
        # Format scheduled reminders with human-readable times
        formatted_scheduled = []
        for rem in active_scheduled:
            try:
                dt = datetime.strptime(rem["time"], "%Y-%m-%d %H:%M")
                now = datetime.now()
                
                # Format time based on when it occurs
                if dt.date() == now.date():
                    # Today: show just time
                    time_display = dt.strftime("%I:%M %p")
                elif dt.date() == (now + timedelta(days=1)).date():
                    # Tomorrow: show "Tomorrow at X:XX PM"
                    time_display = f"Tomorrow at {dt.strftime('%I:%M %p')}"
                else:
                    # Future date: show full date and time
                    time_display = dt.strftime("%B %d at %I:%M %p")
                formatted_scheduled.append(f"{rem['text']} - {time_display}")
            except:
                # Fallback to raw time if parsing fails
                formatted_scheduled.append(f"{rem['text']} - {rem['time']}")
        
        # Combine both types for unified display
        all_reminders = regular_reminders + formatted_scheduled
        
        return jsonify({
            'reminders': all_reminders,
            'regular': regular_reminders,
            'scheduled': formatted_scheduled
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """
    Get all emergency contacts.
    
    Returns:
        JSON with list of emergency contacts
    """
    try:
        contacts = storage.load("emergency_contacts")
        return jsonify({'contacts': contacts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts', methods=['POST'])
def add_contact():
    """
    Add a new emergency contact.
    
    Request Body:
        {
            "name": "John Doe",
            "phone": "+1234567890"
        }
    
    Returns:
        JSON with success status and message
    """
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        
        if not name or not phone:
            return jsonify({'error': 'Name and phone required'}), 400
        
        success = storage.add_contact(name, phone)
        
        return jsonify({
            'success': success,
            'message': 'Contact added' if success else 'Contact already exists'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/<phone>', methods=['DELETE'])
def delete_contact(phone):
    """
    Delete an emergency contact by phone number.
    
    Args:
        phone (str): Phone number of contact to delete
    
    Returns:
        JSON with success status
    """
    try:
        storage.remove_contact(phone)
        return jsonify({'success': True, 'message': 'Contact removed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON with server status
    """
    return jsonify({'status': 'healthy'})

@app.route('/api/llm-status', methods=['GET'])
def llm_status():
    """
    Get current LLM status (provider, model, ready state, errors).
    Useful for debugging LLM configuration issues.
    
    Returns:
        JSON with LLM status information
    """
    try:
        return jsonify({'llm': llm.status()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """
    Get user profile (name, preferences).
    
    Returns:
        JSON with user profile data
    """
    try:
        return jsonify({'profile': storage.get_profile()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def set_profile():
    """
    Set or update user profile.
    
    Request Body:
        {
            "name": "John",
            "preferences": {"tone": "gentle"}
        }
    
    Returns:
        JSON with success status
    """
    try:
        data = request.json or {}
        profile = {
            'name': data.get('name'),
            'preferences': data.get('preferences') or {}
        }
        storage.set_profile(profile)
        llm.update_profile(profile)  # Update LLM with new profile
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """
    Get pending notifications (frontend polls this endpoint).
    Notifications are cleared after being read.
    
    Returns:
        JSON with list of pending notifications
    """
    global pending_notifications
    notifications = pending_notifications.copy()
    pending_notifications = []  # Clear after reading (one-time delivery)
    return jsonify({'notifications': notifications})

@app.route('/api/notifications/<reminder_id>', methods=['DELETE'])
def dismiss_notification(reminder_id):
    """
    Dismiss a specific notification by ID.
    
    Args:
        reminder_id (str): ID of notification to dismiss
    
    Returns:
        JSON with success status
    """
    global pending_notifications
    pending_notifications = [n for n in pending_notifications if n.get("id") != reminder_id]
    return jsonify({'success': True})

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Run Flask server
    # debug=False: Disable debug mode for production
    # use_reloader=False: Disable auto-reload to prevent scheduler restart issues
    # host='0.0.0.0': Listen on all network interfaces
    # port=5000: Default Flask port
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)