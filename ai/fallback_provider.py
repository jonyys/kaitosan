from ai.groq_provider import GroqProvider
from ai.gemini_provider import GeminiProvider

class FallbackProvider:
    def __init__(self, model="openai/gpt-oss-120b"):
        self.groq = GroqProvider(model=model)
        self.gemini = GeminiProvider()

    def completar(self, mensajes: list, max_tokens: int = None,
                  response_format: dict = None, temperature: float = None,
                  strict: bool = False, reasoning_effort: str = None) -> str:
        try:
            return self.groq.completar(mensajes, max_tokens=max_tokens,
                                       response_format=response_format,
                                       temperature=temperature,
                                       strict=strict,
                                       reasoning_effort=reasoning_effort)
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