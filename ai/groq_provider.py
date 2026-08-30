from groq import Groq
from core.config import (
    GROQ_API_KEY, DEFAULT_MODEL, MODEL_SENSEI, MAX_TOKENS, TEMPERATURE,
    MODELOS_ALTERNATIVOS, MODELOS_TOOLS, groq_seleccion,
)
from core.token_tracker import TokenTracker


def _seleccion_validada() -> dict:
    """`config.groq_seleccion()` descartando los modelos que ya no están activos
    en la API (retirados / renombrados) — PLAN_AJUSTES §5 nota "Modelos de Groq".

    Si no se puede consultar la lista real (sin red o sin API key) se devuelve
    la selección tal cual: el `_saltar_modelo()` de abajo cubre el caso en
    caliente cuando un modelo responde `decommissioned` / `model_not_found`.
    """
    sel = groq_seleccion()
    try:
        from core.system_settings import groq_modelos
        ids = {m["id"] for m in groq_modelos()}
    except Exception:
        ids = set()
    if not ids:
        return sel

    if sel["principal"] not in ids and DEFAULT_MODEL in ids:
        sel["principal"] = DEFAULT_MODEL
    if sel["sensei"] not in ids and MODEL_SENSEI in ids:
        sel["sensei"] = MODEL_SENSEI
    sel["alternativos"] = (
        [m for m in sel["alternativos"] if m in ids]
        or [m for m in MODELOS_ALTERNATIVOS if m in ids]
        or sel["alternativos"]
    )
    sel["tools"] = (
        [m for m in sel["tools"] if m in ids]
        or [m for m in MODELOS_TOOLS if m in ids]
        or sel["tools"]
    )
    return sel


class GroqProvider:
    def __init__(self, model=None):
        self.client = Groq(api_key=GROQ_API_KEY, max_retries=0)
        sel = _seleccion_validada()
        # `model` explícito (p.ej. el sensei) manda; si no, el principal de Ajustes.
        self.model = model or sel["principal"]
        self.modelos_alternativos = sel["alternativos"]
        # Modelos capaces de manejar tool calls correctamente
        self.modelos_tools = sel["tools"]
        self.tracker = TokenTracker()

    @staticmethod
    def _saltar_modelo(e: Exception) -> bool:
        """True si el error indica que este modelo no está disponible y debe probarse el siguiente."""
        s = str(e).lower()
        return (
            "429" in str(e) or
            "rate_limit" in s or
            "decommissioned" in s or
            "model_not_active" in s or
            "model_not_found" in s or
            "not supported" in s
        )

    def completar(self, mensajes: list, max_tokens: int = None,
                  response_format: dict = None, temperature: float = None,
                  strict: bool = False, reasoning_effort: str = None) -> str:
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
                # reasoning_effort solo lo aceptan los modelos gpt-oss; en otros
                # daría 400, así que lo filtramos por nombre.
                if reasoning_effort and "gpt-oss" in modelo:
                    kwargs["reasoning_effort"] = reasoning_effort
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
                if self._saltar_modelo(e):
                    if strict:
                        raise Exception(f"Modelo {modelo} no disponible — extracción pospuesta")
                    print(f"⚠️ {modelo} no disponible ({type(e).__name__}), probando otro...")
                    continue
                else:
                    raise e

        raise Exception("Todos los modelos fallaron")

    @staticmethod
    def _es_error_tool_call(e: Exception) -> bool:
        """True cuando el modelo no puede manejar tool calls en este contexto."""
        s = str(e).lower()
        return (
            "tool_use_failed" in s or
            "failed to call a function" in s or
            "failed to render" in s or
            "harmonyerror" in s or
            "tools should have a name" in s or
            "failed to template" in s
        )

    def completar_tools(self, mensajes: list, tools: list) -> tuple:
        """
        Llamada con soporte de herramientas.
        Retorna (content, tool_calls) — tool_calls es None si el modelo responde directamente.
        Solo usa modelos_tools (70B+) porque los modelos pequeños no formatean bien las tool calls.
        """
        modelos_a_probar = [m for m in self.modelos_tools if m == self.model] + \
                           [m for m in self.modelos_tools if m != self.model]

        ultimo_error = None
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
                    print(f"⚠️ Usando modelo alternativo para tools: {modelo}")

                message = response.choices[0].message
                return message.content, message.tool_calls

            except Exception as e:
                if self._saltar_modelo(e):
                    print(f"⚠️ {modelo} no disponible ({type(e).__name__}), probando otro...")
                    ultimo_error = e
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
                        ultimo_error = e
                        continue
                elif self._es_error_tool_call(e):
                    # El modelo intentó llamar la herramienta pero con formato incorrecto
                    # → saltar al siguiente modelo con capacidad de tools
                    print(f"⚠️ {modelo} generó tool call con formato incorrecto, probando otro...")
                    ultimo_error = e
                    continue
                else:
                    print(f"❌ Error en {modelo} con tools: {e}")
                    raise e

        raise Exception(f"Todos los modelos con tools fallaron. Último error: {ultimo_error}")