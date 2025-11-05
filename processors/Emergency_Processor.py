from .Base_Processor import BaseProcessor
from twilio.rest import Client
import os

class EmergencyProcessor(BaseProcessor):
    keywords = ["emergency", "sos"]

    def __init__(self, speaker, storage):
        super().__init__(speaker, storage)
        account_sid = os.getenv("twilio_account_sid")
        auth_token = os.getenv("twilio_auth_token")
        self.from_phone = os.getenv("twilio_from_phone")  
        self.contacts = self.storage.get_contacts() if self.storage else []

        # Make Twilio optional: if credentials are missing, disable SMS sending gracefully
        if not all([account_sid, auth_token, self.from_phone]):
            self.client = None
        else:
            self.client = Client(account_sid, auth_token)

    def handle(self, command: str):
        if self.client is None:
            self.speaker("Emergency mode activated, but SMS is not configured.")
            self.speaker("Please set Twilio credentials to enable emergency texting.")
            return True
        self.speaker("Emergency SOS activated! Sending SMS to contacts.")
        if not self.contacts:
            self.speaker("No emergency contacts found.")
            return True
        for number in self.contacts:
            try:
                self.client.messages.create(
                    body="Emergency! I need help",
                    from_=self.from_phone,
                    to=number
                )
            except Exception as e:
                print(f"Failed to send SMS to {number}: {e}")
        self.speaker("Emergency SMS sent.")
        return True

    def match(self, command: str) -> bool:
        # Only trigger on clear emergency intents, not generic "help"
        text = command.lower()
        words = set(text.split())
        if "emergency" in words or "sos" in words:
            return True
        # Common phrases
        if "emergency help" in text or "call emergency" in text or "call 911" in text or "need emergency" in text:
            return True
        return False
