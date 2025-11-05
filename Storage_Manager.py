import json
import os

class StorageManager:
    def __init__(self, filename="assistant_data.json"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                json.dump({"reminders": [], "emergency_contacts": []}, f, indent=4)

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

