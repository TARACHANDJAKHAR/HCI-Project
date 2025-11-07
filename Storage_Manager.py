"""
Storage Manager - Handles all data persistence for the assistant.

Manages JSON file storage for:
- Regular reminders (simple text reminders without times)
- Scheduled reminders (with specific times for notifications)
- Emergency contacts (name and phone number)
- User profile (name, preferences for personalization)

All data is stored in a single JSON file (assistant_data.json) for simplicity.
The file is created automatically if it doesn't exist.
"""

import json
import os


class StorageManager:
    """
    Manages persistent storage for assistant data using JSON file.
    
    Provides methods to save/load reminders, contacts, and user profile.
    Handles file creation if it doesn't exist.
    
    All operations are synchronous file I/O. For production, consider
    using a database for better performance and concurrency.
    """
    
    def __init__(self, filename="assistant_data.json"):
        """
        Initialize storage manager with a JSON file.
        
        Args:
            filename (str): Path to JSON file for data storage.
                           Defaults to "assistant_data.json" in current directory.
                           Can be absolute or relative path.
        """
        self.filename = filename
        
        # Create file with empty data structure if it doesn't exist
        # This ensures the file is always available for reading/writing
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                json.dump({
                    "reminders": [],              # Simple text reminders (legacy)
                    "emergency_contacts": [],     # Emergency contact list
                    "profile": {},                # User profile (name, preferences)
                    "scheduled_reminders": []     # Reminders with specific times
                }, f, indent=4)  # indent=4 for readable JSON

    def load(self, key):
        """
        Load data for a specific key from storage.
        
        This is a generic method that can load any top-level key
        from the JSON file. Returns empty list if key doesn't exist.
        
        Args:
            key (str): Key to load (e.g., "reminders", "emergency_contacts")
            
        Returns:
            list or dict: Data associated with the key, or empty list if not found
            
        Example:
            load("reminders") -> ["take medicine", "drink water"]
            load("profile") -> {"name": "John", "preferences": {"tone": "gentle"}}
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get(key, [])

    def save(self, key, value):
        """
        Append a value to a list in storage.
        
        This is a generic method for appending to any list in storage.
        Creates the list if it doesn't exist.
        
        Args:
            key (str): Key to save to (e.g., "reminders")
            value: Value to append to the list (can be any JSON-serializable type)
            
        Example:
            save("reminders", "take medicine") -> appends to reminders list
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        # Create list if it doesn't exist, then append
        data.setdefault(key, []).append(value)
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def add_contact(self, name, phone, previous_phone=None):
        """
        Add an emergency contact if it doesn't already exist.
        
        Checks for duplicate phone numbers to prevent adding the same contact twice.
        
        Args:
            name (str): Contact's name (e.g., "John Doe")
            phone (str): Contact's phone number (e.g., "+1234567890")
            previous_phone (str, optional): Previous phone number for display purposes
            
        Returns:
            bool: True if added successfully, False if contact already exists
            
        Example:
            add_contact("John", "+1234567890") -> True (added)
            add_contact("Jane", "+1234567890") -> False (phone already exists)
        """
        contacts = self.load("emergency_contacts")
        
        # Check if phone number already exists (prevent duplicates)
        if any(c["phone"] == phone for c in contacts):
            return False  # Contact already exists
        
        # Add new contact as dictionary with name, phone, and optional previous_phone
        contact_data = {"name": name, "phone": phone}
        if previous_phone:
            contact_data["previous_phone"] = previous_phone
        contacts.append(contact_data)
        
        # Save updated contacts list back to file
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["emergency_contacts"] = contacts
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)
        return True

    def remove_contact(self, phone):
        """
        Remove an emergency contact by phone number.
        
        Args:
            phone (str): Phone number of contact to remove
            
        Note:
            If phone number doesn't exist, this silently does nothing.
            Consider returning a boolean to indicate success/failure.
        """
        contacts = self.load("emergency_contacts")
        # Filter out the contact with matching phone number
        contacts = [c for c in contacts if c["phone"] != phone]
        
        # Save updated list (with contact removed)
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["emergency_contacts"] = contacts
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def get_contacts(self):
        """
        Get list of phone numbers from emergency contacts.
        
        Used by EmergencyProcessor to send SMS to all contacts.
        Only returns phone numbers, not names.
        
        Returns:
            list[str]: List of phone numbers
            
        Example:
            get_contacts() -> ["+1234567890", "+0987654321"]
        """
        contacts = self.load("emergency_contacts")
        return [c["phone"] for c in contacts]

    def get_profile(self):
        """
        Get user profile data (name, preferences).
        
        Profile is used for personalization:
        - Name: LLM can address user by name
        - Preferences: Tone, language, etc.
        
        Returns:
            dict: User profile dictionary with keys like "name", "preferences"
            
        Example:
            get_profile() -> {"name": "John", "preferences": {"tone": "gentle"}}
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get("profile", {})

    def set_profile(self, profile: dict):
        """
        Set or update user profile.
        
        Overwrites entire profile. To update partially, get profile first,
        modify it, then set it again.
        
        Args:
            profile (dict): Profile data with keys like "name", "preferences"
                           If None or empty dict, clears the profile
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["profile"] = profile or {}  # Use empty dict if None provided
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def save_scheduled_reminder(self, reminder_text: str, reminder_time: str, reminder_id: str = None):
        """
        Save a reminder with a scheduled time for notification.
        
        Creates a reminder object with:
        - id: Unique identifier (auto-generated if not provided)
        - text: Reminder message
        - time: Scheduled time in 'YYYY-MM-DD HH:MM' format
        - completed: False (set to True when notification is sent)
        
        Args:
            reminder_text (str): The reminder message/text (e.g., "take medicine")
            reminder_time (str): Time in format 'YYYY-MM-DD HH:MM' or 'HH:MM'
            reminder_id (str, optional): Unique ID for the reminder.
                                       If None, generates a new UUID (first 8 chars).
        
        Returns:
            str: The reminder ID (newly generated or provided)
            
        Example:
            save_scheduled_reminder("meds", "2024-01-15 15:00") -> "a1b2c3d4"
        """
        import uuid
        with open(self.filename, "r") as f:
            data = json.load(f)
        
        scheduled = data.get("scheduled_reminders", [])
        
        # Generate ID if not provided (use first 8 chars of UUID for readability)
        if reminder_id is None:
            reminder_id = str(uuid.uuid4())[:8]
        
        # Create reminder object with all necessary fields
        scheduled.append({
            "id": reminder_id,           # Unique identifier
            "text": reminder_text,        # What to remind about
            "time": reminder_time,        # When to remind (YYYY-MM-DD HH:MM)
            "completed": False            # Track if notification has been sent
        })
        
        # Save updated reminders list back to file
        data["scheduled_reminders"] = scheduled
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)
        return reminder_id

    def get_scheduled_reminders(self):
        """
        Get all scheduled reminders (both active and completed).
        
        Use this to get all reminders, then filter by completed status
        if you only want active ones.
        
        Returns:
            list[dict]: List of reminder dictionaries, each with:
                       id, text, time, completed fields
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get("scheduled_reminders", [])

    def mark_reminder_completed(self, reminder_id: str):
        """
        Mark a scheduled reminder as completed (notification sent).
        
        This prevents the reminder from being triggered again.
        Completed reminders are still stored but filtered out from active lists.
        
        Args:
            reminder_id (str): ID of the reminder to mark as completed
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        scheduled = data.get("scheduled_reminders", [])
        
        # Find and mark the reminder as completed
        for r in scheduled:
            if r.get("id") == reminder_id:
                r["completed"] = True
                break  # Found it, no need to continue
        
        # Save updated data
        data["scheduled_reminders"] = scheduled
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def delete_all_reminders(self):
        """
        Delete all regular (non-scheduled) reminders.
        
        This clears the "reminders" list but leaves scheduled reminders intact.
        Use delete_all_scheduled_reminders() to clear those separately.
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["reminders"] = []  # Clear the list
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def delete_all_scheduled_reminders(self):
        """
        Delete all scheduled reminders (both active and completed).
        
        This completely clears the scheduled_reminders list.
        Use delete_all_reminders() to clear regular reminders separately.
        """
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["scheduled_reminders"] = []  # Clear the list
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def delete_reminder_by_index(self, index: int):
        """
        Delete a regular reminder by its position in the list (1-based indexing).
        
        Uses 1-based indexing to match user expectations (first = 1, not 0).
        
        Args:
            index (int): Position of reminder (1 = first, 2 = second, etc.)
            
        Returns:
            bool: True if deleted successfully, False if index out of range
            
        Example:
            delete_reminder_by_index(1) -> deletes first reminder
            delete_reminder_by_index(5) -> deletes fifth reminder (if exists)
        """
        reminders = self.load("reminders")
        
        # Validate index is in valid range (1-based, so 1 to len(reminders))
        if 1 <= index <= len(reminders):
            reminders.pop(index - 1)  # Convert to 0-based index for list.pop()
            
            # Save updated list
            with open(self.filename, "r") as f:
                data = json.load(f)
            data["reminders"] = reminders
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=4)
            return True
        return False  # Index out of range

    def delete_scheduled_reminder_by_index(self, index: int):
        """
        Delete a scheduled reminder by its position in active reminders list (1-based).
        
        Only considers non-completed reminders when calculating the index.
        This matches how reminders are displayed to users (only active ones shown).
        
        Args:
            index (int): Position in active reminders list (1-based)
                        This matches the numbering shown in "list reminders"
            
        Returns:
            bool: True if deleted successfully, False if index out of range
            
        Example:
            If there are 3 active reminders:
            delete_scheduled_reminder_by_index(1) -> deletes first active reminder
            delete_scheduled_reminder_by_index(3) -> deletes third active reminder
        """
        scheduled = self.get_scheduled_reminders()
        # Filter to only active (non-completed) reminders
        # This matches what users see when they list reminders
        active = [r for r in scheduled if not r.get("completed", False)]
        
        # Validate index
        if 1 <= index <= len(active):
            # Get the ID of the reminder to delete
            reminder_id = active[index - 1]["id"]
            
            # Remove from full list (including completed ones)
            # This ensures we remove it even if there are completed reminders
            scheduled = [r for r in scheduled if r.get("id") != reminder_id]
            
            # Save updated list
            with open(self.filename, "r") as f:
                data = json.load(f)
            data["scheduled_reminders"] = scheduled
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=4)
            return True
        return False  # Index out of range
