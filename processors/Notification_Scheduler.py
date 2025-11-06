import threading
import time
from datetime import datetime
from Storage_Manager import StorageManager

class NotificationScheduler:
    def __init__(self, storage: StorageManager, notify_callback):
        self.storage = storage
        self.notify_callback = notify_callback  # Function to call when reminder is due
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler in background thread"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("Notification scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _run(self):
        """Main loop: check every 10 seconds for due reminders"""
        while self.running:
            try:
                scheduled = self.storage.get_scheduled_reminders()
                now = datetime.now()
                
                for reminder in scheduled:
                    if reminder.get("completed", False):
                        continue
                    
                    try:
                        reminder_time = datetime.strptime(reminder["time"], "%Y-%m-%d %H:%M")
                        # Calculate time difference in seconds
                        time_diff = (reminder_time - now).total_seconds()
                        
                        # Trigger if reminder time has arrived (within the last 60 seconds or up to 10 seconds ahead)
                        # This accounts for the 10-second check interval
                        if -60 <= time_diff <= 10:
                            # Time to notify!
                            print(f"Triggering reminder: {reminder['text']} at {reminder['time']} (diff: {time_diff:.1f}s)")
                            self.notify_callback(reminder["text"], reminder["id"])
                            self.storage.mark_reminder_completed(reminder["id"])
                    except Exception as e:
                        print(f"Error processing reminder {reminder.get('id')}: {e}")
                
                time.sleep(10)  # Check every 10 seconds for better accuracy
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(10)