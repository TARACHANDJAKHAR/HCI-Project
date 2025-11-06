"""
Base Processor - Abstract base class for all command processors.

All specialized processors inherit from this class and implement
the handle() method. The match() method checks if keywords are present.

This implements the Template Method pattern where the base class
defines the structure (match -> handle) and subclasses provide
specific implementations.
"""


class BaseProcessor:
    """
    Base class for all command processors.
    
    Provides common functionality:
    - Keyword matching to determine if processor can handle a command
    - Speaker function for text-to-speech output
    - Storage access for data persistence
    
    Subclasses must:
    1. Define a 'keywords' list of strings to match against
    2. Implement the handle() method to process matching commands
    """
    
    # Subclasses must override this with their specific keywords
    # Example: keywords = ["reminder", "meds", "medicine"]
    keywords = []

    def __init__(self, speaker, storage=None):
        """
        Initialize base processor with dependencies.
        
        Args:
            speaker: Function to call for text-to-speech output.
                    Typically receives a string and outputs it via TTS.
            storage: Optional StorageManager instance for data persistence.
                    Used to save/load reminders, contacts, profile, etc.
        """
        self.speaker = speaker  # Function to output text (TTS)
        self.storage = storage  # Storage manager for data persistence

    def match(self, command: str) -> bool:
        """
        Check if this processor can handle the given command.
        
        Matches if ANY keyword from the keywords list appears in the command.
        This is a simple substring match (case-sensitive).
        
        Args:
            command (str): User's command text (usually lowercase)
            
        Returns:
            bool: True if any keyword matches, False otherwise
            
        Example:
            If keywords = ["reminder", "meds"]
            - "set a reminder" -> True (contains "reminder")
            - "take my medicine" -> True (contains "meds" in "medicine")
            - "what time is it" -> False (no keywords match)
        """
        return any(keyword in command for keyword in self.keywords)

    def handle(self, command: str):
        """
        Process the command. Must be implemented by subclasses.
        
        This method is called by CommandProcessor when match() returns True.
        Subclasses should:
        1. Parse the command to extract relevant information
        2. Perform the requested action (save data, fetch info, etc.)
        3. Call self.speaker() to provide feedback to the user
        
        Args:
            command (str): User's command text
            
        Raises:
            NotImplementedError: If subclass doesn't implement this method
            
        Returns:
            Typically returns True to indicate successful handling
        """
        raise NotImplementedError("Subclasses must implement handle() method")
