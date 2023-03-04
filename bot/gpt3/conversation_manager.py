# -*- coding: utf-8 -*-

import json


class ConversationManager():
    def __init__(self):
        self.conversations = {}

    def add_conversation(self, key: str, history: list = []) -> None:
        self.conversations[key] = history

    def get_conversation(self, key: str) -> list:
        if key not in self.conversations:
            self.add_conversation(key)

        return self.conversations[key]

    def remove_conversation(self, key: str) -> None:
        """
        Removes the history list from the conversations dict with the id as the key
        """
        del self.conversations[key]

    def __str__(self) -> str:
        """
        Creates a JSON string of the conversations
        """
        return json.dumps(self.conversations)

    def save(self, file: str) -> None:
        """
        Saves the conversations to a JSON file
        """
        with open(file, 'w', encoding='utf-8') as f:
            f.write(str(self))

    def load(self, file: str) -> None:
        """
        Loads the conversations from a JSON file
        """
        with open(file, encoding='utf-8') as f:
            self.conversations = json.loads(f.read())
