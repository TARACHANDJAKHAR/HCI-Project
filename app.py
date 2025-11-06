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

load_dotenv()

app = Flask(__name__)
CORS(app)
llm=LLMResponder()  # Enable CORS for frontend communication

# Initialize components
storage = StorageManager()
recognizer = sr.Recognizer()

def speak_response(text):
    """This will be returned to frontend for TTS"""
    return text

command_processor = CommandProcessor(storage)

# Initialize LLM profile from storage if available
try:
    llm.update_profile(storage.get_profile())
except Exception:
    pass

# Store pending notifications for frontend to poll
pending_notifications = []

def notify_user(reminder_text: str, reminder_id: str):
    """Callback when reminder is due - stores notification for frontend"""
    global pending_notifications
    notification = {
        "id": reminder_id,
        "text": reminder_text,
        "message": f"Reminder: {reminder_text}",
        "timestamp": datetime.now().isoformat()
    }
    pending_notifications.append(notification)
    print(f"NOTIFICATION: {reminder_text}")

# Initialize and start notification scheduler
scheduler = NotificationScheduler(storage, notify_user)
scheduler.start()

@app.route('/api/process-command', methods=['POST'])
def process_command():
    """Process text command from frontend"""
    try:
        data = request.json
        command = data.get('command', '').lower()
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        if "exit" in command or "bye" in command:
            return jsonify({
                'response': 'Take care, I am always here when you need me.',
                'exit': True
            })
        
        result = command_processor.process(command)
        
        if result is None:
            response_text = llm.generate(command)
        else:
            # The processor already called speaker(), capture that
            response_text = result
        
        return jsonify({
            'response': response_text,
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """Process audio from frontend (Web Speech API or recorded audio)"""
    try:
        data = request.json
        audio_base64 = data.get('audio')
        
        if not audio_base64:
            return jsonify({'error': 'No audio provided'}), 400
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        audio_file = io.BytesIO(audio_bytes)
        
        # Recognize speech
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            command = recognizer.recognize_google(audio_data, language="en-in").lower()
        
        # Process command
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
    """Get all reminders (both regular and scheduled)"""
    try:
        regular_reminders = storage.load("reminders")
        scheduled_reminders = storage.get_scheduled_reminders()
        
        # Filter active scheduled reminders and format them
        active_scheduled = [r for r in scheduled_reminders if not r.get("completed", False)]
        
        # Format scheduled reminders for display
        formatted_scheduled = []
        for rem in active_scheduled:
            try:
                dt = datetime.strptime(rem["time"], "%Y-%m-%d %H:%M")
                now = datetime.now()
                if dt.date() == now.date():
                    time_display = dt.strftime("%I:%M %p")
                elif dt.date() == (now + timedelta(days=1)).date():
                    time_display = f"Tomorrow at {dt.strftime('%I:%M %p')}"
                else:
                    time_display = dt.strftime("%B %d at %I:%M %p")
                formatted_scheduled.append(f"{rem['text']} - {time_display}")
            except:
                formatted_scheduled.append(f"{rem['text']} - {rem['time']}")
        
        # Combine both types
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
    """Get emergency contacts"""
    try:
        contacts = storage.load("emergency_contacts")
        return jsonify({'contacts': contacts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts', methods=['POST'])
def add_contact():
    """Add emergency contact"""
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
    """Delete emergency contact"""
    try:
        storage.remove_contact(phone)
        return jsonify({'success': True, 'message': 'Contact removed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/api/llm-status', methods=['GET'])
def llm_status():
    try:
        return jsonify({'llm': llm.status()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    try:
        return jsonify({'profile': storage.get_profile()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def set_profile():
    try:
        data = request.json or {}
        profile = {
            'name': data.get('name'),
            'preferences': data.get('preferences') or {}
        }
        storage.set_profile(profile)
        llm.update_profile(profile)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get pending notifications (frontend polls this)"""
    global pending_notifications
    notifications = pending_notifications.copy()
    pending_notifications = []  # Clear after reading
    return jsonify({'notifications': notifications})

@app.route('/api/notifications/<reminder_id>', methods=['DELETE'])
def dismiss_notification(reminder_id):
    """Dismiss a notification"""
    global pending_notifications
    pending_notifications = [n for n in pending_notifications if n.get("id") != reminder_id]
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=False,use_reloader=False, host='0.0.0.0', port=5000)
    
    