"""Proveedor del modo sensei.

- Turnos (y resumen básico de cierre): si hay `OPENROUTER_API_KEY`, van primero
  a OpenRouter (`OPENROUTER_MODELOS_SENSEI` en orden). Es pago-por-uso y da
  modelos fuertes en seguir el prompt (Qwen, GLM) sin el rate limit por
  tokens/min del tier gratis. Si OpenRouter falla (o no está configurado) se cae
  al camino anterior: Gemini (con `SENSEI_TURNOS_GEMINI=1`, rotando modelos ante
  429) y por último Groq gpt-oss-120b.
- Extractor de cierre (`strict=True`): SIEMPRE Groq gpt-oss-120b. Es donde la
  calidad del JSON y del japonés no es negociable; si Groq no está, el guardrail
  de `profesor.py` guarda solo el resumen y no toca `can_do_progreso`.

Modelos de OpenRouter: `OPENROUTER_MODELOS_SENSEI` (env, coma-separado).
Modelos de Gemini: `gemini_seleccion()` (Ajustes → Modelos).
Modelo de la reserva Groq: `groq_seleccion()["sensei"]`, y `ProfesorJapones.
_resolver_modelo()` lo reajusta en cada sesión vía `self.provider.groq`.
"""

from ai.fallback_provider import FallbackProvider
from ai.gemini_provider import GeminiProvider
from ai.openrouter_provider import OpenRouterProvider
from core.config import (
    OPENROUTER_API_KEY, SENSEI_TURNOS_GEMINI, gemini_seleccion, groq_seleccion,
)


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
        self.openrouter = OpenRouterProvider() if OPENROUTER_API_KEY else None
        if SENSEI_TURNOS_GEMINI:
            sel = gemini_seleccion()
            modelos = [sel["sensei"]] + [
                m for m in sel.get("reservas", []) if m and m != sel["sensei"]
            ]
            self.gemini = [GeminiProvider(model=m) for m in modelos]
        else:
            self.gemini = []  # turnos directos a Groq
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

        # Turnos y resumen básico: OpenRouter primero (si hay API key), y si
        # falla se sigue con Gemini → Groq como antes.
        if self.openrouter:
            try:
                return self.openrouter.completar(
                    mensajes, max_tokens=max_tokens, response_format=response_format,
                    temperature=temperature, reasoning_effort=reasoning_effort,
                )
            except Exception as e:  # noqa: BLE001
                print(f"⚠️ OpenRouter falló ({type(e).__name__}: {e}) → Gemini/Groq")

        # Gemini primario → reservas Gemini → Groq.
        # Sin Gemini configurado (SENSEI_TURNOS_GEMINI=0) van directos a Groq.
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
            if self.gemini:
                print("⚠️ Todos los modelos Gemini en rate limit → Groq")

        return self.reserva.completar(
            mensajes, max_tokens=max_tokens, response_format=response_format,
            temperature=temperature, reasoning_effort=reasoning_effort,
        )
