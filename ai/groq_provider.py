from groq import Groq

from core.config import (
    GROQ_API_KEY,
    DEFAULT_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
)


class GroqProvider:

    def __init__(self, model=DEFAULT_MODEL):

        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = model

    def stream_chat(self, messages):

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )