"""
Command Processor - Routes user commands to appropriate specialized processors.

This module implements a chain-of-responsibility pattern where user commands
are matched against keywords and routed to the first matching processor.
If no processor matches, the command is passed to the LLM for general conversation.

The processor chain is checked in order:
1. InfoProcessor (time, date, weather, news)
2. ReminderProcessor (reminders, meds, appointments)
3. EmergencyProcessor (emergency, SOS)
4. HealthProcessor (exercise, motivation, health)
5. EntertainmentProcessor (jokes, stories, music)
"""

import os
from processors.Info_Processor import InfoProcessor
from processors.Reminder_Processor import ReminderProcessor
from processors.Emergency_Processor import EmergencyProcessor
from processors.Health_Processor import HealthProcessor
from processors.Entertainment_Processor import EntertainmentProcessor


class CommandProcessor:
    """
    Main command processor that routes commands to specialized processors.
    
    Uses a chain-of-responsibility pattern: each processor checks if it can
    handle the command based on keywords. First match wins.
    
    If no processor matches, returns None so the caller can use LLM
    for general conversation.
    """
    
    def __init__(self, storage, speaker=None):
        """
        Initialize the command processor with storage and optional speaker.
        
        Args:
            storage: StorageManager instance for data persistence.
                    Used by processors to save/load reminders, contacts, etc.
            speaker: Optional function to call for text-to-speech output.
                    If None, creates a default lambda that just returns text.
                    This allows the processor to work even without TTS.
        """
        # Use provided speaker or create a default one that just returns text
        # This makes speaker optional - if not provided, responses are just returned
        if speaker is None:
            speaker = lambda text: text
        
        # Store references for use by processors
        self.speaker = speaker
        self.storage = storage
        # List to capture all response messages from processors
        # Processors may call speaker() multiple times, we capture all
        self.response_messages = []
    
        # Create a wrapper function that captures responses before passing to speaker
        # This allows us to collect all messages even if speaker doesn't return them
        def capture_speaker(text):
            """
            Wrapper that captures response text before passing to actual speaker.
            
            This is necessary because processors call speaker() to output text,
            but we also need to capture that text to return to the API caller.
            
            Args:
                text (str): Message to speak and capture
                
            Returns:
                Result of speaker function call (usually the text itself)
            """
            self.response_messages.append(text)  # Capture the message
            return self.speaker(text)  # Pass to actual speaker function
        
        # Initialize all specialized processors with the capture wrapper
        # Order matters: processors are checked in this sequence (first match wins)
        self.processors = [
            InfoProcessor(capture_speaker, storage),        # Handles: time, date, weather, news
            ReminderProcessor(capture_speaker, storage),    # Handles: reminders, meds, appointments
            EmergencyProcessor(capture_speaker, storage),    # Handles: emergency, SOS
            HealthProcessor(capture_speaker, storage),      # Handles: exercise, motivation, health
            EntertainmentProcessor(capture_speaker, storage), # Handles: jokes, stories, music
        ]

    def process(self, command: str):
        """
        Process a user command by routing it to the appropriate processor.
        
        This method:
        1. Clears previous response messages
        2. Iterates through processors in order
        3. Checks if each processor matches the command (via keywords)
        4. If match found, lets processor handle it and returns captured messages
        5. If no match, returns None (caller should use LLM)
        
        Args:
            command (str): User's command text (should be lowercase for matching)
            
        Returns:
            str: Combined response messages if a processor handled it.
                 Messages are joined with spaces.
            None: If no processor matched (should use LLM instead)
            
        Example:
            process("what time is it") -> "The current time is 14:30:15"
            process("set reminder for meds at 3pm") -> "Reminder set for 3:00 PM: meds"
            process("tell me a joke") -> "Why don't scientists trust atoms? ..."
            process("how are you") -> None (no processor matches, use LLM)
        """
        # Clear previous messages to avoid mixing responses from different commands
        self.response_messages = []
    
        # Try each processor in order until one matches
        for processor in self.processors:
            # Check if this processor's keywords match the command
            if processor.match(command):
                # Let the processor handle the command
                # It will call speaker() which we capture in response_messages
                processor.handle(command)
                # Return all captured messages joined together
                # If no messages were captured, return a default message
                return ' '.join(self.response_messages) if self.response_messages else "Command processed."
    
        # No processor matched - return None so caller can use LLM for general conversation
        return None
