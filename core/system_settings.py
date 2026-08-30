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
`reset_fabrica()` hace la copia de seguridad y no borra nada.
    actualizar()          reiniciar_servicio()      reset_fabrica()

Fase 13: WiFi real en la Pi (§5 notas WiFi, §7.2 bloque WiFi, §7.4). Cambiar de
red **tumba la conexión** con la que se ve la página, así que `wifi_conectar()`
responde antes de tocar nada: el `nmcli connect` y un **watchdog de reversión**
a 60 s corren en un hilo daemon. Si tras el cambio no hay conectividad plena,
vuelve al SSID anterior y, en último caso, deja que el portal
`kaitosan-wifi-connect` levante la red de seguridad.
    wifi_estado()      wifi_escanear()      wifi_guardadas()
    wifi_conectar(ssid, psk)   wifi_olvidar(ssid)   wifi_abrir_portal()

Fase 14: Bluetooth real en la Pi (§2.1, §5 nota Bluetooth, §6.7, §7.2 bloque
Bluetooth). `bluetoothctl` en modo no interactivo (subcomandos, nunca
`shell=True`). Mismo patrón que WiFi: API JSON + `fetch`. Al conectar un
dispositivo de audio aparece como salida elegible en `audio_salidas()`; si se
apaga o sale de rango, `audio_salida_preferida()` cae a la tarjeta local.
    bt_estado()        bt_radio(on)         bt_escanear(seg=10)
    bt_emparejados()   bt_conectar(mac)     bt_desconectar(mac)   bt_olvidar(mac)

El onboarding WiFi (`balena-wifi-connect`) llega en una fase posterior.
"""

import glob
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


# Aviso para la UI cuando se cambia de red (§7.4.2): la sesión puede caerse.
_WIFI_AVISO = (
    "Kaito se está conectando a «{ssid}». Si pierdes esta página, conéctate a "
    "esa misma red y vuelve a entrar en http://kaitosan.local:5000"
)


def wifi_escanear() -> list:
    """Redes WiFi visibles -> [{ssid, senal, seguridad, en_uso}] (una por SSID).

    `nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list --rescan yes` (§5).
    """
    if _simulado():
        return [
            {"ssid": "MiFibra-A1B2",       "senal": 74, "seguridad": "WPA2", "en_uso": True},
            {"ssid": "MOVISTAR_5G_3F2A",   "senal": 58, "seguridad": "WPA2", "en_uso": False},
            {"ssid": "Vodafone-2C10",      "senal": 41, "seguridad": "WPA2", "en_uso": False},
            {"ssid": "Casa de la abuela",  "senal": 33, "seguridad": "WPA2", "en_uso": False},
            {"ssid": "Invitados",          "senal": 66, "seguridad": "abierta", "en_uso": False},
        ]

    salida = _cmd(
        ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE",
         "dev", "wifi", "list", "--rescan", "yes"],
        timeout=25,
    )
    redes, vistos = [], set()
    for linea in (salida or "").splitlines():
        campos = _split_terse(linea)
        if len(campos) < 4:
            continue
        ssid = campos[0].strip()
        if not ssid or ssid in vistos:            # oculta ("") y duplicados fuera
            continue
        vistos.add(ssid)
        redes.append({
            "ssid": ssid,
            "senal": int(campos[1]) if campos[1].isdigit() else None,
            "seguridad": campos[2].strip() or "abierta",
            "en_uso": campos[3].strip() == "*",
        })
    redes.sort(key=lambda r: r["senal"] or 0, reverse=True)
    return redes


def wifi_guardadas() -> list:
    """Nombres de las conexiones WiFi ya guardadas en NetworkManager."""
    if _simulado():
        return ["MiFibra-A1B2", "Casa de la abuela", "Oficina"]

    salida = _cmd(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"])
    guardadas = []
    for linea in (salida or "").splitlines():
        campos = _split_terse(linea)
        if len(campos) >= 2 and campos[1].strip() in ("802-11-wireless", "wifi"):
            nombre = campos[0].strip()
            if nombre:
                guardadas.append(nombre)
    return guardadas


def _conectividad_plena() -> bool:
    """True si `nmcli -t -f CONNECTIVITY g` dice `full` (§7.4.3)."""
    return (_cmd(["nmcli", "-t", "-f", "CONNECTIVITY", "g"]) or "").strip() == "full"


def _wifi_conectar_worker(ssid: str, psk: str, anterior) -> None:
    """Hilo daemon: cambia de red y revierte si a los 60 s no hay conexión plena.

    1. `nmcli dev wifi connect`. 2. espera 60 s. 3. si no hay conectividad
    `full`, borra el perfil recién creado (contraseña mal) y vuelve a
    `anterior`. 4. si aun así no hay red, arranca el portal de onboarding.
    """
    args = ["nmcli", "dev", "wifi", "connect", ssid]
    if psk:
        args += ["password", psk]
    _cmd(args, timeout=45)

    time.sleep(60)
    if _conectividad_plena():
        return

    if anterior and anterior != ssid:
        _cmd(["nmcli", "connection", "delete", ssid])      # perfil que ha fallado
        _cmd(["nmcli", "connection", "up", anterior], timeout=45)
        time.sleep(10)
        if _conectividad_plena():
            return

    # Última red de seguridad: el portal «Kaitosan-Setup» (§7.4.3, §3.4).
    _cmd(["sudo", "-n", "systemctl", "start", "kaitosan-wifi-connect"])


def wifi_conectar(ssid: str, psk: str = "") -> dict:
    """Conecta a `ssid`. OJO: desconecta la red actual (§5, §7.4).

    Responde de inmediato; el `nmcli connect` y el watchdog de reversión a 60 s
    corren en un hilo daemon (§7.4.1). `mensaje` es el aviso para la UI (§7.4.2).
    """
    ssid = (ssid or "").strip()
    if not ssid:
        return {"ok": False, "error": "falta el nombre de la red (SSID)"}

    anterior = wifi_estado().get("ssid")

    if _simulado():
        return {"ok": True, "simulado": True, "ssid": ssid,
                "mensaje": _WIFI_AVISO.format(ssid=ssid)}

    threading.Thread(
        target=_wifi_conectar_worker,
        args=(ssid, psk or "", anterior),
        daemon=True,
    ).start()
    return {"ok": True, "ssid": ssid, "mensaje": _WIFI_AVISO.format(ssid=ssid)}


def wifi_olvidar(ssid: str) -> dict:
    """Borra la conexión guardada `ssid` de NetworkManager."""
    ssid = (ssid or "").strip()
    if not ssid:
        return {"ok": False, "error": "falta el nombre de la red"}
    if _simulado():
        return {"ok": True, "simulado": True}
    if _cmd(["nmcli", "connection", "delete", ssid]) is None:
        return {"ok": False, "error": "no se pudo olvidar la red (¿existe?)"}
    return {"ok": True}


def wifi_abrir_portal() -> dict:
    """Recuperación (§3.4): baja el WiFi actual y arranca `kaitosan-wifi-connect`
    para reconfigurar la red desde el portal «Kaitosan-Setup». Tumba la sesión.
    """
    if _simulado():
        return {"ok": True, "simulado": True,
                "mensaje": ("En la Pi se abriría ahora el portal «Kaitosan-Setup»: "
                            "conéctate a esa red WiFi desde el móvil para elegir "
                            "una red.")}

    def _worker():
        time.sleep(0.5)                            # deja responder al fetch
        actual = wifi_estado().get("ssid")
        if actual:
            _cmd(["nmcli", "connection", "down", actual], timeout=30)
        _cmd(["sudo", "-n", "systemctl", "start", "kaitosan-wifi-connect"], timeout=30)

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True,
            "mensaje": ("Abriendo el portal «Kaitosan-Setup». Esta página se "
                        "desconectará: conéctate a esa red WiFi desde el móvil "
                        "para configurar una red nueva.")}


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


# Subcadenas de dispositivos ALSA que NO son tarjetas físicas elegibles: plugins
# y salidas virtuales de ALSA/Pulse, más el audio integrado de la Raspberry (HDMI
# y minijack) que este montaje no usa. Todo lo demás sí se muestra: un micro USB,
# o un altavoz/DAC I2S conectado a los pines (hifiberry, max98357a, voicecard...).
# ponytail: denylist por subcadena; ajústala si cuela ruido o falta una tarjeta.
_AUDIO_OCULTAR_HINTS = (
    "sysdefault", "default", "pulse", "pipewire", "dmix", "dsnoop",
    "samplerate", "speexrate", "upmix", "vdownmix", "dummy", "jack", "oss",
    "hdmi", "vc4-hdmi", "vc4hdmi", "bcm2835",
    "surround", "iec958", "spdif", "null", "front:", "center_lfe", "side:",
)


def _audio_oculto(nombre: str) -> bool:
    n = (nombre or "").lower()
    return any(h in n for h in _AUDIO_OCULTAR_HINTS)


def _audio_dispositivos_reales(entrada: bool) -> list:
    """Enumera tarjetas de audio con `sounddevice` (reutiliza la autodetección
    del resto del proyecto). Devuelve [] si `sounddevice` no está disponible.

    Se descartan los plugins virtuales de ALSA y el audio integrado de la
    Raspberry (HDMI / minijack); quedan las tarjetas reales conectadas (USB o
    DAC/altavoz por los pines) y la que esté seleccionada ahora mismo."""
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
            if _audio_oculto(nombre) and not (pref and pref in nombre.lower()):
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
        candidatos = [
            (i, (d.get("name") or "").lower())
            for i, d in enumerate(sd.query_devices())
            if d.get(clave, 0) > 0
        ]
    except Exception:  # noqa: BLE001
        return None
    # Coincidencia exacta antes que por subcadena (evita colarse en otro
    # dispositivo cuyo nombre contenga el mismo texto).
    for i, nombre in candidatos:
        if nombre == pref:
            return i
    for i, nombre in candidatos:
        if pref in nombre:
            return i
    return None


def _portaudio_tiene_pulse() -> bool:
    """¿`sounddevice` puede enrutar por el servidor de sonido (PulseAudio/PipeWire)?
    Sin ese puente NO se puede reproducir por un altavoz Bluetooth, así que no
    tiene sentido ofrecerlos como salida elegible."""
    try:
        import sounddevice as sd
        for d in sd.query_devices():
            n = (d.get("name") or "").lower()
            if ("pulse" in n or "pipewire" in n) and d.get("max_output_channels", 0) > 0:
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


def audio_salidas() -> list:
    """[{id, nombre, en_uso, bt_mac?}] — tarjetas de salida + altavoces BT conectados.

    Los altavoces Bluetooth conectados ahora mismo se añaden como salida
    elegible (§5 nota Bluetooth). Llevan `bt_mac` para poder volver a la tarjeta
    local si el dispositivo se apaga (ver `audio_salida_preferida()`).
    """
    guardada = (settings_get("audio_output") or "").strip()
    if _simulado():
        salidas = [{**s, "en_uso": s["id"] == guardada} for s in _AUDIO_SALIDAS_FAKE]
        for d in _BT_ESTADO_FAKE["conectados"]:
            if d["tipo"] == "audio":
                salidas.append({"id": d["nombre"], "nombre": d["nombre"] + " (Bluetooth)",
                                "en_uso": d["nombre"] == guardada, "bt_mac": d["mac"]})
        return salidas

    salidas = _audio_dispositivos_reales(entrada=False)
    # Altavoces Bluetooth: solo si `sounddevice` tiene puente con el servidor de
    # sonido; si no, no se puede reproducir por ellos y no se ofrecen.
    if _portaudio_tiene_pulse():
        nombres = {s["id"].lower() for s in salidas}
        for d in _bt_audio_conectados():
            if d["nombre"].lower() not in nombres:
                salidas.append({"id": d["nombre"], "nombre": d["nombre"] + " (Bluetooth)",
                                "en_uso": bool(guardada) and guardada == d["nombre"],
                                "bt_mac": d["mac"]})
    return salidas


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
    salidas = audio_salidas()
    if valor and valor not in {s["id"] for s in salidas}:
        return {"ok": False, "error": "dispositivo de salida desconocido"}
    settings_set("audio_output", valor)
    # Recuerda si la salida elegida es un altavoz Bluetooth, para poder caer a la
    # tarjeta local cuando se apague / salga de rango (§5 nota Bluetooth).
    bt_mac = next((s.get("bt_mac", "") for s in salidas if s["id"] == valor), "")
    settings_set("audio_output_bt_mac", bt_mac or "")
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
    `AUDIO_OUTPUT_HINT` del `.env` (que pasa a ser semilla / override de fábrica).

    Si la preferencia guardada es un altavoz Bluetooth que ahora mismo no está
    conectado (apagado / fuera de rango), se ignora y se cae a la tarjeta local
    (§5 nota Bluetooth, "fallback obligatorio")."""
    guardada = (settings_get("audio_output") or "").strip()
    if guardada:
        bt_mac = (settings_get("audio_output_bt_mac") or "").strip()
        if not bt_mac or _bt_mac_conectado(bt_mac):
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


def _primer_micro_real():
    """Primer dispositivo de captura 'real' (USB o tarjeta por los pines),
    saltándose los plugins de ALSA y el audio integrado. -> índice o None."""
    try:
        import sounddevice as sd
        for i, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0 and not _audio_oculto(d.get("name") or ""):
                return i
    except Exception:  # noqa: BLE001
        pass
    return None


def _sr_dispositivo(dev, entrada: bool) -> int:
    """Sample rate por defecto del dispositivo: no forzamos uno que no acepte
    (un micro USB suele ser 48000, no 44100 -> InputStream con -9985/-9997)."""
    try:
        import sounddevice as sd
        info = sd.query_devices(dev, "input" if entrada else "output")
        return int(info.get("default_samplerate") or 48000)
    except Exception:  # noqa: BLE001
        return 48000


def _msg_audio_error(accion: str, e: Exception) -> str:
    s = str(e).lower()
    if "-9985" in s or "-9996" in s or "unavailable" in s or "no default" in s:
        return (f"no se pudo {accion}: el dispositivo de audio no está disponible "
                "(¿está conectado y elegido en el desplegable de dispositivos? "
                "¿lo está usando Kaito u otra app ahora mismo?)")
    return f"no se pudo {accion}: {e}"


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
        pref = audio_salida_preferida()
        dev = _resolver_indice(pref, entrada=False)
        try:
            if dev is not None:
                nombre = sd.query_devices(dev)["name"]
            elif pref:
                nombre = f"predeterminado del sistema («{pref}» no está disponible)"
            else:
                nombre = "predeterminado del sistema"
        except Exception:  # noqa: BLE001
            nombre = str(dev)
        sr = _sr_dispositivo(dev, entrada=False)
        dur = 1.0
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        mono = (0.35 * np.sin(2 * np.pi * 660 * t)).astype("float32")
        # Estéreo: los DAC I2S (HifiBerry / PCM5102A) suelen exigir 2 canales;
        # con 1 canal el `hw:` no reproduce nada aunque no dé error.
        tono = np.column_stack([mono, mono])
        sd.play(tono, sr, device=dev)
        sd.wait()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": _msg_audio_error("reproducir el tono", e)}
    return {"ok": True, "dispositivo": nombre}


def audio_probar_micro() -> dict:
    """Graba 2 s por el micrófono activo y los reproduce por la salida activa.
    Resuelve el micro igual que el grabador real (audio.recorder)."""
    if _simulado():
        return {"ok": True, "simulado": True}
    try:
        import sounddevice as sd
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"audio no disponible: {e}"}
    try:
        from audio.recorder import buscar_microfono
        dev_in = buscar_microfono()
    except Exception:  # noqa: BLE001
        dev_in = _resolver_indice(audio_entrada_preferida(), entrada=True)
    # Si no hay micro elegido o se resolvió a un plugin de ALSA / el audio
    # integrado (que no captura -> -9985), usa la 1ª tarjeta de captura real.
    try:
        nombre = sd.query_devices(dev_in)["name"] if dev_in is not None else ""
    except Exception:  # noqa: BLE001
        nombre = ""
    if dev_in is None or _audio_oculto(nombre):
        alt = _primer_micro_real()
        if alt is not None:
            dev_in = alt
    # Ni preferencia válida ni ninguna tarjeta de captura: no hay micro.
    if dev_in is None and _primer_micro_real() is None:
        return {"ok": False, "error": "no se detecta ningún micrófono conectado "
                "(ninguna tarjeta de captura; revisa el cable USB o `arecord -l`)"}
    try:
        sr = _sr_dispositivo(dev_in, entrada=True)
        grab = sd.rec(int(sr * 2), samplerate=sr, channels=1, dtype="float32", device=dev_in)
        sd.wait()
        dev_out = _resolver_indice(audio_salida_preferida(), entrada=False)
        import numpy as np
        estereo = np.column_stack([grab[:, 0], grab[:, 0]])  # DAC I2S: 2 canales
        sd.play(estereo, sr, device=dev_out)
        sd.wait()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": _msg_audio_error("probar el micrófono", e)}
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Bluetooth (BlueZ / bluetoothctl) — Fase 14 (§2.1, §5 nota Bluetooth, §6.7)
# --------------------------------------------------------------------------- #
# `bluetoothctl` de Bookworm (bluez 5.66) acepta subcomandos no interactivos:
#   show | power on|off | --timeout N scan on | devices [Paired|Connected]
#   info <mac> | pair <mac> | trust <mac> | connect <mac> | disconnect <mac>
#   remove <mac>
# Siempre como lista de argumentos, nunca `shell=True` (§5).
_RE_MAC = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")

_BT_ESTADO_FAKE = {
    "adaptador_on": True,
    "conectados": [
        {"mac": "AA:BB:CC:11:22:33", "nombre": "Altavoz salón", "tipo": "audio"},
    ],
}
_BT_ESCANEO_FAKE = [
    {"mac": "AA:BB:CC:11:22:33", "nombre": "Altavoz salón", "tipo": "audio",
     "emparejado": True,  "conectado": True,  "rssi": -47},
    {"mac": "DE:AD:BE:EF:00:01", "nombre": "JBL Go 3", "tipo": "audio",
     "emparejado": False, "conectado": False, "rssi": -63},
    {"mac": "12:34:56:78:9A:BC", "nombre": "Mi Band 7", "tipo": "otro",
     "emparejado": False, "conectado": False, "rssi": -71},
]


def _mac_valida(mac) -> bool:
    return bool(_RE_MAC.match((mac or "").strip()))


def _bt(args: list, timeout: int = 15):
    """`bluetoothctl <args...>` -> stdout (str) o None."""
    return _cmd(["bluetoothctl", *args], timeout=timeout)


def _bt_tipo(info: str) -> str:
    """Clasifica un dispositivo a partir de la salida de `bluetoothctl info`."""
    txt = (info or "").lower()
    if ("icon: audio" in txt or "audio sink" in txt or "a2dp" in txt
            or "headset" in txt or "handsfree" in txt):
        return "audio"
    m = re.search(r"icon:\s*(\S+)", txt)
    if m:
        return {"input-mouse": "ratón", "input-keyboard": "teclado",
                "phone": "teléfono", "computer": "ordenador"}.get(m.group(1), "otro")
    return "otro"


def _bt_parse_info(mac: str) -> dict:
    """`bluetoothctl info <mac>` -> {mac, nombre, tipo, emparejado, conectado, rssi}."""
    info = _bt(["info", mac], timeout=10) or ""
    m = re.search(r"^\s*(?:Name|Alias):\s*(.+)$", info, re.MULTILINE)
    nombre = m.group(1).strip() if m else mac
    m = re.search(r"RSSI:\s*(-?\d+)", info)
    rssi = int(m.group(1)) if m else None
    return {
        "mac": mac,
        "nombre": nombre,
        "tipo": _bt_tipo(info),
        "emparejado": bool(re.search(r"Paired:\s*yes", info)),
        "conectado": bool(re.search(r"Connected:\s*yes", info)),
        "rssi": rssi,
    }


def _bt_listar(filtro: str = "") -> list:
    """MACs conocidas por BlueZ. `filtro` opcional: 'Paired' o 'Connected'."""
    salida = _bt(["devices", filtro] if filtro else ["devices"])
    if salida is None and filtro:                 # bluez viejo sin filtro
        salida = _bt(["devices"])
    macs = []
    for linea in (salida or "").splitlines():
        m = re.match(r"Device\s+(\S+)", linea.strip())
        if m and _mac_valida(m.group(1)):
            macs.append(m.group(1))
    return macs


def bt_estado() -> dict:
    """{adaptador_on: bool, conectados: [{mac, nombre, tipo}]}"""
    if _simulado():
        return json.loads(json.dumps(_BT_ESTADO_FAKE))     # copia defensiva

    show = _bt(["show"]) or ""
    adaptador_on = bool(re.search(r"Powered:\s*yes", show))
    conectados = []
    if adaptador_on:
        for mac in _bt_listar("Connected"):
            d = _bt_parse_info(mac)
            if d["conectado"]:
                conectados.append({"mac": d["mac"], "nombre": d["nombre"],
                                   "tipo": d["tipo"]})
    return {"adaptador_on": adaptador_on, "conectados": conectados}


def bt_radio(on: bool) -> dict:
    """Enciende / apaga el adaptador Bluetooth (`bluetoothctl power on|off`)."""
    if _simulado():
        return {"ok": True, "simulado": True}
    # Al encender, primero quita un posible bloqueo por rfkill (típico en la Pi).
    if on:
        _cmd(["rfkill", "unblock", "bluetooth"])

    # `org.bluez.Error.Busy` suele ser transitorio (adaptador inicializándose):
    # reintenta una vez tras una pausa breve.
    salida = ""
    for intento in range(3):
        try:
            p = subprocess.run(
                ["bluetoothctl", "power", "on" if on else "off"],
                capture_output=True, text=True, timeout=15,
            )
        except FileNotFoundError:
            return {"ok": False, "error": "bluetoothctl no está instalado"}
        except (subprocess.TimeoutExpired, OSError) as e:
            return {"ok": False, "error": f"no se pudo cambiar el adaptador Bluetooth: {e}"}
        salida = (p.stdout + p.stderr).strip()
        baja = salida.lower()
        if "succeeded" in baja or (p.returncode == 0 and "fail" not in baja):
            return {"ok": True}
        if "busy" in baja and intento < 2:
            time.sleep(1.2)
            continue
        break
    baja = salida.lower()

    if "busy" in baja:
        detalle = ("el adaptador está ocupado (otro gestor lo controla o aún se está "
                   "iniciando). Prueba `sudo systemctl restart bluetooth` y reintenta")
    elif "no default controller" in baja:
        detalle = "no hay controlador Bluetooth (¿está `bluetooth.service` activo y el hardware habilitado?)"
    elif "blocked" in baja:
        detalle = "el adaptador está bloqueado (rfkill). Ejecuta `sudo rfkill unblock bluetooth`"
    elif "denied" in baja or "not authorized" in baja:
        detalle = "permiso denegado: el usuario del panel debe estar en el grupo `bluetooth`"
    else:
        detalle = salida.splitlines()[-1] if salida else f"código {p.returncode}"
    return {"ok": False, "error": f"no se pudo cambiar el adaptador Bluetooth: {detalle}"}


def bt_escanear(seg: int = 10) -> list:
    """Descubre dispositivos cercanos.

    [{mac, nombre, tipo, emparejado, conectado, rssi}] ordenado por señal.
    """
    try:
        seg = max(3, min(30, int(seg)))
    except (TypeError, ValueError):
        seg = 10
    if _simulado():
        return json.loads(json.dumps(_BT_ESCANEO_FAKE))

    _bt(["--timeout", str(seg), "scan", "on"], timeout=seg + 12)
    dispositivos = [_bt_parse_info(mac) for mac in dict.fromkeys(_bt_listar())]
    dispositivos.sort(key=lambda d: (d["rssi"] is None, -(d["rssi"] or -999)))
    return dispositivos


def bt_emparejados() -> list:
    """Dispositivos ya emparejados -> [{mac, nombre, tipo, emparejado, conectado, rssi}]."""
    if _simulado():
        return [d for d in json.loads(json.dumps(_BT_ESCANEO_FAKE)) if d["emparejado"]]
    return [_bt_parse_info(mac) for mac in _bt_listar("Paired")]


def bt_conectar(mac: str) -> dict:
    """Empareja, marca como de confianza y conecta, en ese orden (§5)."""
    if not _mac_valida(mac):
        return {"ok": False, "error": "dirección Bluetooth no válida"}
    mac = mac.strip()
    if _simulado():
        return {"ok": True, "simulado": True, "es_audio": True,
                "mensaje": "En la Pi se emparejaría y conectaría el dispositivo."}

    _bt(["pair", mac], timeout=30)                 # puede fallar si ya está emparejado
    _bt(["trust", mac], timeout=10)
    _bt(["connect", mac], timeout=30)

    d = _bt_parse_info(mac)
    if not d["conectado"]:
        return {"ok": False, "error": "no se pudo conectar con el dispositivo"}
    es_audio = d["tipo"] == "audio"
    return {
        "ok": True,
        "es_audio": es_audio,
        "mensaje": ("Conectado. Ya puedes elegirlo como altavoz en «Sonido»."
                    if es_audio else "Dispositivo conectado."),
    }


def bt_desconectar(mac: str) -> dict:
    """Desconecta un dispositivo sin borrar el emparejamiento."""
    if not _mac_valida(mac):
        return {"ok": False, "error": "dirección Bluetooth no válida"}
    if _simulado():
        return {"ok": True, "simulado": True}
    if _bt(["disconnect", mac.strip()], timeout=20) is None:
        return {"ok": False, "error": "no se pudo desconectar"}
    return {"ok": True}


def bt_olvidar(mac: str) -> dict:
    """`bluetoothctl remove <mac>` — borra el emparejamiento."""
    if not _mac_valida(mac):
        return {"ok": False, "error": "dirección Bluetooth no válida"}
    if _simulado():
        return {"ok": True, "simulado": True}
    if _bt(["remove", mac.strip()], timeout=15) is None:
        return {"ok": False, "error": "no se pudo olvidar el dispositivo"}
    return {"ok": True}


def _bt_audio_conectados() -> list:
    """[{mac, nombre, tipo}] de los dispositivos de audio BT conectados ahora."""
    try:
        return [d for d in bt_estado().get("conectados", []) if d["tipo"] == "audio"]
    except Exception:  # noqa: BLE001 — la capa de sistema nunca propaga
        return []


def _bt_mac_conectado(mac: str) -> bool:
    """True si `mac` está conectado ahora mismo (fallback de audio, §5)."""
    if not _mac_valida(mac):
        return False
    if _simulado():
        return any(d["mac"] == mac for d in _BT_ESTADO_FAKE["conectados"])
    return bool(re.search(r"Connected:\s*yes", _bt(["info", mac.strip()], timeout=8) or ""))


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


# Salvapantallas: minutos de inactividad antes de mostrar solo el reloj.
# Se guarda en `app_settings`; el front del /reloj lo consume (§Fase pantalla).
_INACTIVIDAD_DEFECTO = 5


def pantalla_inactividad_get() -> int:
    """Minutos de inactividad para el salvapantallas del /reloj. 1..120."""
    try:
        n = int((settings_get("screensaver_min") or "").strip())
    except (TypeError, ValueError):
        return _INACTIVIDAD_DEFECTO
    return max(1, min(120, n))


def pantalla_inactividad_set(valor) -> dict:
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        return {"ok": False, "error": "valor de inactividad no válido"}
    if not 1 <= n <= 120:
        return {"ok": False, "error": "los minutos deben estar entre 1 y 120"}
    settings_set("screensaver_min", str(n))
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


def reset_fabrica() -> dict:
    """Reset de fábrica: copia de la BD -> borra BD, claves de `app_settings` y
    conexiones de NetworkManager -> vuelve al onboarding (§5, §11). Irreversible;
    la UI exige doble confirmación y ofrece descargar una copia antes.

    Fuera de la Pi (simulado) hace la copia de seguridad y **no borra nada**.
    """
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
