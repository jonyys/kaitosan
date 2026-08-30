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

Las escrituras (hora/zona/volumen/brillo…), WiFi como API JSON, Bluetooth,
audio, modelos y mantenimiento llegan en fases posteriores.
"""

import glob
import os
import platform
import re
import shutil
import socket
import subprocess
from datetime import datetime

from core.settings_store import settings_get

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
