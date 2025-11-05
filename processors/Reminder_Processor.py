from .Base_Processor import BaseProcessor

class ReminderProcessor(BaseProcessor):
    keywords = ["reminder", "meds", "medicine", "water", "appointment"]

    def handle(self, command: str):
        text = command.lower()
        if "set" in text or "add" in text:
            reminder = command.replace("set reminder", "").strip()
            self.storage.save("reminders", reminder)
            self.speaker(f"Reminder saved: {reminder}")
        elif "list" in text or "show" in text:
            reminders = self.storage.load("reminders")
            if reminders:
                self.speaker("Your reminders are: " + ", ".join(reminders))
            else:
                self.speaker("You have no reminders.")
        elif "how many" in text or "count" in text:
            reminders = self.storage.load("reminders")
            n = len(reminders)
            if n == 0:
                self.speaker("You have no reminders.")
            elif n == 1:
                self.speaker("You have 1 reminder.")
            else:
                self.speaker(f"You have {n} reminders.")
        return True