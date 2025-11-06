"""
Health Processor - Handles health and wellness related commands.

Provides:
- Exercise suggestions
- Motivational messages

Simple processor for basic health-related interactions.
Can be extended with more features like medication tracking,
exercise routines, health tips, etc.
"""

from .Base_Processor import BaseProcessor


class HealthProcessor(BaseProcessor):
    """
    Processor for health and wellness commands.
    
    Provides simple health-related responses like exercise suggestions
    and motivational messages. Can be extended with more features.
    """
    
    # Keywords that trigger this processor
    keywords = ["exercise", "motivate", "health"]

    def handle(self, command: str):
        """
        Handle health-related commands.
        
        Args:
            command (str): User's command text
        """
        if "exercise" in command:
            # Suggest light exercise
            self.speaker("Let's do some light stretching for 5 minutes.")
        elif "motivate" in command:
            # Provide motivational message
            self.speaker("You are strong and doing great! Keep it up.")
        return True
