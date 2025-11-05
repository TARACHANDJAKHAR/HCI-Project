from .Base_Processor import BaseProcessor
import random

class EntertainmentProcessor(BaseProcessor):
    keywords = ["joke", "story", "music"]

    def handle(self, command: str):
        if "joke" in command:
            jokes = ["Why don’t scientists trust atoms? Because they make up everything!",
                     "I told my computer I needed a break, and it said no problem—it’ll go to sleep."]
            self.speaker(random.choice(jokes))
        elif "story" in command:
            self.speaker("Once upon a time, there was a wise old owl in the forest...")
        elif "music" in command:
            self.speaker("Playing your favorite music.")  
        return True