"""
Emergency Processor - Handles emergency/SOS commands.

When user says "emergency" or "SOS", this processor:
1. Sends SMS to all emergency contacts via Twilio
2. Provides voice feedback about the action

Twilio credentials are optional - if not configured, processor
still works but just informs user that SMS is not available.

This prevents the app from crashing if Twilio env vars are missing.
"""

from .Base_Processor import BaseProcessor
from twilio.rest import Client
import os


class EmergencyProcessor(BaseProcessor):
    """
    Processor for emergency/SOS commands.
    
    Sends SMS alerts to all emergency contacts when activated.
    Requires Twilio account credentials (optional - graceful degradation if missing).
    """
    
    # Keywords that trigger this processor
    # Note: "help" is intentionally excluded to avoid false triggers
    keywords = ["emergency", "sos"]

    def __init__(self, speaker, storage):
        """
        Initialize emergency processor with optional Twilio support.
        
        Args:
            speaker: Function for text-to-speech output
            storage: StorageManager to get emergency contacts
        """
        super().__init__(speaker, storage)
        
        # Get Twilio credentials from environment variables
        account_sid = os.getenv("twilio_account_sid")
        auth_token = os.getenv("twilio_auth_token")
        self.from_phone = os.getenv("twilio_from_phone")  # Twilio phone number
        
        # Load emergency contacts from storage
        self.contacts = self.storage.get_contacts() if self.storage else []

        # Make Twilio optional: if credentials are missing, disable SMS sending gracefully
        # This prevents crashes when Twilio is not configured
        if not all([account_sid, auth_token, self.from_phone]):
            # Missing credentials - disable SMS but processor still works
            self.client = None
        else:
            # All credentials present - initialize Twilio client
            self.client = Client(account_sid, auth_token)

    def handle(self, command: str):
        """
        Handle emergency/SOS command.
        
        If Twilio is configured, sends SMS to all emergency contacts.
        If not configured, informs user that SMS is unavailable.
        
        Args:
            command (str): User's command text
        """
        # Check if Twilio is configured
        if self.client is None:
            self.speaker("Emergency mode activated, but SMS is not configured.")
            self.speaker("Please set Twilio credentials to enable emergency texting.")
            return True
        
        # Twilio is configured - proceed with SMS sending
        self.speaker("Emergency SOS activated! Sending SMS to contacts.")
        
        # Check if there are any emergency contacts
        if not self.contacts:
            self.speaker("No emergency contacts found.")
            return True
        
        # Send SMS to each emergency contact
        for number in self.contacts:
            try:
                self.client.messages.create(
                    body="Emergency! I need help",  # SMS message text
                    from_=self.from_phone,         # Twilio phone number
                    to=number                       # Recipient phone number
                )
            except Exception as e:
                # Log error but continue sending to other contacts
                print(f"Failed to send SMS to {number}: {e}")
        
        # Confirm SMS were sent
        self.speaker("Emergency SMS sent.")
        return True

    def match(self, command: str) -> bool:
        """
        Override match() to be more specific and avoid false triggers.
        
        Only triggers on clear emergency intents, not generic "help".
        This prevents "help me find X" from triggering emergency mode.
        
        Args:
            command (str): User's command text
            
        Returns:
            bool: True if command is clearly an emergency request
        """
        text = command.lower()
        words = set(text.split())
        
        # Direct keyword match
        if "emergency" in words or "sos" in words:
            return True
        
        # Common emergency phrases
        emergency_phrases = [
            "emergency help",
            "call emergency",
            "call 911",
            "need emergency"
        ]
        
        # Check if any emergency phrase appears in command
        for phrase in emergency_phrases:
            if phrase in text:
                return True
        
        return False
