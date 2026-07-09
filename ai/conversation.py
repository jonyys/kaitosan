from ai.prompts import SYSTEM_PROMPT


class Conversation:

    def __init__(self):

        self._messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    def add_user(self, text):

        self._messages.append(
            {
                "role": "user",
                "content": text
            }
        )

    def add_assistant(self, text):

        self._messages.append(
            {
                "role": "assistant",
                "content": text
            }
        )

    def get_messages(self):

        return self._messages