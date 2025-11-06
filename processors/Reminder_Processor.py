from .Base_Processor import BaseProcessor
import re
from datetime import datetime, timedelta

class ReminderProcessor(BaseProcessor):
    keywords = ["reminder", "meds", "medicine", "water", "appointment", "delete", "remove", "clear"]

    def _parse_time(self, command: str):
        """Extract time from command. Returns (time_str, is_today)"""
        text = command.lower()
        
        # Patterns: "at 3pm", "at 15:30", "at 3:30 pm", "tomorrow at 10am", "12:15", "1:13 am"
        time_patterns = [
            r'at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?',
            r'at\s+(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # Matches "12:15" or "1:13 am"
            r'(\d{1,2})\s*(am|pm)',  # Matches "3 pm" or "12am"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                
                # Handle AM/PM - check all groups for am/pm
                ampm = None
                for g in groups:
                    if g and g.lower() in ['am', 'pm']:
                        ampm = g.lower()
                        break
                
                if ampm:
                    if ampm == 'pm' and hour < 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                # Ensure hour is valid (0-23) and minute is valid (0-59)
                hour = hour % 24
                minute = min(59, max(0, minute))
                
                # Check if tomorrow
                is_tomorrow = "tomorrow" in text
                if is_tomorrow:
                    target_date = datetime.now() + timedelta(days=1)
                else:
                    target_date = datetime.now()
                    # If no AM/PM specified and hour > 12, assume it's already 24-hour format
                    # Otherwise, if hour is reasonable (1-12), assume PM if it's afternoon context
                    if not ampm and hour <= 12:
                        # If current time is before noon and hour is 1-11, could be AM or PM
                        # Default to PM for afternoon hours (1-6), AM for morning (7-11)
                        current_hour = datetime.now().hour
                        if current_hour >= 12 and hour <= 6:
                            hour += 12  # Assume PM
                            hour = hour % 24
                
                # Create datetime with the parsed hour and minute
                target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                time_str = target_datetime.strftime("%Y-%m-%d %H:%M")
                return time_str, is_tomorrow
        
        # Default: if no time found, assume next hour
        next_hour = datetime.now() + timedelta(hours=1)
        return next_hour.strftime("%Y-%m-%d %H:%M"), False

    def _clean_reminder_text(self, command: str):
        """Extract clean reminder text by removing command phrases and time patterns"""
        text = command
        
        # Remove common command phrases (case insensitive)
        patterns_to_remove = [
            r'set\s+(a\s+)?reminder\s+(for\s+)?',
            r'add\s+(a\s+)?reminder\s+(for\s+)?',
            r'remind\s+(me\s+)?(to\s+)?(about\s+)?',
            r'reminder\s+(for\s+)?',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove time patterns
        text = re.sub(r'\b(at|tomorrow|am|pm)\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d{1,2}:?\d{0,2}\s*(am|pm)?\b', '', text, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def handle(self, command: str):
        text = command.lower()
        
        # Check for list/show FIRST (before checking for set/add)
        if "list" in text or "show" in text:
            reminders = self.storage.load("reminders")
            scheduled = self.storage.get_scheduled_reminders()
            
            # Filter active scheduled reminders
            active_scheduled = [r for r in scheduled if not r.get("completed", False)]
            
            # Format time for display (convert YYYY-MM-DD HH:MM to readable format)
            def format_time(time_str):
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    now = datetime.now()
                    if dt.date() == now.date():
                        return dt.strftime("%I:%M %p")
                    elif dt.date() == (now + timedelta(days=1)).date():
                        return f"Tomorrow at {dt.strftime('%I:%M %p')}"
                    else:
                        return dt.strftime("%B %d at %I:%M %p")
                except:
                    return time_str
            
            # Clean reminder text for display
            def clean_display_text(text):
                """Remove command phrases from reminder text for display"""
                if not text:
                    return text
                cleaned = text
                # Remove common command phrases
                patterns = [
                    r'^set\s+(a\s+)?reminder\s+(for\s+)?',
                    r'^add\s+(a\s+)?reminder\s+(for\s+)?',
                    r'^remind\s+(me\s+)?(to\s+)?(about\s+)?',
                ]
                for pattern in patterns:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
                return cleaned.strip()
            
            if reminders or active_scheduled:
                msg_parts = []
                
                # Add regular reminders (clean them up)
                if reminders:
                    for idx, rem in enumerate(reminders, 1):
                        cleaned_rem = clean_display_text(rem)
                        if cleaned_rem:  # Only add if there's actual content
                            msg_parts.append(f"{idx}. {cleaned_rem}")
                
                # Add scheduled reminders (clean them up)
                if active_scheduled:
                    start_num = len([r for r in reminders if clean_display_text(r)]) + 1
                    for idx, rem in enumerate(active_scheduled, start_num):
                        cleaned_text = clean_display_text(rem['text'])
                        if cleaned_text:
                            formatted_time = format_time(rem['time'])
                            msg_parts.append(f"{idx}. {cleaned_text} - {formatted_time}")
                
                if msg_parts:
                    # Format with proper line breaks for frontend display
                    # Use double newline for better separation, or format as HTML-friendly
                    full_message = "Here are your reminders:\n\n" + "\n".join(msg_parts)
                    self.speaker(full_message)
                else:
                    self.speaker("You have no reminders set.")
            else:
                self.speaker("You have no reminders set.")
                
        elif "set" in text or "add" in text or re.search(r'\bremind\s+(me|to|about)', text):
            # Try to extract time
            time_str, _ = self._parse_time(command)
            
            # Extract clean reminder text
            reminder_text = self._clean_reminder_text(command)
            
            # If no text left after cleaning, try to extract meaningful content
            if not reminder_text or reminder_text.lower() in ['for', 'a', 'an', 'the']:
                # Try to find the actual task/content
                # Look for common reminder patterns
                content_match = re.search(r'(?:to|for|about)\s+(.+?)(?:\s+at|\s+tomorrow|$)', command, re.IGNORECASE)
                if content_match:
                    reminder_text = content_match.group(1).strip()
                    # Remove time patterns from extracted content
                    reminder_text = re.sub(r'\b\d{1,2}:?\d{0,2}\s*(am|pm)?\b', '', reminder_text, flags=re.IGNORECASE).strip()
                
                if not reminder_text or len(reminder_text) < 2:
                    # If still no text, use time as reminder
                    try:
                        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                        reminder_text = f"Reminder at {dt.strftime('%I:%M %p')}"
                    except:
                        reminder_text = "Reminder"
            
            # Save as scheduled reminder
            reminder_id = self.storage.save_scheduled_reminder(reminder_text, time_str)
            
            # Format time for confirmation message
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                now = datetime.now()
                if dt.date() == now.date():
                    time_display = dt.strftime("%I:%M %p")
                elif dt.date() == (now + timedelta(days=1)).date():
                    time_display = f"tomorrow at {dt.strftime('%I:%M %p')}"
                else:
                    time_display = dt.strftime("%B %d at %I:%M %p")
            except:
                time_display = time_str
            
            self.speaker(f"Reminder set for {time_display}: {reminder_text}")
                
        elif "delete" in text or "remove" in text or "clear" in text:
            # Check for "all" or "delete all"
            if "all" in text:
                # Delete all reminders (both regular and scheduled)
                self.storage.delete_all_reminders()
                self.storage.delete_all_scheduled_reminders()
                self.speaker("All reminders have been deleted.")
            else:
                # Try to extract number/index
                number_match = re.search(r'\b(\d+)\b', text)
                if number_match:
                    index = int(number_match.group(1))
                    reminders = self.storage.load("reminders")
                    scheduled = self.storage.get_scheduled_reminders()
                    active_scheduled = [r for r in scheduled if not r.get("completed", False)]
                    
                    # Calculate which list the index belongs to
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
                    # If no number specified, delete all
                    self.storage.delete_all_reminders()
                    self.storage.delete_all_scheduled_reminders()
                    self.speaker("All reminders have been deleted.")
                
        elif "how many" in text or "count" in text:
            reminders = self.storage.load("reminders")
            scheduled = self.storage.get_scheduled_reminders()
            active_scheduled = [r for r in scheduled if not r.get("completed", False)]
            total = len(reminders) + len(active_scheduled)
            
            if total == 0:
                self.speaker("You have no reminders.")
            elif total == 1:
                self.speaker("You have 1 reminder.")
            else:
                self.speaker(f"You have {total} reminders.")
        return True