from ai.groq_provider import GroqProvider
from ai.gemini_provider import GeminiProvider

class FallbackProvider:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.groq = GroqProvider(model=model)
        self.gemini = GeminiProvider()

    def completar(self, mensajes: list) -> str:
        try:
            return self.groq.completar(mensajes)
        except Exception as e:
            print(f"⚠️ Groq falló definitivamente: {e}")
            print("🔄 Cambiando a Gemini...")
            return self.gemini.completar(mensajes)