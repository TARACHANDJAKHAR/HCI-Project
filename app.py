from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io
import speech_recognition as sr
from Command_Processor import CommandProcessor
from Storage_Manager import StorageManager
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
    """Get all reminders"""
    try:
        reminders = storage.load("reminders")
        return jsonify({'reminders': reminders})
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

if __name__ == '__main__':
    app.run(debug=False,use_reloader=False, host='0.0.0.0', port=5000)
    
    