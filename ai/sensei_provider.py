"""Proveedor del modo sensei: Gemini (con rotación) primero, Groq de reserva.

- Turnos (y resumen básico de cierre): van a Gemini. Se prueba el modelo
  primario y, si da rate limit (429), se rota a las `reservas` en orden. El free
  tier de Gemini limita a ~20 req/día POR MODELO, así que rotar entre varios
  flash multiplica el aforo diario. Si TODOS los Gemini fallan, cae a Groq
  gpt-oss-120b.
- Extractor de cierre (`strict=True`): SIEMPRE Groq gpt-oss-120b. Es donde la
  calidad del JSON y del japonés no es negociable; si Groq no está, el guardrail
  de `profesor.py` guarda solo el resumen y no toca `can_do_progreso`.

Modelos de Gemini: `gemini_seleccion()` (Ajustes → Modelos).
Modelo de la reserva Groq: `groq_seleccion()["sensei"]`, y `ProfesorJapones.
_resolver_modelo()` lo reajusta en cada sesión vía `self.provider.groq`.
"""

from ai.fallback_provider import FallbackProvider
from ai.gemini_provider import GeminiProvider
from core.config import gemini_seleccion, groq_seleccion


def _es_rate_limit(e: Exception) -> bool:
    s = str(e).lower()
    return (
        "429" in s
        or "resourceexhausted" in type(e).__name__.lower()
        or "quota" in s
        or "rate limit" in s
        or "rate_limit" in s
    )


class SenseiProvider:

    def __init__(self):
        sel = gemini_seleccion()
        modelos = [sel["sensei"]] + [
            m for m in sel.get("reservas", []) if m and m != sel["sensei"]
        ]
        self.gemini = [GeminiProvider(model=m) for m in modelos]
        self.reserva = FallbackProvider(model=groq_seleccion()["sensei"])
        # ProfesorJapones._resolver_modelo() hace self.provider.groq.model = ...
        self.groq = self.reserva.groq

    def completar(self, mensajes, max_tokens=None, response_format=None,
                  temperature=None, strict=False, reasoning_effort=None):
        # Extractor de cierre: solo Groq. strict=True hace que FallbackProvider
        # lance si el modelo fuerte no está (lo recoge el guardrail).
        if strict:
            return self.reserva.completar(
                mensajes, max_tokens=max_tokens, response_format=response_format,
                temperature=temperature, strict=True, reasoning_effort=reasoning_effort,
            )

        # Turnos y resumen básico: Gemini primario → reservas Gemini → Groq.
        for gp in self.gemini:
            try:
                return gp.completar(
                    mensajes, max_tokens=max_tokens, temperature=temperature,
                    raise_on_error=True,
                )
            except Exception as e:  # noqa: BLE001
                if _es_rate_limit(e):
                    print(f"⚠️ Gemini {gp.model_id}: rate limit → siguiente modelo")
                    continue
                # Fallo no-429 (respuesta vacía, red…): rotar de modelo Gemini no
                # ayudaría; a la reserva Groq directamente.
                print(f"⚠️ Gemini {gp.model_id} falló ({type(e).__name__}) → Groq")
                break
        else:
            print("⚠️ Todos los modelos Gemini en rate limit → Groq")

        return self.reserva.completar(
            mensajes, max_tokens=max_tokens, response_format=response_format,
            temperature=temperature, reasoning_effort=reasoning_effort,
        )
