from groq import Groq
from core.config import GROQ_API_KEY, DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE
from core.token_tracker import TokenTracker


class GroqProvider:
    def __init__(self, model=DEFAULT_MODEL):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = model
        self.modelos_alternativos = [
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "mixtral-8x7b-32768"
        ]
        self.tracker = TokenTracker()

    def completar(self, mensajes: list, max_tokens: int = None,
                  response_format: dict = None, temperature: float = None,
                  strict: bool = False) -> str:
        """Intenta con el modelo principal y alternativos si hay rate limit.

        strict=True: solo usa el modelo principal — lanza excepción si hay rate
        limit en lugar de caer en alternativos. Úsalo cuando la calidad del modelo
        no es negociable (p.ej. extractor de sesión).
        """
        modelos_a_probar = [self.model] if strict else (
            [self.model] + [m for m in self.modelos_alternativos if m != self.model]
        )

        for modelo in modelos_a_probar:
            try:
                kwargs = {
                    "max_tokens": max_tokens or MAX_TOKENS,
                    "temperature": temperature if temperature is not None else TEMPERATURE,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                response = self.client.chat.completions.create(
                    model=modelo,
                    messages=mensajes,
                    **kwargs
                )

                try:
                    tokens_usados = response.usage.total_tokens
                    datos = self.tracker.añadir_tokens(modelo, tokens_usados)
                    total_modelo = datos["tokens"].get(modelo, 0)
                    total_hoy = sum(datos["tokens"].values())
                    print(f"📊 Tokens {modelo}: {tokens_usados} (hoy: {total_modelo} este modelo, {total_hoy} total)")
                except Exception as e:
                    print(f"⚠️ Error guardando tokens: {e}")
                    
                if modelo != self.model:
                    print(f"⚠️ Usando modelo alternativo: {modelo}")
                return response.choices[0].message.content
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    if strict:
                        raise Exception(f"Rate limit en modelo principal ({modelo}) — extracción pospuesta")
                    print(f"⚠️ Rate limit en {modelo}, probando otro...")
                    continue
                else:
                    raise e

        raise Exception("Todos los modelos fallaron por rate limit")

    def completar_tools(self, mensajes: list, tools: list) -> tuple:
        """
        Llamada con soporte de herramientas.
        Retorna (content, tool_calls) — tool_calls es None si el modelo responde directamente.
        """
        modelos_a_probar = [self.model] + [m for m in self.modelos_alternativos if m != self.model]

        for modelo in modelos_a_probar:
            try:
                response = self.client.chat.completions.create(
                    model=modelo,
                    messages=mensajes,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                )

                try:
                    tokens_usados = response.usage.total_tokens
                    datos = self.tracker.añadir_tokens(modelo, tokens_usados)
                    total_modelo = datos["tokens"].get(modelo, 0)
                    total_hoy = sum(datos["tokens"].values())
                    print(f"📊 Tokens {modelo}: {tokens_usados} (hoy: {total_modelo} este modelo, {total_hoy} total)")
                except Exception as e:
                    print(f"⚠️ Error guardando tokens: {e}")

                if modelo != self.model:
                    print(f"⚠️ Usando modelo alternativo: {modelo}")

                message = response.choices[0].message
                return message.content, message.tool_calls

            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    print(f"⚠️ Rate limit en {modelo}, probando otro...")
                    continue
                elif "does not support tool" in str(e).lower() or "tool use is not supported" in str(e).lower():
                    print(f"⚠️ {modelo} no soporta tools, respondiendo sin herramientas")
                    try:
                        response = self.client.chat.completions.create(
                            model=modelo,
                            messages=mensajes,
                            max_tokens=MAX_TOKENS,
                            temperature=TEMPERATURE,
                        )
                        return response.choices[0].message.content, None
                    except Exception:
                        continue
                else:
                    print(f"❌ Error en {modelo} con tools: {e}")
                    raise e

        raise Exception("Todos los modelos fallaron por rate limit")