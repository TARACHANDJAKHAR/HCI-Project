import json
import os

class StorageManager:
    def __init__(self, filename="assistant_data.json"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                json.dump({"reminders": [], "emergency_contacts": [], "profile": {}, "scheduled_reminders": []}, f, indent=4)

    def load(self, key):
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get(key, [])

    def save(self, key, value):
        with open(self.filename, "r") as f:
            data = json.load(f)
        data.setdefault(key, []).append(value)
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def add_contact(self, name, phone):
        contacts = self.load("emergency_contacts")
        if any(c["phone"] == phone for c in contacts):
            return False
        contacts.append({"name": name, "phone": phone})
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["emergency_contacts"] = contacts
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)
        return True

    def remove_contact(self, phone):
        contacts = self.load("emergency_contacts")
        contacts = [c for c in contacts if c["phone"] != phone]
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["emergency_contacts"] = contacts
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def get_contacts(self):
        contacts = self.load("emergency_contacts")
        return [c["phone"] for c in contacts]

    def get_profile(self):
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get("profile", {})

    def set_profile(self, profile: dict):
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["profile"] = profile or {}
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def save_scheduled_reminder(self, reminder_text: str, reminder_time: str, reminder_id: str = None):
        """Save reminder with scheduled time. reminder_time format: 'HH:MM' or 'YYYY-MM-DD HH:MM'"""
        import uuid
        with open(self.filename, "r") as f:
            data = json.load(f)
        
        scheduled = data.get("scheduled_reminders", [])
        if reminder_id is None:
            reminder_id = str(uuid.uuid4())[:8]
        
        scheduled.append({
            "id": reminder_id,
            "text": reminder_text,
            "time": reminder_time,
            "completed": False
        })
        data["scheduled_reminders"] = scheduled
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)
        return reminder_id

    def get_scheduled_reminders(self):
        """Get all scheduled reminders"""
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get("scheduled_reminders", [])

    def mark_reminder_completed(self, reminder_id: str):
        """Mark a reminder as completed"""
        with open(self.filename, "r") as f:
            data = json.load(f)
        scheduled = data.get("scheduled_reminders", [])
        for r in scheduled:
            if r.get("id") == reminder_id:
                r["completed"] = True
                break
        data["scheduled_reminders"] = scheduled
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def delete_all_reminders(self):
        """Delete all regular reminders"""
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["reminders"] = []
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def delete_all_scheduled_reminders(self):
        """Delete all scheduled reminders"""
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["scheduled_reminders"] = []
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def delete_reminder_by_index(self, index: int):
        """Delete a regular reminder by index (1-based)"""
        reminders = self.load("reminders")
        if 1 <= index <= len(reminders):
            reminders.pop(index - 1)
            with open(self.filename, "r") as f:
                data = json.load(f)
            data["reminders"] = reminders
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=4)
            return True
        return False

    def delete_scheduled_reminder_by_index(self, index: int):
        """Delete a scheduled reminder by index (1-based, only active ones)"""
        scheduled = self.get_scheduled_reminders()
        active = [r for r in scheduled if not r.get("completed", False)]
        if 1 <= index <= len(active):
            reminder_id = active[index - 1]["id"]
            scheduled = [r for r in scheduled if r.get("id") != reminder_id]
            with open(self.filename, "r") as f:
                data = json.load(f)
            data["scheduled_reminders"] = scheduled
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=4)
            return True
        return False

