from groq import Groq
from core.config import GROQ_API_KEY, DEFAULT_MODEL, MAX_TOKENS

class GroqProvider:
    def __init__(self, model=DEFAULT_MODEL):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = model

    def completar(self, mensajes: list) -> str:
        """Llama a la API de Groq y devuelve la respuesta"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=mensajes,
                max_tokens=MAX_TOKENS
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Error en Groq API: {e}")
            raise e