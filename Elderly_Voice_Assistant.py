import pyttsx3
import speech_recognition as sr
from Command_Processor import CommandProcessor
from Storage_Manager import StorageManager
from dotenv import load_dotenv
from ai_modules.LLM_Responder import LLMResponder

def configure():
    load_dotenv()

class ElderlyVoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.storage = StorageManager()
        self.llm = LLMResponder()

        
        # Create speaker function for TTS
        def speak_with_tts(text):
            print(f"Assistant: {text}")
            try:
                tts_engine = pyttsx3.init()
                tts_engine.say(text)
                tts_engine.runAndWait()
            except Exception as e:
                print(f"Speech Output Error: {e}")
            return text
        
        # Initialize command processor with storage and speaker
        self.command_processor = CommandProcessor(self.storage, speak_with_tts)

    def speak(self, text: str):
        """Wrapper for speaking (used by main loop)"""
        print(f"Assistant: {text}")
        try:
            tts_engine = pyttsx3.init()
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"Speech Output Error: {e}")

    def listen(self) -> str:
        with sr.Microphone() as src:
            print("Listening...")
            self.recognizer.pause_threshold = 1
            audio = self.recognizer.listen(src)
        try:
            print("Recognizing...")
            command = self.recognizer.recognize_google(audio, language="en-in")
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            self.speak("Can you say it again?")
            return ""
        except sr.RequestError:
            self.speak("Trying to connect to the internet")
            return ""

    def run(self):
        self.speak("Hello! I am your elderly care assistant. How can I help you?")
        while True:
            command = self.listen()
            if not command:
                continue
            if "exit" in command or "bye" in command:
                self.speak("Take care, I am always here when you need me.")
                break
            
            # Process command
            result = self.command_processor.process(command)
            
            if result is None:
               response = self.llm.generate(command)
               self.speak(response)

        

if __name__ == "__main__":
    configure()
    elderly_voice_assistant = ElderlyVoiceAssistant()
    elderly_voice_assistant.storage.add_contact("Harshit", "+919324831545")
    elderly_voice_assistant.run()