"""Proveedor del modo sensei.

- Turnos (y resumen básico de cierre): si hay `OPENROUTER_API_KEY`, van a
  OpenRouter (`openrouter_modelos_sensei()` en orden). Es pago-por-uso y da
  modelos fuertes en seguir el prompt (Qwen, GLM) sin el rate limit por
  tokens/min del tier gratis. Si OpenRouter falla del todo (o no está
  configurado), se cae a Groq `gpt-oss-120b` como último recurso.
- Extractor de cierre (`strict=True`): SIEMPRE Groq gpt-oss-120b. Es donde la
  calidad del JSON y del japonés no es negociable; si Groq no está, el guardrail
  de `profesor.py` guarda solo el resumen y no toca `can_do_progreso`.

Modelos de OpenRouter: `openrouter_modelos_sensei()` (Ajustes → Modelos).
"""

from ai.fallback_provider import FallbackProvider
from ai.openrouter_provider import OpenRouterProvider
from core.config import OPENROUTER_API_KEY, groq_seleccion


class SenseiProvider:

    def __init__(self):
        self.openrouter = OpenRouterProvider() if OPENROUTER_API_KEY else None
        self.reserva = FallbackProvider(model=groq_seleccion()["sensei"])
        # `getattr(provider, "groq", None)` sigue funcionando por si algo lo mira.
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

        # Turnos y resumen básico: OpenRouter primero (si hay API key); si falla,
        # Groq gpt-oss-120b de reserva.
        if self.openrouter:
            try:
                return self.openrouter.completar(
                    mensajes, max_tokens=max_tokens, response_format=response_format,
                    temperature=temperature, reasoning_effort=reasoning_effort,
                )
            except Exception as e:  # noqa: BLE001
                print(f"⚠️ OpenRouter falló ({type(e).__name__}: {e}) → Groq")

        return self.reserva.completar(
            mensajes, max_tokens=max_tokens, response_format=response_format,
            temperature=temperature, reasoning_effort=reasoning_effort,
        )
