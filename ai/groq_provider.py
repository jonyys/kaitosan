from groq import Groq
from core.config import GROQ_API_KEY, DEFAULT_MODEL, MAX_TOKENS

class GroqProvider:
    def __init__(self, model=DEFAULT_MODEL):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = model
        self.modelos_alternativos = [
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "mixtral-8x7b-32768"
        ]

    def completar(self, mensajes: list) -> str:
        """Intenta con el modelo principal y alternativos si hay rate limit."""
        modelos_a_probar = [self.model] + [
            m for m in self.modelos_alternativos if m != self.model
        ]

        for modelo in modelos_a_probar:
            try:
                response = self.client.chat.completions.create(
                    model=modelo,
                    messages=mensajes,
                    max_tokens=MAX_TOKENS
                )
                if modelo != self.model:
                    print(f"⚠️ Usando modelo alternativo: {modelo}")
                return response.choices[0].message.content
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    print(f"⚠️ Rate limit en {modelo}, probando otro...")
                    continue
                else:
                    raise e

        raise Exception("Todos los modelos fallaron por rate limit")