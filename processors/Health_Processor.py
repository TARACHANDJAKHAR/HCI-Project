from .Base_Processor import BaseProcessor

class HealthProcessor(BaseProcessor):
    keywords = ["exercise", "motivate", "health"]

    def handle(self, command: str):
        if "exercise" in command:
            self.speaker("Let's do some light stretching for 5 minutes.")
        elif "motivate" in command:
            self.speaker("You are strong and doing great! Keep it up.")
        return True