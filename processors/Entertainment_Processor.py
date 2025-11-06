"""
Entertainment Processor - Provides entertainment content.

Offers:
- Random jokes
- Short stories
- Music suggestions

Designed to provide light entertainment and companionship
for elderly users. Content is gentle and appropriate.
"""

from .Base_Processor import BaseProcessor
import random


class EntertainmentProcessor(BaseProcessor):
    """
    Processor for entertainment commands (jokes, stories, music).
    
    Provides light entertainment to keep users engaged and happy.
    All content is appropriate and gentle for elderly users.
    """
    
    # Keywords that trigger this processor
    keywords = ["joke", "story", "music"]

    def handle(self, command: str):
        """
        Handle entertainment commands.
        
        Args:
            command (str): User's command text
        """
        if "joke" in command:
            # Collection of gentle, appropriate jokes
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my computer I needed a break, and it said no problem—it'll go to sleep.",
                "Why did the scarecrow get promoted? Because he was outstanding in his field!",
                "Why did the bicycle fall over? It was two-tired!",
                "I would tell you a construction joke, but I'm still working on it.",
            ]
            # Select and tell a random joke
            self.speaker(random.choice(jokes))
            
        elif "story" in command:
            # Collection of gentle, uplifting short stories
            stories = [
                "Once upon a time, there was a wise old owl who watched over the forest. When animals argued, he listened calmly and helped them find peace.",
                "A little boat set sail on a quiet lake at dawn. As the sun rose, the water turned to gold, and the sailor smiled, knowing every day brings new light.",
                "In a small village, a gardener planted seeds of kindness. Soon, flowers bloomed in every courtyard—and so did friendships.",
                "A young child asked the moon why it followed them home. The moon winked and said, 'To make sure you always feel safe in the dark.'",
            ]
            # Select and tell a random story
            self.speaker(random.choice(stories))
            
        elif "music" in command:
            # Collection of music-related responses
            tracks = [
                "Playing a calm instrumental track.",
                "Let me put on some gentle piano music for you.",
                "Here's a soothing nature melody with soft rain.",
                "Playing a relaxing lo-fi tune to help you unwind.",
            ]
            # Select and announce a random music suggestion
            self.speaker(random.choice(tracks))
            
        return True
