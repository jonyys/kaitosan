"""Proveedor del modo sensei: Gemini primero, Groq de reserva.

- Turnos (y resumen básico de cierre): van a Gemini. Su free tier tiene TPM
  holgado y en conversación da mejores resultados que gpt-oss. Si Gemini falla
  (429 / red / respuesta vacía), caen a Groq gpt-oss-120b.
- Extractor de cierre (`strict=True`): SIEMPRE Groq gpt-oss-120b. Es donde la
  calidad del JSON y del japonés no es negociable; si Groq no está, el guardrail
  de `profesor.py` guarda solo el resumen y no toca `can_do_progreso`.

Modelo de Gemini: `gemini_seleccion()["sensei"]` (Ajustes → Modelos).
Modelo de la reserva Groq: `groq_seleccion()["sensei"]`, y `ProfesorJapones.
_resolver_modelo()` lo reajusta en cada sesión vía `self.provider.groq`.
"""

from ai.fallback_provider import FallbackProvider
from ai.gemini_provider import GeminiProvider
from core.config import groq_seleccion


class SenseiProvider:

    def __init__(self):
        self.gemini = GeminiProvider(rol="sensei")
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

        # Turnos y resumen básico: Gemini primero, Groq si falla.
        try:
            return self.gemini.completar(
                mensajes, max_tokens=max_tokens, temperature=temperature,
                raise_on_error=True,
            )
        except Exception as e:  # noqa: BLE001 — cualquier fallo de Gemini → reserva
            print(f"⚠️ Gemini falló en el turno del sensei ({type(e).__name__}); "
                  f"reserva → Groq")
            return self.reserva.completar(
                mensajes, max_tokens=max_tokens, response_format=response_format,
                temperature=temperature, reasoning_effort=reasoning_effort,
            )
