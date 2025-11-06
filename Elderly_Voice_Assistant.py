"""
Elderly Voice Assistant - Standalone CLI version of the assistant.

This is an alternative interface that runs in the terminal with:
- Microphone input (speech recognition)
- Text-to-speech output (pyttsx3)

Useful for:
- Testing without web interface
- Running on devices without browser
- Development and debugging

Main entry point: Run this file directly to start the CLI assistant.
"""

import pyttsx3
import speech_recognition as sr
from Command_Processor import CommandProcessor
from Storage_Manager import StorageManager
from dotenv import load_dotenv
from ai_modules.LLM_Responder import LLMResponder


def configure():
    """
    Load environment variables from .env file.
    
    This must be called before initializing components that need env vars.
    """
    load_dotenv()


class ElderlyVoiceAssistant:
    """
    Standalone voice assistant that runs in terminal.
    
    Uses microphone for input and text-to-speech for output.
    Perfect for testing or running on devices without web browser.
    """
    
    def __init__(self):
        """
        Initialize the voice assistant with all components.
        
        Sets up:
        - Speech recognition (microphone input)
        - Text-to-speech (audio output)
        - Command processor (handles commands)
        - Storage manager (saves data)
        - LLM responder (general conversation)
        """
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Initialize storage for data persistence
        self.storage = StorageManager()
        
        # Initialize LLM for natural conversation
        self.llm = LLMResponder()

        # Create speaker function for TTS (text-to-speech)
        def speak_with_tts(text):
            """
            Internal function that speaks text using pyttsx3.
            
            Args:
                text (str): Text to speak
                
            Returns:
                str: Same text (for compatibility with processor)
            """
            print(f"Assistant: {text}")
            try:
                # Initialize TTS engine
                tts_engine = pyttsx3.init()
                # Queue text for speaking
                tts_engine.say(text)
                # Block until speech is complete
                tts_engine.runAndWait()
            except Exception as e:
                print(f"Speech Output Error: {e}")
            return text
        
        # Initialize command processor with storage and TTS speaker
        self.command_processor = CommandProcessor(self.storage, speak_with_tts)

    def speak(self, text: str):
        """
        Speak text using text-to-speech engine.
        
        Used by main loop for direct speech output.
        
        Args:
            text (str): Text to speak
        """
        print(f"Assistant: {text}")
        try:
            # Initialize TTS engine
            tts_engine = pyttsx3.init()
            # Queue text for speaking
            tts_engine.say(text)
            # Block until speech is complete
            tts_engine.runAndWait()
        except Exception as e:
            print(f"Speech Output Error: {e}")

    def listen(self) -> str:
        """
        Listen for voice input from microphone.
        
        Uses Google Speech Recognition API (requires internet).
        Handles errors gracefully with user-friendly messages.
        
        Returns:
            str: Recognized command text (lowercase), or empty string on error
        """
        with sr.Microphone() as src:
            print("Listening...")
            # Set pause threshold (how long to wait for speech to end)
            self.recognizer.pause_threshold = 1
            # Record audio from microphone
            audio = self.recognizer.listen(src)
        
        try:
            print("Recognizing...")
            # Use Google Speech Recognition (requires internet)
            command = self.recognizer.recognize_google(audio, language="en-in")
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            # Could not understand audio
            self.speak("Can you say it again?")
            return ""
        except sr.RequestError:
            # API error (network issue, etc.)
            self.speak("Trying to connect to the internet")
            return ""

    def run(self):
        """
        Main loop: continuously listen and respond.
        
        Runs until user says "exit" or "bye".
        Each iteration:
        1. Listens for command
        2. Processes command through processor chain
        3. If no processor matches, uses LLM
        4. Speaks the response
        """
        # Greet user on startup
        self.speak("Hello! I am your elderly care assistant. How can I help you?")
        
        # Main conversation loop
        while True:
            # Listen for user input
            command = self.listen()
            
            # Skip if no command received (error handling already done in listen())
            if not command:
                continue
            
            # Check for exit command
            if "exit" in command or "bye" in command:
                self.speak("Take care, I am always here when you need me.")
                break
            
            # Process command through processor chain
            result = self.command_processor.process(command)
            
            # If no processor handled it, use LLM for general conversation
            if result is None:
                response = self.llm.generate(command)
                self.speak(response)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Load environment variables
    configure()
    
    # Create and run assistant
    elderly_voice_assistant = ElderlyVoiceAssistant()
    
    # Add a default emergency contact for testing
    elderly_voice_assistant.storage.add_contact("Harshit", "+919324831545")
    
    # Start the main loop
    elderly_voice_assistant.run()
