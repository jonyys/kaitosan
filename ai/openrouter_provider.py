"""Proveedor OpenRouter para los TURNOS del modo sensei.

Por qué: el prompt del profesor es grande y cada turno rozaba el límite de
tokens/min del tier gratis de Groq/Gemini (429 constante). OpenRouter es
pago-por-uso y enruta a modelos fuertes en *seguir instrucciones* (Qwen, GLM),
que es el cuello de botella real del sensei. El extractor de cierre NO pasa por
aquí — sigue en Groq (ver `sensei_provider.SenseiProvider.completar`, rama
`strict`).

API compatible con OpenAI (`/chat/completions`). Se usa `requests` (ya es
dependencia) en vez del SDK de OpenAI para no añadir nada.

`OPENROUTER_MODELOS_SENSEI` se recorre en orden: el primero que responda gana;
rate limit / modelo caído / respuesta vacía → siguiente.
"""
import json

import requests

from core.config import (
    OPENROUTER_API_KEY, MAX_TOKENS, TEMPERATURE, openrouter_modelos_sensei,
)
from core.token_tracker import TokenTracker

_URL = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT = 60


class OpenRouterProvider:
    def __init__(self, modelos=None):
        # `modelos` explícito manda; si no, la lista guardada en Ajustes →
        # Modelos (o la de fábrica del .env si no se ha tocado).
        self.modelos = list(modelos or openrouter_modelos_sensei())
        self.tracker = TokenTracker()

    @staticmethod
    def _saltar_modelo(status: int, cuerpo: str) -> bool:
        """True si conviene pasar al siguiente modelo de la lista en vez de fallar."""
        s = (cuerpo or "").lower()
        return (
            status in (402, 404, 429, 502, 503) or
            "rate limit" in s or "rate_limit" in s or "quota" in s or
            "not found" in s or "no endpoints" in s or "no allowed providers" in s or
            # algún endpoint obliga a razonar y rechaza reasoning.enabled=false
            "reasoning is mandatory" in s or "cannot be disabled" in s
        )

    def completar(self, mensajes, max_tokens=None, response_format=None,
                  temperature=None, reasoning_effort=None) -> str:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY no configurada")
        if not self.modelos:
            raise RuntimeError("OpenRouter sin modelos configurados")

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "X-Title": "Kaitosan",
        }
        ultimo = None
        for modelo in self.modelos:
            payload = {
                "model": modelo,
                "messages": mensajes,
                "max_tokens": max_tokens or MAX_TOKENS,
                "temperature": temperature if temperature is not None else TEMPERATURE,
                # Enruta al endpoint más rápido de los que sirven el modelo (no al
                # más barato, que es lo que hace por defecto). Sin esto, gpt-oss y
                # glm caían a proveedores lentos: turnos de 10-30 s. En modelos de
                # un solo proveedor (qwen flash) no cambia nada.
                "provider": {"sort": "throughput"},
            }
            if response_format:
                payload["response_format"] = response_format
            # Razonamiento: `reasoning_effort` (= REASONING_EFFORT_SENSEI en los
            # turnos) vale para TODOS los modelos por igual. "off" (o vacío)
            # apaga el thinking; low|medium|high lo fija. Ojo: en qwen3.7-flash
            # cualquier valor distinto de "off" se dispara a 15-30 s/turno.
            ef = (reasoning_effort or "off").strip().lower()
            payload["reasoning"] = (
                {"enabled": False} if ef == "off" else {"effort": ef}
            )

            try:
                r = requests.post(_URL, headers=headers, json=payload, timeout=_TIMEOUT)
            except requests.RequestException as e:
                print(f"⚠️ OpenRouter {modelo} error de red ({type(e).__name__}), probando otro...")
                ultimo = e
                continue

            # Algún endpoint (glm-5.3-flash) rechaza con 400 que se toque el
            # razonamiento. En vez de descartar el modelo, se reintenta una vez
            # dejándole su comportamiento por defecto.
            if (r.status_code == 400 and "reasoning" in payload
                    and "reasoning" in r.text.lower()):
                print(f"⚠️ OpenRouter {modelo}: no acepta tocar reasoning, reintento sin el param")
                payload.pop("reasoning", None)
                try:
                    r = requests.post(_URL, headers=headers, json=payload, timeout=_TIMEOUT)
                except requests.RequestException as e:
                    print(f"⚠️ OpenRouter {modelo} error de red ({type(e).__name__}), probando otro...")
                    ultimo = e
                    continue

            if r.status_code != 200:
                if self._saltar_modelo(r.status_code, r.text):
                    print(f"⚠️ OpenRouter {modelo} no disponible ({r.status_code}), probando otro...")
                    ultimo = Exception(f"{r.status_code}: {r.text[:200]}")
                    continue
                raise Exception(f"OpenRouter {modelo} {r.status_code}: {r.text[:300]}")

            data = r.json()
            clave = f"openrouter/{modelo}"
            try:
                uso = data.get("usage", {}) or {}
                tokens = int(uso.get("total_tokens", 0) or 0)
                # `cost` = importe REAL cobrado a la cuenta por esta llamada
                # (OpenRouter lo incluye siempre). No es un cálculo local.
                coste = float(uso.get("cost", 0) or 0)
                if tokens:
                    d = self.tracker.añadir_tokens(clave, tokens)
                    print(f"📊 Tokens {clave}: {tokens} "
                          f"(hoy: {d['tokens'][clave]} este modelo, "
                          f"{sum(d['tokens'].values())} total)")
                if coste:
                    self.tracker.añadir_coste(clave, coste)
            except Exception as e:  # noqa: BLE001 — el tracking nunca debe romper el turno
                print(f"⚠️ Error guardando tokens: {e}")

            contenido = ((data.get("choices") or [{}])[0]
                         .get("message", {}).get("content") or "")
            if not contenido.strip():
                print(f"⚠️ OpenRouter {modelo} respuesta vacía, probando otro...")
                ultimo = Exception("respuesta vacía")
                continue
            if modelo != self.modelos[0]:
                print(f"⚠️ Usando modelo alternativo OpenRouter: {modelo}")
            return contenido

        raise Exception(f"Todos los modelos OpenRouter fallaron. Último error: {ultimo}")

    def completar_stream(self, mensajes, max_tokens=None, temperature=None, reasoning_effort=None):
        """Como `completar`, pero va devolviendo el texto según llega (generador de trozos
        de texto). Solo usa el primer modelo: si falla ANTES de dar nada, lanza la excepción
        y el llamante vuelve a `completar` (con su reserva de modelos). Si se corta a mitad
        de respuesta, termina con lo que llegó (repetir la respuesta entera duplicaría lo ya
        dicho en voz alta)."""
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY no configurada")
        if not self.modelos:
            raise RuntimeError("OpenRouter sin modelos configurados")
        modelo = self.modelos[0]
        ef = (reasoning_effort or "off").strip().lower()
        payload = {
            "model": modelo,
            "messages": mensajes,
            "max_tokens": max_tokens or MAX_TOKENS,
            "temperature": temperature if temperature is not None else TEMPERATURE,
            "provider": {"sort": "throughput"},
            "reasoning": {"enabled": False} if ef == "off" else {"effort": ef},
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "X-Title": "Kaitosan"}
        r = requests.post(_URL, headers=headers, json=payload, timeout=_TIMEOUT, stream=True)
        if r.status_code == 400 and "reasoning" in r.text.lower():  # no acepta tocar reasoning
            payload.pop("reasoning", None)
            r = requests.post(_URL, headers=headers, json=payload, timeout=_TIMEOUT, stream=True)
        if r.status_code != 200:
            raise Exception(f"OpenRouter {modelo} {r.status_code}: {r.text[:200]}")
        dio = False
        uso = {}
        try:
            for linea in r.iter_lines(decode_unicode=True):
                if not linea or not linea.startswith("data:"):
                    continue  # comentarios SSE («: OPENROUTER PROCESSING») y líneas vacías
                cuerpo = linea[5:].strip()
                if cuerpo == "[DONE]":
                    break
                try:
                    d = json.loads(cuerpo)
                except ValueError:
                    continue
                if d.get("error"):
                    raise Exception(f"OpenRouter {modelo}: {d['error']}")
                uso = d.get("usage") or uso
                for ch in d.get("choices") or []:
                    texto = (ch.get("delta") or {}).get("content") or ""
                    if texto:
                        dio = True
                        yield texto
        except Exception as e:  # noqa: BLE001
            if not dio:
                raise
            print(f"⚠️ OpenRouter {modelo}: stream cortado a mitad ({type(e).__name__}); sigo con lo recibido")
        finally:
            r.close()
        if not dio:
            raise Exception(f"OpenRouter {modelo}: respuesta vacía")
        try:
            tokens = int(uso.get("total_tokens", 0) or 0)
            if tokens:
                clave = f"openrouter/{modelo}"
                d = self.tracker.añadir_tokens(clave, tokens)
                print(f"📊 Tokens {clave}: {tokens} (stream)")
            coste = float(uso.get("cost", 0) or 0)
            if coste:
                self.tracker.añadir_coste(f"openrouter/{modelo}", coste)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Error guardando tokens: {e}")
