from ai.groq_provider import GroqProvider
from ai.openrouter_provider import OpenRouterProvider
from core.config import OPENROUTER_API_KEY


class FallbackProvider:
    """Groq como primario; si Groq falla del todo (no rate limit puntual, sino
    caído / todos los modelos fuera), cae a OpenRouter — siempre que haya
    `OPENROUTER_API_KEY`. Sin key, se propaga el error de Groq.
    """

    def __init__(self, model=None):
        # model=None -> GroqProvider usa el modelo principal de Ajustes → Modelos.
        self.groq = GroqProvider(model=model)
        self._or = OpenRouterProvider() if OPENROUTER_API_KEY else None

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
            if strict or not self._or:
                raise  # sin fallback aceptable — que decida el caller
            print(f"⚠️ Groq falló definitivamente: {e}")
            print("🔄 Cambiando a OpenRouter…")
            return self._or.completar(mensajes, max_tokens=max_tokens,
                                      response_format=response_format,
                                      temperature=temperature,
                                      reasoning_effort=reasoning_effort)

    def completar_tools(self, mensajes: list, tools: list) -> tuple:
        try:
            return self.groq.completar_tools(mensajes, tools)
        except Exception as e:
            if not self._or:
                raise
            print(f"⚠️ Groq tools falló: {e}, respondiendo por OpenRouter sin herramientas")
            return self._or.completar(mensajes), None
