import os
from processors.Info_Processor import InfoProcessor
from processors.Reminder_Processor import ReminderProcessor
from processors.Emergency_Processor import EmergencyProcessor
from processors.Health_Processor import HealthProcessor
from processors.Entertainment_Processor import EntertainmentProcessor


class CommandProcessor:
    def __init__(self, storage, speaker=None):
    # Use provided speaker or create a default one
       if speaker is None:
          speaker = lambda text: text
    
       self.speaker = speaker
       self.storage = storage
       self.response_messages = []
    
    # Create a wrapper that captures responses
       def capture_speaker(text):
          self.response_messages.append(text)
          return self.speaker(text)
    
       self.processors = [
           InfoProcessor(capture_speaker, storage),
           ReminderProcessor(capture_speaker, storage),
           EmergencyProcessor(capture_speaker, storage),
           HealthProcessor(capture_speaker, storage),
           EntertainmentProcessor(capture_speaker, storage),
        ]

    def process(self, command: str):
       self.response_messages = []  # Clear previous messages
    
       for processor in self.processors:
          if processor.match(command):
            processor.handle(command)
            return ' '.join(self.response_messages) if self.response_messages else "Command processed."
    
       return None