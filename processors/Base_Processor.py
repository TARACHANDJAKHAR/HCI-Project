class BaseProcessor:
    keywords = []

    def __init__(self, speaker, storage=None):
        self.speaker = speaker
        self.storage = storage

    def match(self, command: str) -> bool:
        return any(keyword in command for keyword in self.keywords)

    def handle(self, command: str):
        raise NotImplementedError
