"""
core/system_settings.py — Capa de sistema de Ajustes (PLAN_AJUSTES §5).

Envuelve los comandos del SO (NetworkManager, timedatectl, ALSA, sysfs…) y
devuelve `dict`s ya parseados. Reglas del plan:

  - `subprocess.run([...], capture_output=True, text=True, timeout=15)`, nunca `shell=True`.
  - Cada función devuelve datos parseados o un valor seguro; nunca lanza.
  - Fuera de Linux (o con `AJUSTES_FAKE=1`) se usa un modo simulado con datos de
    ejemplo, para poder maquetar la UI en el portátil.

Fase 3: solo las funciones de **lectura**.
    wifi_estado()   -> {conectado, ssid, senal, ip}
    hora_estado()   -> {hora, zona, ntp, tz_auto}
    volumen_get()   -> int (0..100)
    brillo_get()    -> {soportado, valor, max}
    sistema_info()  -> {hostname, modelo, uptime, temperatura, disco}

Fase 6: escrituras **estáticas** (hora, zona, volumen, brillo). Cada una valida
la entrada, devuelve `{"ok": bool, ...}` o `{"ok": False, "error": "..."}` y en
modo simulado no toca nada del sistema real.
    hora_set_ntp(on)      hora_set_manual(iso)
    zona_listar()         zona_set(tz)          zona_auto(on)
    volumen_set(pct)      brillo_set(pct)

Fase 8: selección de dispositivo de audio. Todo con modo simulado; la
preferencia se guarda en `app_settings` (`audio_output` / `audio_input`) y el
arranque de audio la lee **antes** que los `*_HINT` del `.env`.
    audio_salidas()        audio_entradas()
    audio_salida_set(id)   audio_entrada_set(id)
    audio_salida_preferida()   audio_entrada_preferida()   (las usa el arranque)
    micro_ganancia_get()   micro_ganancia_set(pct)
    audio_probar_salida()  audio_probar_micro()

Fase 9: selección de modelos de Groq. `groq_modelos()` hace un GET real a
`api.groq.com/openai/v1/models` (HTTP puro: **funciona también en el portátil**,
no se simula) y cachea la lista ~1 h. La selección se guarda en `app_settings`
(`groq_models`, JSON) y `core/config.groq_seleccion()` la aplica sobre los
valores de fábrica de `config.py`.
    groq_modelos()          groq_seleccion_get()      groq_seleccion_set(sel)

Fase 10: salud, logs y copia de seguridad (§2.1, §5, §11 nota "Diagnóstico").
`salud()` y `logs()` usan modo simulado fuera de la Pi; `backup_bd()` y
`diagnostico_zip()` funcionan también en el portátil (solo tocan ficheros del
propio proyecto). El zip de diagnóstico ofusca las claves del `.env`.
    salud()        logs(n=200)
    backup_bd()    restaurar_bd(fichero)    diagnostico_zip()

Fase 11: actualizar / reiniciar servicio / reset de fábrica (§5 notas
"actualizar()" y "reset_fabrica()", §11). El trabajo pesado corre en un hilo
daemon y las funciones responden **antes** de tocar nada (la sesión se cae al
reiniciar el servicio). Fuera de la Pi: `actualizar()` sí hace el `git pull` y
guarda el commit anterior, pero se salta `pip install` y el `restart`;
`reset_fabrica()` valida el PIN y no borra nada.
    actualizar()          reiniciar_servicio()      reset_fabrica(pin)

WiFi como API JSON, Bluetooth y onboarding llegan en fases posteriores.
"""

import glob
import hmac
import json
import os
import platform
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from datetime import datetime

from core.memory import BASE_DIR, DB_PATH
from core.settings_store import settings_get, settings_set

_BOOL_TRUE = ("1", "true", "yes", "si", "sí", "on")


# --------------------------------------------------------------------------- #
# Modo simulado
# --------------------------------------------------------------------------- #
def _simulado() -> bool:
    """True fuera de Linux o si `AJUSTES_FAKE` está activado."""
    if platform.system() != "Linux":
        return True
    return os.getenv("AJUSTES_FAKE", "").strip().lower() in _BOOL_TRUE


# --------------------------------------------------------------------------- #
# Utilidades internas
# --------------------------------------------------------------------------- #
def _cmd(args, timeout: int = 15):
    """Ejecuta un comando y devuelve su stdout (str) o None si falla."""
    try:
        p = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    if p.returncode != 0:
        return None
    return p.stdout


def _split_terse(line: str) -> list[str]:
    """Parte una línea de `nmcli -t` respetando el escape de ':' y '\\'."""
    campos, buf, esc = [], "", False
    for ch in line:
        if esc:
            buf += ch
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == ":":
            campos.append(buf)
            buf = ""
        else:
            buf += ch
    campos.append(buf)
    return campos


def _leer_archivo(ruta: str):
    try:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _fmt_uptime(segundos: float) -> str:
    segundos = int(segundos)
    dias, resto = divmod(segundos, 86400)
    horas, resto = divmod(resto, 3600)
    minutos = resto // 60
    partes = []
    if dias:
        partes.append(f"{dias} día{'s' if dias != 1 else ''}")
    if horas:
        partes.append(f"{horas} h")
    partes.append(f"{minutos} min")
    return ", ".join(partes)


def _temperatura():
    """Temperatura de la CPU en °C, o None si no se puede leer."""
    crudo = _leer_archivo("/sys/class/thermal/thermal_zone0/temp")
    if crudo:
        try:
            return round(int(crudo.strip()) / 1000, 1)
        except ValueError:
            pass
    salida = _cmd(["vcgencmd", "measure_temp"])
    if salida:
        m = re.search(r"([\d.]+)", salida)
        if m:
            return round(float(m.group(1)), 1)
    return None


def _uptime_txt():
    """Tiempo encendida como texto ('3 días, 4 h, 12 min'), o None."""
    crudo = _leer_archivo("/proc/uptime")
    if not crudo:
        return None
    try:
        return _fmt_uptime(float(crudo.split()[0]))
    except (ValueError, IndexError):
        return None


def _disco() -> dict:
    """Uso del disco de '/' -> {total_gb, usado_gb, libre_gb, pct}."""
    try:
        uso = shutil.disk_usage("/")
    except OSError:
        return {"total_gb": None, "usado_gb": None, "libre_gb": None, "pct": None}
    usado = uso.total - uso.free
    return {
        "total_gb": round(uso.total / 1e9, 1),
        "usado_gb": round(usado / 1e9, 1),
        "libre_gb": round(uso.free / 1e9, 1),
        "pct": round(usado / uso.total * 100) if uso.total else 0,
    }


def _tz_auto() -> bool:
    """Preferencia guardada en app_settings (no es un dato del SO)."""
    return settings_get("tz_auto") == "1"


def _clamp_pct(valor) -> int | None:
    """Normaliza un porcentaje a un entero 0..100; None si no es un número."""
    try:
        n = int(round(float(valor)))
    except (TypeError, ValueError):
        return None
    return max(0, min(100, n))


# Formato aceptado para la hora manual: 'YYYY-MM-DD HH:MM[:SS]' (o con 'T').
_RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$")

# Cache por proceso de `timedatectl list-timezones` (lista larga y estable).
_ZONAS_CACHE: "list[str] | None" = None


# --------------------------------------------------------------------------- #
# WiFi
# --------------------------------------------------------------------------- #
def wifi_estado() -> dict:
    """{conectado: bool, ssid: str|None, senal: int|None, ip: str|None}"""
    if _simulado():
        return {
            "conectado": True,
            "ssid": "MiFibra-A1B2",
            "senal": 74,
            "ip": "192.168.1.42",
        }

    conectado, ssid, senal, ip = False, None, None, None
    try:
        salida = _cmd(
            ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL", "dev", "wifi"]
        )
        for linea in (salida or "").splitlines():
            campos = _split_terse(linea)
            if len(campos) >= 3 and campos[0] == "*":
                conectado = True
                ssid = campos[1] or None
                senal = int(campos[2]) if campos[2].isdigit() else None
                break

        salida_ip = _cmd(["nmcli", "-t", "-f", "IP4.ADDRESS", "device", "show"])
        for linea in (salida_ip or "").splitlines():
            if linea.startswith("IP4.ADDRESS") and ":" in linea:
                valor = _split_terse(linea)[1].split("/")[0].strip()
                if valor:
                    ip = valor
                    break
    except Exception as e:  # noqa: BLE001 — nunca debe propagar
        return {"conectado": False, "ssid": None, "senal": None,
                "ip": None, "error": str(e)}

    return {"conectado": conectado, "ssid": ssid, "senal": senal, "ip": ip}


# --------------------------------------------------------------------------- #
# Hora
# --------------------------------------------------------------------------- #
def hora_estado() -> dict:
    """{hora: iso, zona: str|None, ntp: bool, tz_auto: bool}"""
    if _simulado():
        return {
            "hora": datetime.now().isoformat(timespec="seconds"),
            "zona": "Europe/Madrid",
            "ntp": True,
            "tz_auto": _tz_auto(),
        }

    zona, ntp = None, False
    try:
        salida = _cmd(
            ["timedatectl", "show", "-p", "Timezone", "-p", "NTP", "--value"]
        )
        lineas = (salida or "").splitlines()
        if len(lineas) >= 1:
            zona = lineas[0].strip() or None
        if len(lineas) >= 2:
            ntp = lineas[1].strip().lower() == "yes"
    except Exception:  # noqa: BLE001
        pass

    return {
        "hora": datetime.now().isoformat(timespec="seconds"),
        "zona": zona,
        "ntp": ntp,
        "tz_auto": _tz_auto(),
    }


def hora_set_ntp(on: bool) -> dict:
    """Activa/desactiva la sincronización horaria automática (NTP)."""
    if _simulado():
        return {"ok": True, "simulado": True}
    if _cmd(["timedatectl", "set-ntp", "true" if on else "false"]) is None:
        return {"ok": False, "error": "no se pudo cambiar la hora automática"}
    return {"ok": True}


def hora_set_manual(iso: str) -> dict:
    """Fija la hora del sistema. Requiere NTP apagado (se apaga antes)."""
    crudo = (iso or "").strip()
    if not _RE_FECHA.match(crudo):
        return {"ok": False, "error": "formato de fecha no válido (YYYY-MM-DD HH:MM)"}
    texto = crudo.replace("T", " ")
    if len(texto) == 16:                       # sin segundos -> añadir ':00'
        texto += ":00"
    if _simulado():
        return {"ok": True, "simulado": True}
    _cmd(["timedatectl", "set-ntp", "false"])  # set-time falla si NTP está activo
    if _cmd(["timedatectl", "set-time", texto]) is None:
        return {"ok": False, "error": "no se pudo fijar la hora"}
    return {"ok": True}


def zona_listar() -> list:
    """Lista de zonas horarias para el desplegable (y lista blanca de validación)."""
    global _ZONAS_CACHE
    if _ZONAS_CACHE is not None:
        return _ZONAS_CACHE
    if _simulado():
        _ZONAS_CACHE = [
            "Europe/Madrid", "Atlantic/Canary", "Europe/London", "Europe/Lisbon",
            "Europe/Paris", "Europe/Berlin", "Europe/Rome", "America/New_York",
            "America/Chicago", "America/Denver", "America/Los_Angeles",
            "America/Mexico_City", "America/Bogota", "America/Lima",
            "America/Argentina/Buenos_Aires", "America/Sao_Paulo",
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
            "UTC",
        ]
        return _ZONAS_CACHE
    zonas = [ln.strip() for ln in (_cmd(["timedatectl", "list-timezones"]) or "").splitlines() if ln.strip()]
    if zonas:
        _ZONAS_CACHE = zonas
    return zonas


def zona_set(tz: str) -> dict:
    """Fija la zona horaria manual (validada contra `zona_listar()`)."""
    tz = (tz or "").strip()
    if not tz or tz not in zona_listar():
        return {"ok": False, "error": "zona horaria desconocida"}
    if _simulado():
        return {"ok": True, "simulado": True}
    if _cmd(["timedatectl", "set-timezone", tz]) is None:
        return {"ok": False, "error": "no se pudo fijar la zona horaria"}
    return {"ok": True}


def zona_auto(on: bool) -> dict:
    """on -> `tzupdate` (geolocaliza por IP). Guarda la preferencia en app_settings.

    Ojo: con `on` se hace 1 petición saliente a un servicio de geolocalización.
    """
    settings_set("tz_auto", "1" if on else "0")
    if not on:
        return {"ok": True}
    if _simulado():
        return {"ok": True, "simulado": True}
    if _cmd(["tzupdate"], timeout=30) is None:
        return {"ok": False, "error": "tzupdate no está disponible o no hay red"}
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Sonido
# --------------------------------------------------------------------------- #
def volumen_get() -> int:
    """Volumen de la tarjeta de salida, 0..100. 50 si no se puede leer."""
    if _simulado():
        return 65

    forzado = os.getenv("AJUSTES_MIXER_CONTROL", "").strip()
    controles = [forzado] if forzado else [
        "Master", "PCM", "Speaker", "Playback", "Digital", "Headphone",
    ]
    try:
        for control in controles:
            salida = _cmd(["amixer", "-M", "sget", control])
            if not salida:
                continue
            m = re.search(r"\[(\d{1,3})%\]", salida)
            if m:
                return max(0, min(100, int(m.group(1))))
    except Exception:  # noqa: BLE001
        pass
    return 50


def volumen_set(pct) -> dict:
    """Fija el volumen de la tarjeta de salida (0..100) con `amixer -M sset`."""
    n = _clamp_pct(pct)
    if n is None:
        return {"ok": False, "error": "valor de volumen no válido"}
    if _simulado():
        return {"ok": True, "simulado": True, "valor": n}

    forzado = os.getenv("AJUSTES_MIXER_CONTROL", "").strip()
    controles = [forzado] if forzado else [
        "Master", "PCM", "Speaker", "Playback", "Digital", "Headphone",
    ]
    try:
        for control in controles:
            if _cmd(["amixer", "-M", "sget", control]) is None:
                continue
            if _cmd(["amixer", "-M", "sset", control, f"{n}%"]) is not None:
                return {"ok": True, "valor": n}
    except Exception:  # noqa: BLE001
        pass
    return {"ok": False, "error": "no se encontró un control de volumen"}


# --------------------------------------------------------------------------- #
# Audio: selección de dispositivo (§2.1, §5 nota "Selección de audio")
# --------------------------------------------------------------------------- #
# En modo simulado los índices ALSA no existen; usamos tarjetas de ejemplo. El
# `id` es un trozo estable del nombre (nunca el número de tarjeta, que baila
# entre arranques) y sirve a la vez como subcadena para la autodetección.
_AUDIO_SALIDAS_FAKE = [
    {"id": "hifiberry", "nombre": "HiFiBerry DAC — altavoz de Kaito"},
    {"id": "G435", "nombre": "Logitech G435 — cascos"},
    {"id": "HDMI", "nombre": "Salida HDMI"},
]
_AUDIO_ENTRADAS_FAKE = [
    {"id": "AB17X", "nombre": "Micrófono USB AB17X"},
    {"id": "G435", "nombre": "Logitech G435 — micro de los cascos"},
]


def _audio_dispositivos_reales(entrada: bool) -> list:
    """Enumera tarjetas de audio con `sounddevice` (reutiliza la autodetección
    del resto del proyecto). Devuelve [] si `sounddevice` no está disponible."""
    try:
        import sounddevice as sd
    except Exception:  # noqa: BLE001 — la capa de sistema nunca propaga
        return []
    clave = "max_input_channels" if entrada else "max_output_channels"
    pref = (audio_entrada_preferida() if entrada else audio_salida_preferida()).lower()
    salidas, vistos = [], set()
    try:
        for d in sd.query_devices():
            if d.get(clave, 0) <= 0:
                continue
            nombre = (d.get("name") or "").strip()
            if not nombre or nombre in vistos:
                continue
            vistos.add(nombre)
            salidas.append({
                "id": nombre,
                "nombre": nombre,
                "en_uso": bool(pref) and pref in nombre.lower(),
            })
    except Exception:  # noqa: BLE001
        return []
    return salidas


def _resolver_indice(pref: str, entrada: bool):
    """Resuelve una subcadena a un índice de dispositivo de `sounddevice`, o
    None (para que `sounddevice` use el predeterminado)."""
    pref = (pref or "").strip().lower()
    if not pref:
        return None
    try:
        import sounddevice as sd
    except Exception:  # noqa: BLE001
        return None
    clave = "max_input_channels" if entrada else "max_output_channels"
    try:
        for i, d in enumerate(sd.query_devices()):
            if d.get(clave, 0) > 0 and pref in (d.get("name") or "").lower():
                return i
    except Exception:  # noqa: BLE001
        return None
    return None


def audio_salidas() -> list:
    """[{id, nombre, en_uso}] — tarjetas de salida elegibles."""
    guardada = (settings_get("audio_output") or "").strip()
    if _simulado():
        return [{**s, "en_uso": s["id"] == guardada} for s in _AUDIO_SALIDAS_FAKE]
    return _audio_dispositivos_reales(entrada=False)


def audio_entradas() -> list:
    """[{id, nombre, en_uso}] — micrófonos elegibles."""
    guardada = (settings_get("audio_input") or "").strip()
    if _simulado():
        return [{**s, "en_uso": s["id"] == guardada} for s in _AUDIO_ENTRADAS_FAKE]
    return _audio_dispositivos_reales(entrada=True)


def audio_salida_set(valor) -> dict:
    """Guarda la salida elegida en `app_settings` (sustituye AUDIO_OUTPUT_HINT).
    Cadena vacía = volver a la autodetección del `.env`."""
    valor = (valor or "").strip()
    if valor and valor not in {s["id"] for s in audio_salidas()}:
        return {"ok": False, "error": "dispositivo de salida desconocido"}
    settings_set("audio_output", valor)
    return {"ok": True, "valor": valor}


def audio_entrada_set(valor) -> dict:
    """Guarda el micrófono elegido en `app_settings` (sustituye AUDIO_INPUT_HINT).
    Cadena vacía = volver a la autodetección del `.env`."""
    valor = (valor or "").strip()
    if valor and valor not in {s["id"] for s in audio_entradas()}:
        return {"ok": False, "error": "dispositivo de entrada desconocido"}
    settings_set("audio_input", valor)
    return {"ok": True, "valor": valor}


def audio_salida_preferida() -> str:
    """Subcadena para elegir el altavoz: preferencia guardada y, si está vacía,
    `AUDIO_OUTPUT_HINT` del `.env` (que pasa a ser semilla / override de fábrica)."""
    guardada = (settings_get("audio_output") or "").strip()
    if guardada:
        return guardada
    from core.config import AUDIO_OUTPUT_HINT
    return AUDIO_OUTPUT_HINT


def audio_entrada_preferida() -> str:
    """Ídem para el micrófono: `app_settings` antes que `AUDIO_INPUT_HINT`."""
    guardada = (settings_get("audio_input") or "").strip()
    if guardada:
        return guardada
    from core.config import AUDIO_INPUT_HINT
    return AUDIO_INPUT_HINT


def micro_ganancia_get() -> int:
    """Ganancia de captura del micrófono, 0..100. 50 si no se puede leer."""
    if _simulado():
        return 70
    try:
        for control in ("Capture", "Mic", "Front Mic"):
            salida = _cmd(["amixer", "-M", "sget", control])
            if not salida:
                continue
            m = re.search(r"\[(\d{1,3})%\]", salida)
            if m:
                return max(0, min(100, int(m.group(1))))
    except Exception:  # noqa: BLE001
        pass
    return 50


def micro_ganancia_set(pct) -> dict:
    """Fija la ganancia del micrófono (0..100) con `amixer -M sset Capture`."""
    n = _clamp_pct(pct)
    if n is None:
        return {"ok": False, "error": "valor de ganancia no válido"}
    if _simulado():
        return {"ok": True, "simulado": True, "valor": n}
    try:
        for control in ("Capture", "Mic", "Front Mic"):
            if _cmd(["amixer", "-M", "sget", control]) is None:
                continue
            if _cmd(["amixer", "-M", "sset", control, f"{n}%"]) is not None:
                return {"ok": True, "valor": n}
    except Exception:  # noqa: BLE001
        pass
    return {"ok": False, "error": "no se encontró un control de ganancia de micrófono"}


def audio_probar_salida() -> dict:
    """Reproduce un tono corto por la salida activa."""
    if _simulado():
        return {"ok": True, "simulado": True}
    try:
        import numpy as np
        import sounddevice as sd
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"audio no disponible: {e}"}
    try:
        sr = 44100
        t = np.linspace(0, 0.6, int(sr * 0.6), endpoint=False)
        tono = (0.2 * np.sin(2 * np.pi * 660 * t)).astype("float32")
        sd.play(tono, sr, device=_resolver_indice(audio_salida_preferida(), entrada=False))
        sd.wait()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"no se pudo reproducir el tono: {e}"}
    return {"ok": True}


def audio_probar_micro() -> dict:
    """Graba 2 s por el micrófono activo y los reproduce por la salida activa."""
    if _simulado():
        return {"ok": True, "simulado": True}
    try:
        import sounddevice as sd
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"audio no disponible: {e}"}
    try:
        sr = 44100
        grab = sd.rec(int(sr * 2), samplerate=sr, channels=1, dtype="float32",
                      device=_resolver_indice(audio_entrada_preferida(), entrada=True))
        sd.wait()
        sd.play(grab, sr, device=_resolver_indice(audio_salida_preferida(), entrada=False))
        sd.wait()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"no se pudo probar el micrófono: {e}"}
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Modelos de IA (Groq) — §2.1, §5 nota "Modelos de Groq", §11
# --------------------------------------------------------------------------- #
# Cache por proceso de la lista de modelos (la API cambia poco; el plan pide ~1 h).
_GROQ_CACHE: dict = {"ts": 0.0, "datos": None}
_GROQ_CACHE_SEG = 3600

# Subcadenas que descartan un modelo del desplegable de chat: audio (whisper/tts)
# y clasificadores de seguridad (guard). El resto de modelos `active` entran.
_GROQ_EXCLUIR = ("whisper", "tts", "guard", "playai")


def groq_modelos(forzar: bool = False) -> list:
    """Modelos de chat disponibles para la API key configurada.

    `GET https://api.groq.com/openai/v1/models` con `Authorization: Bearer`.
    Filtra `active != false` y excluye los de audio / guard. Cachea ~1 h por
    proceso. Es HTTP puro, así que **no se simula**: en el portátil devuelve la
    lista real. Devuelve `[]` si no hay API key o la red falla.

        [{id, context_window, owned_by, tokens_hoy}]
    """
    ahora = time.time()
    if (not forzar and _GROQ_CACHE["datos"] is not None
            and ahora - _GROQ_CACHE["ts"] < _GROQ_CACHE_SEG):
        return _GROQ_CACHE["datos"]

    from core.config import GROQ_API_KEY
    if not GROQ_API_KEY:
        return []

    try:
        import requests
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception:  # noqa: BLE001 — la capa de sistema nunca propaga
        return _GROQ_CACHE["datos"] or []

    tokens_hoy = {}
    try:
        from core.token_tracker import TokenTracker
        tokens_hoy = TokenTracker().consultar().get("tokens", {})
    except Exception:  # noqa: BLE001
        pass

    modelos = []
    for m in data:
        mid = (m.get("id") or "").strip()
        if not mid or m.get("active") is False:
            continue
        if any(x in mid.lower() for x in _GROQ_EXCLUIR):
            continue
        modelos.append({
            "id": mid,
            "context_window": m.get("context_window"),
            "owned_by": m.get("owned_by"),
            "tokens_hoy": tokens_hoy.get(mid, 0),
        })
    modelos.sort(key=lambda x: x["id"])

    _GROQ_CACHE.update(ts=ahora, datos=modelos)
    return modelos


def groq_seleccion_get() -> dict:
    """Selección efectiva actual: {principal, sensei, alternativos:[...], tools:[...]}.

    Es lo guardado en `app_settings` con los huecos rellenados por los valores
    de fábrica de `core/config.py` (ver `groq_seleccion()` allí).
    """
    from core.config import groq_seleccion
    return groq_seleccion()


def groq_seleccion_set(sel: dict) -> dict:
    """Valida `sel` contra `groq_modelos()` y lo guarda en `app_settings['groq_models']`.

    - `principal` y `sensei` son obligatorios y deben existir en la lista real
      (si se pudo consultar); si no, se rechaza.
    - de `alternativos` y `tools` se descartan en silencio los ids que ya no
      estén activos (no se deja guardar un id retirado).
    """
    if not isinstance(sel, dict):
        return {"ok": False, "error": "selección no válida"}

    principal = (sel.get("principal") or "").strip()
    sensei = (sel.get("sensei") or "").strip()
    alternativos = list(dict.fromkeys(
        str(m).strip() for m in (sel.get("alternativos") or []) if str(m).strip()
    ))
    tools = list(dict.fromkeys(
        str(m).strip() for m in (sel.get("tools") or []) if str(m).strip()
    ))

    if not principal or not sensei:
        return {"ok": False, "error": "elige un modelo principal y uno para el sensei"}

    ids = {m["id"] for m in groq_modelos()}
    if ids:
        desconocidos = [x for x in (principal, sensei) if x not in ids]
        if desconocidos:
            return {"ok": False,
                    "error": "modelo no disponible: " + ", ".join(desconocidos)}
        alternativos = [m for m in alternativos if m in ids]
        tools = [m for m in tools if m in ids]

    payload = {
        "principal": principal,
        "sensei": sensei,
        "alternativos": alternativos,
        "tools": tools,
    }
    settings_set("groq_models", json.dumps(payload))
    return {"ok": True, "seleccion": payload}


# --------------------------------------------------------------------------- #
# Pantalla
# --------------------------------------------------------------------------- #
def brillo_get() -> dict:
    """{soportado: bool, valor: int|None, max: int|None}

    `soportado` es False si no hay ningún `/sys/class/backlight/*` (p. ej.
    monitor HDMI); la UI oculta la tarjeta de brillo en ese caso.
    """
    if _simulado():
        return {"soportado": True, "valor": 180, "max": 255}

    try:
        carpetas = sorted(glob.glob("/sys/class/backlight/*"))
        if not carpetas:
            return {"soportado": False, "valor": None, "max": None}
        base = carpetas[0]
        crudo_valor = _leer_archivo(os.path.join(base, "brightness"))
        crudo_max = _leer_archivo(os.path.join(base, "max_brightness"))
        valor = int(crudo_valor.strip())
        maximo = int(crudo_max.strip())
    except (AttributeError, ValueError, OSError):
        return {"soportado": False, "valor": None, "max": None}

    return {"soportado": True, "valor": valor, "max": maximo}


def brillo_set(pct) -> dict:
    """Fija el brillo (0..100 %) escribiendo en `/sys/class/backlight/*/brightness`."""
    n = _clamp_pct(pct)
    if n is None:
        return {"ok": False, "error": "valor de brillo no válido"}
    if _simulado():
        return {"ok": True, "simulado": True, "valor": n}

    carpetas = sorted(glob.glob("/sys/class/backlight/*"))
    if not carpetas:
        return {"ok": False, "error": "no hay pantalla con brillo controlable"}
    base = carpetas[0]
    try:
        maximo = int((_leer_archivo(os.path.join(base, "max_brightness")) or "").strip())
    except ValueError:
        return {"ok": False, "error": "no se pudo leer max_brightness"}

    destino = max(1, round(maximo * n / 100))   # nunca 0 -> pantalla en negro
    try:
        with open(os.path.join(base, "brightness"), "w", encoding="utf-8") as f:
            f.write(str(destino))
    except OSError as e:
        return {"ok": False, "error": f"no se pudo escribir el brillo: {e}"}
    return {"ok": True, "valor": n}


# --------------------------------------------------------------------------- #
# Sistema
# --------------------------------------------------------------------------- #
def sistema_info() -> dict:
    """{hostname, modelo, uptime, temperatura, disco:{total_gb,usado_gb,libre_gb,pct}}"""
    if _simulado():
        return {
            "hostname": "kaitosan",
            "modelo": "Raspberry Pi 4 Model B Rev 1.5",
            "uptime": "3 días, 4 h 12 min",
            "temperatura": 47.8,
            "disco": {
                "total_gb": 29.7,
                "usado_gb": 8.3,
                "libre_gb": 21.4,
                "pct": 28,
            },
        }

    try:
        hostname = socket.gethostname()
    except OSError:
        hostname = None

    modelo = _leer_archivo("/proc/device-tree/model")
    if modelo:
        modelo = modelo.replace("\x00", "").strip() or None
    else:
        modelo = platform.platform()

    return {
        "hostname": hostname,
        "modelo": modelo,
        "uptime": _uptime_txt(),
        "temperatura": _temperatura(),
        "disco": _disco(),
    }


# --------------------------------------------------------------------------- #
# Mantenimiento — salud, logs y copia de seguridad (Fase 10, §2.1, §5, §11)
# --------------------------------------------------------------------------- #
# Bits de `vcgencmd get_throttled` (Raspberry Pi): los 4 bajos = ahora mismo,
# los 4 altos (16-19) = "ha ocurrido desde el arranque".
_THROTTLED_BITS = {
    0: "bajada de tensión ahora",
    1: "frecuencia de CPU limitada ahora",
    2: "CPU con throttling ahora",
    3: "límite térmico software ahora",
    16: "ha habido bajada de tensión",
    17: "se ha limitado la frecuencia de CPU",
    18: "ha habido throttling",
    19: "se ha alcanzado el límite térmico software",
}

# Claves del `.env` cuyo valor NO debe salir en claro en el zip de diagnóstico.
_RE_ENV_SECRETO = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|PWD|PASS)", re.IGNORECASE)


def _throttled() -> dict:
    """Estado de `vcgencmd get_throttled` -> {codigo, texto, hay_problema}."""
    salida = _cmd(["vcgencmd", "get_throttled"])
    m = re.search(r"throttled=(0x[0-9a-fA-F]+)", salida or "")
    if not m:
        return {"codigo": None, "texto": "no disponible", "hay_problema": False}
    codigo = int(m.group(1), 16)
    if codigo == 0:
        return {"codigo": "0x0", "texto": "sin problemas", "hay_problema": False}
    activos = [txt for bit, txt in _THROTTLED_BITS.items() if codigo & (1 << bit)]
    return {"codigo": hex(codigo), "texto": "; ".join(activos), "hay_problema": True}


def _cpu() -> dict:
    """Carga de CPU desde /proc/loadavg -> {pct, carga, nucleos}."""
    nucleos = os.cpu_count() or 1
    carga = None
    crudo = _leer_archivo("/proc/loadavg")
    if crudo:
        try:
            carga = float(crudo.split()[0])
        except (ValueError, IndexError):
            carga = None
    pct = None if carga is None else max(0, min(100, round(carga / nucleos * 100)))
    return {"pct": pct, "carga": carga, "nucleos": nucleos}


def _ram() -> dict:
    """Memoria desde /proc/meminfo -> {total_mb, usada_mb, pct}."""
    crudo = _leer_archivo("/proc/meminfo")
    if not crudo:
        return {"total_mb": None, "usada_mb": None, "pct": None}
    vals = {}
    for linea in crudo.splitlines():
        partes = linea.split()
        if len(partes) >= 2 and partes[0].rstrip(":") in ("MemTotal", "MemAvailable"):
            try:
                vals[partes[0].rstrip(":")] = int(partes[1])   # kB
            except ValueError:
                pass
    total, disp = vals.get("MemTotal"), vals.get("MemAvailable")
    if not total or disp is None:
        return {"total_mb": None, "usada_mb": None, "pct": None}
    usada = total - disp
    return {
        "total_mb": round(total / 1024),
        "usada_mb": round(usada / 1024),
        "pct": round(usada / total * 100) if total else None,
    }


def salud() -> dict:
    """Salud del sistema para la tarjeta de Mantenimiento.

    {temperatura, throttled:{codigo,texto,hay_problema}, cpu:{pct,carga,nucleos},
     ram:{total_mb,usada_mb,pct}, disco:{total_gb,usado_gb,libre_gb,pct}, uptime}
    """
    if _simulado():
        return {
            "temperatura": 47.8,
            "throttled": {"codigo": "0x0", "texto": "sin problemas",
                          "hay_problema": False},
            "cpu": {"pct": 12, "carga": 0.48, "nucleos": 4},
            "ram": {"total_mb": 3792, "usada_mb": 1123, "pct": 30},
            "disco": {"total_gb": 29.7, "usado_gb": 8.3, "libre_gb": 21.4, "pct": 28},
            "uptime": "3 días, 4 h, 12 min",
        }
    return {
        "temperatura": _temperatura(),
        "throttled": _throttled(),
        "cpu": _cpu(),
        "ram": _ram(),
        "disco": _disco(),
        "uptime": _uptime_txt(),
    }


def logs(n: int = 200) -> str:
    """Últimas `n` líneas del journal del servicio (`journalctl -u kaito`).

    En modo simulado devuelve un ejemplo; en la Pi, la salida real (o un aviso
    si `journalctl` no está disponible / sin permisos).
    """
    try:
        n = max(1, min(2000, int(n)))
    except (TypeError, ValueError):
        n = 200

    if _simulado():
        sello = datetime.now().strftime("%b %d %H:%M:%S")
        ejemplo = [
            "(modo simulado — líneas de ejemplo, no son logs reales)",
            "INFO  app escuchando en http://0.0.0.0:5000",
            "INFO  cámara inicializada (640x480 @15fps)",
            "INFO  listener de voz activo — wakeword 'kaito'",
            "INFO  turno de charla completado (groq: 412 tokens)",
            "WARN  rate limit de Groq; probando modelo alternativo",
            "INFO  recordatorio disparado: 'clase de japonés'",
        ]
        return "\n".join(f"{sello} kaitosan kaito[1234]: {ln}" for ln in ejemplo)

    salida = _cmd(
        ["journalctl", "-u", "kaito", "-n", str(n), "--no-pager"], timeout=20
    )
    if salida is None:
        return "(no se pudieron leer los logs: journalctl no disponible o sin permisos)"
    return salida.strip() or "(sin entradas de log)"


def _es_sqlite(ruta: str) -> bool:
    """True si `ruta` es un fichero SQLite íntegro (cabecera + integrity_check)."""
    try:
        with open(ruta, "rb") as f:
            if f.read(16) != b"SQLite format 3\x00":
                return False
    except OSError:
        return False
    try:
        con = sqlite3.connect(ruta)
        try:
            fila = con.execute("PRAGMA integrity_check").fetchone()
        finally:
            con.close()
    except sqlite3.Error:
        return False
    return bool(fila) and fila[0] == "ok"


def backup_bd() -> str:
    """Copia consistente de `data/kaito.db` en un temporal; devuelve su ruta.

    Usa la API `backup` de SQLite (segura aunque la app esté escribiendo).
    """
    destino = os.path.join(
        tempfile.gettempdir(),
        f"kaito-backup-{datetime.now():%Y%m%d-%H%M%S}.db",
    )
    try:
        origen = sqlite3.connect(DB_PATH)
        try:
            copia = sqlite3.connect(destino)
            try:
                with copia:
                    origen.backup(copia)
            finally:
                copia.close()
        finally:
            origen.close()
    except (sqlite3.Error, OSError):
        shutil.copy2(DB_PATH, destino)          # último recurso
    return destino


def restaurar_bd(fichero: str) -> dict:
    """Valida que `fichero` es SQLite y reemplaza `data/kaito.db`.

    Hace un `backup_bd()` automático de la BD actual justo antes (§11). El
    servicio debe reiniciarse para leer la nueva BD (Fase 11 en la Pi).
    """
    if not fichero or not os.path.isfile(fichero):
        return {"ok": False, "error": "no se recibió ningún fichero"}
    if not _es_sqlite(fichero):
        return {"ok": False, "error": "el fichero no es una base de datos SQLite válida"}

    try:
        respaldo = backup_bd()
    except Exception:  # noqa: BLE001 — la capa de sistema nunca propaga
        respaldo = None
    try:
        shutil.copy2(fichero, DB_PATH)
    except OSError as e:
        return {"ok": False, "error": f"no se pudo reemplazar la BD: {e}"}
    return {
        "ok": True,
        "respaldo": respaldo,
        "aviso": "Reinicia el servicio para que Kaito use la BD restaurada.",
    }


def _ofuscar_env(texto: str) -> str:
    """Sustituye el valor de las claves sensibles del `.env` por un marcador."""
    salida = []
    for linea in texto.splitlines():
        tira = linea.strip()
        if not tira or tira.startswith("#") or "=" not in linea:
            salida.append(linea)
            continue
        clave, _, valor = linea.partition("=")
        v = valor.strip().strip('"').strip("'")
        if v and _RE_ENV_SECRETO.search(clave):
            pista = (v[:2] + "…" + v[-2:]) if len(v) > 6 else "…"
            salida.append(f"{clave}=***ofuscado*** (len={len(v)}, {pista})")
        else:
            salida.append(linea)
    return "\n".join(salida)


def diagnostico_zip() -> str:
    """Zip para soporte: salud + logs + `.env` con las claves ofuscadas + red.

    Devuelve la ruta al zip. §11: revisar el contenido a mano antes de
    compartirlo (los logs reales aún podrían contener algún secreto).
    """
    destino = os.path.join(
        tempfile.gettempdir(),
        f"kaito-diagnostico-{datetime.now():%Y%m%d-%H%M%S}.zip",
    )
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("info.txt",
                   "Diagnóstico de Kaito\n"
                   f"Generado: {datetime.now().isoformat(timespec='seconds')}\n"
                   f"Modo simulado: {_simulado()}\n\n"
                   "Las claves del .env van ofuscadas. Revisa logs.txt por si "
                   "acaso antes de compartir este archivo.\n")
        z.writestr("salud.json",
                   json.dumps(salud(), indent=2, ensure_ascii=False))
        z.writestr("logs.txt", logs(500))

        crudo_env = _leer_archivo(os.path.join(BASE_DIR, ".env"))
        if crudo_env is not None:
            z.writestr("env.ofuscado.txt", _ofuscar_env(crudo_env))

        if _simulado():
            z.writestr("nmcli-dev-status.txt", "(modo simulado)\n")
        else:
            z.writestr("nmcli-dev-status.txt",
                       _cmd(["nmcli", "dev", "status"]) or "(nmcli no disponible)\n")

    return destino


# --------------------------------------------------------------------------- #
# Mantenimiento — actualizar / reiniciar servicio / reset (Fase 11, §5, §11)
# --------------------------------------------------------------------------- #
# PIN por defecto para el reset de fábrica cuando no hay `pin_hash` guardado ni
# `AJUSTES_RESET_PIN` en el `.env`. El reset es irreversible: la UI pide doble
# confirmación y aquí se re-valida el PIN.
_RESET_PIN_DEFECTO = "1234"

# Estado de la última actualización, para que la UI pueda consultarlo si quiere.
_ACTUALIZAR_ESTADO: dict = {"en_curso": False, "pasos": None}


def _git(args: list, cwd: str, timeout: int = 120):
    """`git -C <cwd> <args...>` -> stdout o None."""
    return _cmd(["git", "-C", cwd, *args], timeout=timeout)


def _actualizar_worker(raiz: str) -> None:
    """Hilo daemon: git pull (+ pip install + restart fuera de simulado)."""
    pasos = []
    try:
        salida = _git(["pull", "--ff-only"], raiz)
        pasos.append(["git pull", (salida or "ERROR").strip()])
        if _simulado():
            pasos.append(["pip install", "omitido (modo simulado)"])
            pasos.append(["systemctl restart kaito", "omitido (modo simulado)"])
        else:
            pip = _cmd(
                [sys.executable, "-m", "pip", "install", "-r",
                 os.path.join(raiz, "requirements.txt")],
                timeout=600,
            )
            pasos.append(["pip install", (pip or "ERROR").strip()[-500:]])
            r = _cmd(["sudo", "-n", "systemctl", "restart", "kaito"], timeout=30)
            pasos.append(["systemctl restart kaito",
                          "ok" if r is not None else "ERROR"])
    finally:
        _ACTUALIZAR_ESTADO.update(en_curso=False, pasos=pasos)


def actualizar() -> dict:
    """`git pull` + `pip install -r` + `systemctl restart kaito`, en segundo plano.

    Responde **antes** de tocar nada: el trabajo real corre en un hilo daemon
    (§5). Guarda el commit actual en `app_settings['update_commit_anterior']`
    para poder ofrecer "volver a la versión anterior". Nunca se auto-invoca.

    Fuera de la Pi (simulado) hace el `git pull` y guarda el commit anterior,
    pero se salta `pip install` y el `restart`.
    """
    if _ACTUALIZAR_ESTADO["en_curso"]:
        return {"ok": False, "error": "ya hay una actualización en curso"}

    raiz = BASE_DIR
    commit_anterior = (_git(["rev-parse", "HEAD"], raiz) or "").strip() or None
    if commit_anterior:
        settings_set("update_commit_anterior", commit_anterior)
    log_entrante = (_git(["log", "--oneline", "-n", "8"], raiz) or "").strip()

    _ACTUALIZAR_ESTADO.update(en_curso=True, pasos=None)
    threading.Thread(
        target=_actualizar_worker, args=(raiz,), daemon=True
    ).start()

    return {
        "ok": True,
        "commit_anterior": commit_anterior,
        "log": log_entrante,
        "simulado": _simulado(),
        "mensaje": (
            "Actualizando Kaito. El servicio se reiniciará y esta página se "
            "desconectará un momento: recárgala en 1–2 minutos."
        ),
    }


def reiniciar_servicio() -> dict:
    """`sudo systemctl restart kaito` — reinicia solo el servicio, no la Pi.

    Corta la sesión unos segundos (mismo aviso que el cambio de WiFi, §7.4).
    Responde antes de reiniciar; el `restart` va en un hilo daemon.
    """
    if _simulado():
        return {"ok": True, "simulado": True,
                "mensaje": "En la Pi el servicio se reiniciaría ahora."}

    def _worker():
        time.sleep(0.5)                        # deja que responda el fetch
        _cmd(["sudo", "-n", "systemctl", "restart", "kaito"], timeout=30)

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True,
            "mensaje": ("Reiniciando el servicio. Esta página se desconectará "
                        "unos segundos; recárgala enseguida.")}


def _pin_correcto(pin: str) -> bool:
    """Valida el PIN del reset contra `app_settings['pin_hash']` o, si no hay,
    contra `AJUSTES_RESET_PIN` del `.env` (por defecto `_RESET_PIN_DEFECTO`)."""
    pin = (pin or "").strip()
    if not pin:
        return False
    h = settings_get("pin_hash")
    if h:
        try:
            from werkzeug.security import check_password_hash
            return check_password_hash(h, pin)
        except Exception:  # noqa: BLE001
            return False
    esperado = os.getenv("AJUSTES_RESET_PIN", "").strip() or _RESET_PIN_DEFECTO
    return hmac.compare_digest(pin, esperado)


def reset_fabrica(pin: str) -> dict:
    """Reset de fábrica: PIN -> copia de la BD -> borra BD, claves de
    `app_settings` y conexiones de NetworkManager -> vuelve al onboarding
    (§5, §11). Irreversible; la UI exige doble confirmación + PIN.

    Fuera de la Pi (simulado) valida el PIN, hace la copia de seguridad y **no
    borra nada**.
    """
    if not _pin_correcto(pin):
        return {"ok": False, "error": "PIN incorrecto"}

    try:                                        # §11: backup automático antes
        respaldo = backup_bd()
    except Exception:  # noqa: BLE001 — la capa de sistema nunca propaga
        respaldo = None

    if _simulado():
        return {
            "ok": True, "simulado": True, "respaldo": respaldo,
            "mensaje": ("PIN correcto. En la Pi se borrarían la base de datos, "
                        "los ajustes y las redes WiFi guardadas, y volvería el "
                        "portal de configuración 'Kaitosan-Setup'."),
        }

    for con in (_cmd(["nmcli", "-g", "NAME", "con", "show"]) or "").splitlines():
        con = con.strip()
        if con:
            _cmd(["nmcli", "con", "delete", con])

    try:
        if os.path.isfile(DB_PATH):
            os.remove(DB_PATH)                  # se lleva también app_settings
    except OSError as e:
        return {"ok": False, "error": f"no se pudo borrar la BD: {e}",
                "respaldo": respaldo}

    _cmd(["sudo", "-n", "systemctl", "start", "kaitosan-wifi-connect"])

    def _worker():
        time.sleep(1)
        _cmd(["sudo", "-n", "systemctl", "restart", "kaito"], timeout=30)

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "respaldo": respaldo,
            "mensaje": ("Reset completado. Kaito vuelve al modo de "
                        "configuración inicial (WiFi 'Kaitosan-Setup').")}
