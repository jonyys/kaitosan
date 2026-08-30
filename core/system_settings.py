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

WiFi como API JSON, Bluetooth y mantenimiento llegan en fases posteriores.
"""

import glob
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import time
from datetime import datetime

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

    uptime = None
    crudo = _leer_archivo("/proc/uptime")
    if crudo:
        try:
            uptime = _fmt_uptime(float(crudo.split()[0]))
        except (ValueError, IndexError):
            uptime = None

    try:
        uso = shutil.disk_usage("/")
        usado = uso.total - uso.free
        disco = {
            "total_gb": round(uso.total / 1e9, 1),
            "usado_gb": round(usado / 1e9, 1),
            "libre_gb": round(uso.free / 1e9, 1),
            "pct": round(usado / uso.total * 100) if uso.total else 0,
        }
    except OSError:
        disco = {"total_gb": None, "usado_gb": None, "libre_gb": None, "pct": None}

    return {
        "hostname": hostname,
        "modelo": modelo,
        "uptime": uptime,
        "temperatura": _temperatura(),
        "disco": disco,
    }
