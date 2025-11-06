from .Base_Processor import BaseProcessor
import random

class EntertainmentProcessor(BaseProcessor):
    keywords = ["joke", "story", "music"]

    def handle(self, command: str):
        if "joke" in command:
            jokes = [
                "Why don’t scientists trust atoms? Because they make up everything!",
                "I told my computer I needed a break, and it said no problem—it’ll go to sleep.",
                "Why did the scarecrow get promoted? Because he was outstanding in his field!",
                "Why did the bicycle fall over? It was two-tired!",
                "I would tell you a construction joke, but I’m still working on it.",
            ]
            self.speaker(random.choice(jokes))
        elif "story" in command:
            stories = [
                "Once upon a time, there was a wise old owl who watched over the forest. When animals argued, he listened calmly and helped them find peace.",
                "A little boat set sail on a quiet lake at dawn. As the sun rose, the water turned to gold, and the sailor smiled, knowing every day brings new light.",
                "In a small village, a gardener planted seeds of kindness. Soon, flowers bloomed in every courtyard—and so did friendships.",
                "A young child asked the moon why it followed them home. The moon winked and said, 'To make sure you always feel safe in the dark.'",
            ]
            self.speaker(random.choice(stories))
        elif "music" in command:
            tracks = [
                "Playing a calm instrumental track.",
                "Let me put on some gentle piano music for you.",
                "Here's a soothing nature melody with soft rain.",
                "Playing a relaxing lo-fi tune to help you unwind.",
            ]
            self.speaker(random.choice(tracks))  
        return True