from ai.groq_provider import GroqProvider
from ai.gemini_provider import GeminiProvider

class FallbackProvider:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.groq = GroqProvider(model=model)
        self.gemini = GeminiProvider()

    def completar(self, mensajes: list, max_tokens: int = None,
                  response_format: dict = None, temperature: float = None,
                  strict: bool = False) -> str:
        try:
            return self.groq.completar(mensajes, max_tokens=max_tokens,
                                       response_format=response_format,
                                       temperature=temperature,
                                       strict=strict)
        except Exception as e:
            if strict:
                raise  # no hay fallback aceptable — dejar que el caller decida
            print(f"⚠️ Groq falló definitivamente: {e}")
            print("🔄 Cambiando a Gemini...")
            return self.gemini.completar(mensajes, max_tokens=max_tokens,
                                         temperature=temperature)

    def completar_tools(self, mensajes: list, tools: list) -> tuple:
        try:
            return self.groq.completar_tools(mensajes, tools)
        except Exception as e:
            print(f"⚠️ Groq tools falló: {e}, usando Gemini sin herramientas")
            content = self.gemini.completar(mensajes)
            return content, None