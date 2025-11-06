"""
Notification Scheduler - Background service for reminder notifications.

Runs in a separate daemon thread and checks for due reminders every 10 seconds.
When a reminder's time arrives, it calls the notify_callback function
to trigger the notification.

This runs independently of the main Flask application, allowing
notifications to work even when no API requests are being made.
"""

import threading
import time
from datetime import datetime
from Storage_Manager import StorageManager


class NotificationScheduler:
    """
    Background scheduler that checks for due reminders and triggers notifications.
    
    Runs in a daemon thread so it doesn't block application shutdown.
    Checks every 10 seconds for reminders that are due.
    """
    
    def __init__(self, storage: StorageManager, notify_callback):
        """
        Initialize the notification scheduler.
        
        Args:
            storage: StorageManager instance to read scheduled reminders
            notify_callback: Function to call when a reminder is due.
                            Should accept (reminder_text: str, reminder_id: str)
        """
        self.storage = storage
        self.notify_callback = notify_callback  # Function to call when reminder is due
        self.running = False  # Flag to control scheduler loop
        self.thread = None    # Background thread reference
    
    def start(self):
        """
        Start the scheduler in a background daemon thread.
        
        Daemon threads automatically terminate when main program exits,
        so we don't need to explicitly stop it on shutdown.
        """
        if self.running:
            return  # Already running, don't start again
        
        self.running = True
        # Create daemon thread (terminates when main program exits)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("Notification scheduler started")
    
    def stop(self):
        """
        Stop the scheduler gracefully.
        
        Sets running flag to False and waits for thread to finish
        (with 2 second timeout to avoid hanging).
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish
    
    def _run(self):
        """
        Main scheduler loop: check every 10 seconds for due reminders.
        
        This method runs in the background thread. It:
        1. Loads all scheduled reminders
        2. Checks each one to see if its time has arrived
        3. Triggers notification if time is within window
        4. Marks reminder as completed
        5. Sleeps for 10 seconds and repeats
        """
        while self.running:
            try:
                # Load all scheduled reminders from storage
                scheduled = self.storage.get_scheduled_reminders()
                now = datetime.now()
                
                # Check each reminder
                for reminder in scheduled:
                    # Skip completed reminders (already notified)
                    if reminder.get("completed", False):
                        continue
                    
                    try:
                        # Parse reminder time from string format
                        reminder_time = datetime.strptime(reminder["time"], "%Y-%m-%d %H:%M")
                        
                        # Calculate time difference in seconds
                        # Positive = future, negative = past
                        time_diff = (reminder_time - now).total_seconds()
                        
                        # Trigger if reminder time has arrived
                        # Window: -60 seconds (up to 1 minute late) to +10 seconds (10 seconds early)
                        # This accounts for the 10-second check interval
                        if -60 <= time_diff <= 10:
                            # Time to notify!
                            print(f"Triggering reminder: {reminder['text']} at {reminder['time']} (diff: {time_diff:.1f}s)")
                            
                            # Call the callback to trigger notification
                            self.notify_callback(reminder["text"], reminder["id"])
                            
                            # Mark as completed so it doesn't trigger again
                            self.storage.mark_reminder_completed(reminder["id"])
                    except Exception as e:
                        # Log error but continue checking other reminders
                        print(f"Error processing reminder {reminder.get('id')}: {e}")
                
                # Sleep for 10 seconds before next check
                # This balances accuracy (frequent checks) with resource usage
                time.sleep(10)
            except Exception as e:
                # Log error but keep scheduler running
                print(f"Scheduler error: {e}")
                time.sleep(10)  # Still sleep to avoid tight error loop
