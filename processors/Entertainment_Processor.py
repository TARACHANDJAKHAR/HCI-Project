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
    keywords = ["joke", "story", "music", "entertainment", "entertain"]

    def handle(self, command: str):
        """
        Handle entertainment commands.
        
        Args:
            command (str): User's command text
        """
        text = command.lower().strip()
        
        # If user just says "entertainment" or "entertain" without other words, offer options
        if text == "entertainment" or text == "entertain":
            self.speaker("I can tell you a joke, share a story, or suggest some music. What would you like?")
            return True
            
        if "joke" in text:
            # Collection of gentle, appropriate jokes suitable for elderly users
            # All jokes are clean, positive, and easy to understand
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my computer I needed a break, and it said no problem—it'll go to sleep.",
                "Why did the scarecrow get promoted? Because he was outstanding in his field!",
                "Why did the bicycle fall over? It was two-tired!",
                "I would tell you a construction joke, but I'm still working on it.",
                "Why did the coffee file a police report? It got mugged!",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
                "Why did the math book look so sad? Because it had too many problems!",
                "What do you call a fake noodle? An impasta!",
                "Why did the golfer bring two pairs of pants? In case he got a hole in one!",
                "What's orange and sounds like a parrot? A carrot!",
                "Why don't scientists trust atoms? Because they make up everything!",
                "What do you call a sleeping bull? A bulldozer!",
                "Why did the cookie go to the doctor? Because it felt crummy!",
                "What's a tree's favorite drink? Root beer!",
                "Why don't oysters share? Because they're shellfish!",
                "What do you call a bear in the rain? A drizzly bear!",
                "Why did the tomato turn red? Because it saw the salad dressing!",
            ]
            # Select and tell a random joke
            self.speaker(random.choice(jokes))
            
        elif "story" in text:
            # Collection of gentle, uplifting short stories perfect for elderly users
            # Stories are positive, heartwarming, and easy to follow
            stories = [
                "Once upon a time, there was a wise old owl who watched over the forest. When animals argued, he listened calmly and helped them find peace. The owl taught everyone that kindness and patience make the world a better place.",
                "A little boat set sail on a quiet lake at dawn. As the sun rose, the water turned to gold, and the sailor smiled, knowing every day brings new light and new opportunities for joy.",
                "In a small village, a gardener planted seeds of kindness. Soon, flowers bloomed in every courtyard—and so did friendships. The village became known as the happiest place, where everyone helped each other.",
                "A young child asked the moon why it followed them home. The moon winked and said, 'To make sure you always feel safe in the dark, and to remind you that even in darkness, there is always light.'",
                "There was an old oak tree that had stood for a hundred years. Children loved to play under its branches, and it provided shade for tired travelers. The tree was happy because it knew it was making the world a better place, one day at a time.",
                "A grandmother baked cookies every Sunday. Her grandchildren would visit, and the smell of fresh cookies filled the house with warmth and love. Those simple moments became the most precious memories.",
                "In a garden, a butterfly landed on a flower. The flower asked, 'Why do you visit me?' The butterfly replied, 'Because you bring beauty and joy to everyone who sees you, just like you do for me.'",
                "An old man sat on a park bench every morning, feeding the birds. People would stop and chat, and soon the bench became a place where friendships blossomed. The simple act of kindness created a community.",
                "A library cat named Whiskers loved to sit on the laps of readers. Children and adults alike found comfort in her purring. She taught everyone that sometimes the best company is quiet and gentle.",
                "A lighthouse keeper spent his life helping ships find their way home. Even though his work was lonely, he knew he was saving lives. His dedication showed that every person can make a difference.",
            ]
            # Select and tell a random story
            self.speaker(random.choice(stories))
            
        elif "music" in text:
            # Collection of music-related responses with variety
            tracks = [
                "Playing a calm instrumental track for you.",
                "Let me put on some gentle piano music to soothe your mind.",
                "Here's a soothing nature melody with soft rain sounds.",
                "Playing a relaxing lo-fi tune to help you unwind and relax.",
                "I'm playing some beautiful classical music that will calm your spirit.",
                "Let me put on some soft jazz music for a peaceful atmosphere.",
                "Here's some gentle acoustic guitar music to brighten your day.",
                "Playing peaceful meditation music to help you find inner calm.",
            ]
            # Select and announce a random music suggestion
            self.speaker(random.choice(tracks))
            
        return True
