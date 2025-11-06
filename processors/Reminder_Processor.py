"""
Reminder Processor - Handles all reminder-related commands.

This processor manages:
- Setting reminders with specific times
- Listing all reminders (regular and scheduled)
- Deleting reminders (all or by index)
- Counting reminders

Supports natural language time parsing:
- "set reminder for meds at 3pm"
- "set reminder for water at 10:30 am"
- "list reminders"
- "delete all reminders"
- "delete reminder 1"
"""

from .Base_Processor import BaseProcessor
import re
from datetime import datetime, timedelta


class ReminderProcessor(BaseProcessor):
    """
    Processor for reminder-related commands.
    
    Handles setting, listing, deleting, and counting reminders.
    Supports both regular reminders (text only) and scheduled reminders (with times).
    """
    
    # Keywords that trigger this processor
    keywords = ["reminder", "meds", "medicine", "water", "appointment", "delete", "remove", "clear"]

    def _parse_time(self, command: str):
        """
        Extract time from command using regex patterns.
        
        Supports multiple time formats:
        - "at 3pm" or "at 3:30 pm"
        - "at 15:30" (24-hour format)
        - "12:15" or "1:13 am" (standalone time)
        - "tomorrow at 10am"
        
        Args:
            command (str): Full command text to parse
            
        Returns:
            tuple: (time_str, is_tomorrow)
                   - time_str: Formatted as "YYYY-MM-DD HH:MM"
                   - is_tomorrow: Boolean indicating if reminder is for tomorrow
        """
        text = command.lower()
        
        # Multiple regex patterns to match different time formats
        # Patterns are tried in order, first match wins
        time_patterns = [
            r'at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?',  # "at 3pm", "at 15:30", "at 3:30 pm"
            r'at\s+(\d{1,2})\s*(am|pm)',            # "at 3 pm" or "at 12am"
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',        # "12:15" or "1:13 am" (standalone)
            r'(\d{1,2})\s*(am|pm)',                 # "3 pm" or "12am" (no colon)
        ]
        
        # Try each pattern until one matches
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                # Extract hour and minute from regex groups
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                
                # Handle AM/PM - check all groups for am/pm indicator
                ampm = None
                for g in groups:
                    if g and g.lower() in ['am', 'pm']:
                        ampm = g.lower()
                        break
                
                # Convert 12-hour format to 24-hour format
                if ampm:
                    if ampm == 'pm' and hour < 12:
                        hour += 12  # 1pm -> 13, 2pm -> 14, etc.
                    elif ampm == 'am' and hour == 12:
                        hour = 0    # 12am -> 0 (midnight)
                
                # Ensure hour is valid (0-23) and minute is valid (0-59)
                hour = hour % 24
                minute = min(59, max(0, minute))
                
                # Check if reminder is for tomorrow
                is_tomorrow = "tomorrow" in text
                if is_tomorrow:
                    target_date = datetime.now() + timedelta(days=1)
                else:
                    target_date = datetime.now()
                    # If no AM/PM specified and hour <= 12, make intelligent guess
                    # If current time is afternoon (>= 12) and hour is 1-6, assume PM
                    if not ampm and hour <= 12:
                        current_hour = datetime.now().hour
                        if current_hour >= 12 and hour <= 6:
                            hour += 12  # Assume PM for afternoon hours
                            hour = hour % 24
                
                # Create datetime object with parsed hour and minute
                target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                time_str = target_datetime.strftime("%Y-%m-%d %H:%M")
                return time_str, is_tomorrow
        
        # Default: if no time found, assume next hour
        # This provides a fallback so reminder is always set
        next_hour = datetime.now() + timedelta(hours=1)
        return next_hour.strftime("%Y-%m-%d %H:%M"), False

    def _clean_reminder_text(self, command: str):
        """
        Extract clean reminder text by removing command phrases and time patterns.
        
        Removes phrases like "set a reminder for", "add reminder", etc.
        Also removes time-related words and numbers to get just the reminder content.
        
        Args:
            command (str): Full command text
            
        Returns:
            str: Clean reminder text with command phrases and times removed
            
        Example:
            "set reminder for medicines at 3pm" -> "medicines"
            "add reminder to take water" -> "take water"
        """
        text = command
        
        # Remove common command phrases (case insensitive regex)
        patterns_to_remove = [
            r'set\s+(a\s+)?reminder\s+(for\s+)?',  # "set reminder for" or "set a reminder for"
            r'add\s+(a\s+)?reminder\s+(for\s+)?',  # "add reminder for" or "add a reminder for"
            r'remind\s+(me\s+)?(to\s+)?(about\s+)?',  # "remind me to" or "remind about"
            r'reminder\s+(for\s+)?',               # Just "reminder for"
        ]
        
        # Apply each pattern to remove command phrases
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove time-related words and patterns
        text = re.sub(r'\b(at|tomorrow|am|pm)\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d{1,2}:?\d{0,2}\s*(am|pm)?\b', '', text, flags=re.IGNORECASE)
        
        # Clean up extra spaces (multiple spaces -> single space)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def handle(self, command: str):
        """
        Handle reminder-related commands.
        
        Routes to appropriate handler based on command content:
        - "list" or "show" -> list all reminders
        - "set", "add", or "remind" -> create new reminder
        - "delete", "remove", or "clear" -> delete reminders
        - "how many" or "count" -> count reminders
        
        Args:
            command (str): User's command text
        """
        text = command.lower()
        
        # Check for list/show FIRST (before checking for set/add)
        # This prevents "list reminders" from being treated as "set reminder"
        if "list" in text or "show" in text:
            # Load both types of reminders
            reminders = self.storage.load("reminders")
            scheduled = self.storage.get_scheduled_reminders()
            
            # Filter out completed scheduled reminders (only show active ones)
            active_scheduled = [r for r in scheduled if not r.get("completed", False)]
            
            # Helper function to format time for display
            def format_time(time_str):
                """
                Convert YYYY-MM-DD HH:MM to human-readable format.
                
                Returns:
                    str: Formatted time like "3:00 PM", "Tomorrow at 10:00 AM", etc.
                """
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    now = datetime.now()
                    if dt.date() == now.date():
                        # Today: show just time
                        return dt.strftime("%I:%M %p")
                    elif dt.date() == (now + timedelta(days=1)).date():
                        # Tomorrow: show "Tomorrow at X:XX PM"
                        return f"Tomorrow at {dt.strftime('%I:%M %p')}"
                    else:
                        # Future date: show full date and time
                        return dt.strftime("%B %d at %I:%M %p")
                except:
                    return time_str  # Fallback to raw time if parsing fails
            
            # Helper function to clean reminder text for display
            def clean_display_text(text):
                """
                Remove command phrases from reminder text for cleaner display.
                
                Args:
                    text (str): Reminder text that may contain command phrases
                    
                Returns:
                    str: Cleaned text without command phrases
                """
                if not text:
                    return text
                cleaned = text
                # Remove common command phrases from the beginning
                patterns = [
                    r'^set\s+(a\s+)?reminder\s+(for\s+)?',
                    r'^add\s+(a\s+)?reminder\s+(for\s+)?',
                    r'^remind\s+(me\s+)?(to\s+)?(about\s+)?',
                ]
                for pattern in patterns:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
                return cleaned.strip()
            
            # Build the reminder list message
            if reminders or active_scheduled:
                msg_parts = []
                
                # Add regular reminders (clean them up for display)
                if reminders:
                    for idx, rem in enumerate(reminders, 1):
                        cleaned_rem = clean_display_text(rem)
                        if cleaned_rem:  # Only add if there's actual content
                            msg_parts.append(f"{idx}. {cleaned_rem}")
                
                # Add scheduled reminders (clean them up and format time)
                if active_scheduled:
                    # Start numbering after regular reminders
                    start_num = len([r for r in reminders if clean_display_text(r)]) + 1
                    for idx, rem in enumerate(active_scheduled, start_num):
                        cleaned_text = clean_display_text(rem['text'])
                        if cleaned_text:
                            formatted_time = format_time(rem['time'])
                            msg_parts.append(f"{idx}. {cleaned_text} - {formatted_time}")
                
                if msg_parts:
                    # Format with proper line breaks for frontend display
                    # Double newline after header for better separation
                    full_message = "Here are your reminders:\n\n" + "\n".join(msg_parts)
                    self.speaker(full_message)
                else:
                    self.speaker("You have no reminders set.")
            else:
                self.speaker("You have no reminders set.")
                
        elif "set" in text or "add" in text or re.search(r'\bremind\s+(me|to|about)', text):
            # Extract time from command
            time_str, _ = self._parse_time(command)
            
            # Extract clean reminder text (remove command phrases and time)
            reminder_text = self._clean_reminder_text(command)
            
            # If no meaningful text left after cleaning, try to extract content
            if not reminder_text or reminder_text.lower() in ['for', 'a', 'an', 'the']:
                # Try to find the actual task/content using regex
                # Look for patterns like "for X", "to X", "about X"
                content_match = re.search(r'(?:to|for|about)\s+(.+?)(?:\s+at|\s+tomorrow|$)', command, re.IGNORECASE)
                if content_match:
                    reminder_text = content_match.group(1).strip()
                    # Remove time patterns from extracted content
                    reminder_text = re.sub(r'\b\d{1,2}:?\d{0,2}\s*(am|pm)?\b', '', reminder_text, flags=re.IGNORECASE).strip()
                
                # If still no text, use time as reminder description
                if not reminder_text or len(reminder_text) < 2:
                    try:
                        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                        reminder_text = f"Reminder at {dt.strftime('%I:%M %p')}"
                    except:
                        reminder_text = "Reminder"
            
            # Save as scheduled reminder
            reminder_id = self.storage.save_scheduled_reminder(reminder_text, time_str)
            
            # Format time for confirmation message (human-readable)
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                now = datetime.now()
                if dt.date() == now.date():
                    time_display = dt.strftime("%I:%M %p")  # "3:00 PM"
                elif dt.date() == (now + timedelta(days=1)).date():
                    time_display = f"tomorrow at {dt.strftime('%I:%M %p')}"  # "tomorrow at 10:00 AM"
                else:
                    time_display = dt.strftime("%B %d at %I:%M %p")  # "January 15 at 3:00 PM"
            except:
                time_display = time_str  # Fallback to raw time
            
            # Confirm reminder was set
            self.speaker(f"Reminder set for {time_display}: {reminder_text}")
                
        elif "delete" in text or "remove" in text or "clear" in text:
            # Check for "all" to delete everything
            if "all" in text:
                # Delete all reminders (both regular and scheduled)
                self.storage.delete_all_reminders()
                self.storage.delete_all_scheduled_reminders()
                self.speaker("All reminders have been deleted.")
            else:
                # Try to extract number/index from command
                number_match = re.search(r'\b(\d+)\b', text)
                if number_match:
                    index = int(number_match.group(1))
                    reminders = self.storage.load("reminders")
                    scheduled = self.storage.get_scheduled_reminders()
                    active_scheduled = [r for r in scheduled if not r.get("completed", False)]
                    
                    # Calculate which list the index belongs to
                    # Regular reminders are numbered first, then scheduled
                    num_regular = len(reminders)
                    
                    if 1 <= index <= num_regular:
                        # Delete from regular reminders
                        self.storage.delete_reminder_by_index(index)
                        self.speaker(f"Reminder {index} has been deleted.")
                    elif num_regular < index <= num_regular + len(active_scheduled):
                        # Delete from scheduled reminders (adjust index)
                        scheduled_index = index - num_regular
                        if self.storage.delete_scheduled_reminder_by_index(scheduled_index):
                            self.speaker(f"Reminder {index} has been deleted.")
                        else:
                            self.speaker(f"Reminder {index} not found.")
                    else:
                        self.speaker(f"Reminder {index} not found.")
                else:
                    # If no number specified, delete all (safety: explicit "all" not required)
                    self.storage.delete_all_reminders()
                    self.storage.delete_all_scheduled_reminders()
                    self.speaker("All reminders have been deleted.")
                
        elif "how many" in text or "count" in text:
            # Count total reminders (regular + active scheduled)
            reminders = self.storage.load("reminders")
            scheduled = self.storage.get_scheduled_reminders()
            active_scheduled = [r for r in scheduled if not r.get("completed", False)]
            total = len(reminders) + len(active_scheduled)
            
            # Provide user-friendly count message
            if total == 0:
                self.speaker("You have no reminders.")
            elif total == 1:
                self.speaker("You have 1 reminder.")
            else:
                self.speaker(f"You have {total} reminders.")
        return True
