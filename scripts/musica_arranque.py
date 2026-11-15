#!/usr/bin/env python3
"""Música de carga (la lanza deploy/kaito-arranque.service).

Suena entera; si recibe SIGUSR1 (la cara ya está en pantalla) baja el volumen
hasta cero en FADE s y termina. Decodifica con ffmpeg y toca con aplay: el DAC
no tiene mezclador, así que el fundido se hace sobre las muestras.
"""
import os
import signal
import sqlite3
import subprocess
import sys
import time

import numpy as np

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kaito.db")


def volumen_guardado() -> float:
    """El volumen de Ajustes (guardado antes de apagar), con la misma curva que la voz
    (core/system_settings.volumen_factor): (porcentaje/100)². 1.0 si no hay nada guardado."""
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=2)
        fila = con.execute("SELECT value FROM app_settings WHERE key='volumen_sw'").fetchone()
        con.close()
        return (max(0.0, min(100.0, float(fila[0]))) / 100) ** 2 if fila else 1.0
    except Exception:  # noqa: BLE001 — sin BD o sin tabla: a todo volumen, como antes
        return 1.0


VOLUMEN = 0.7 * volumen_guardado()  # la música, un 70 % del volumen de Ajustes
FADE = 5.0  # el baile de la cara dura 4,5 s: acaba antes que la música
DEV = "hw:CARD=sndrpihifiberry,DEV=0"
RATE, CH = 48000, 2
CHUNK = RATE // 10 * CH * 2  # 0,1 s de s16

fade_ini = None


def _usr1(*_):
    global fade_ini
    if fade_ini is None:
        fade_ini = time.monotonic()


def _pausa(*_):  # USR2: suelta el altavoz (la app lo necesita libre para detectarlo)
    global pausa
    pausa = True


def _sigue(*_):  # HUP: vuelve a sonar
    global pausa
    pausa = False


pausa = False
signal.signal(signal.SIGUSR1, _usr1)
signal.signal(signal.SIGUSR2, _pausa)
signal.signal(signal.SIGHUP, _sigue)
dec = subprocess.Popen(["ffmpeg", "-nostdin", "-loglevel", "quiet", "-i", sys.argv[1],
                        "-f", "s16le", "-ar", str(RATE), "-ac", str(CH), "-"],
                       stdout=subprocess.PIPE)
def abrir():
    """Arranca con el sistema, antes de que exista la tarjeta: reintenta hasta que
    aplay se quede abierto (la tarjeta tarda unos segundos en aparecer)."""
    for _ in range(100):
        p = subprocess.Popen(["aplay", "-q", "-D", DEV, "-t", "raw", "-f", "S16_LE",
                              "-r", str(RATE), "-c", str(CH)], stdin=subprocess.PIPE)
        time.sleep(0.12)
        if p.poll() is None:
            print(f"música: suena a los {float(open('/proc/uptime').read().split()[0]):.1f} s del arranque", flush=True)
            return p
    sys.exit(1)


out = abrir()
try:
    while True:
        buf = dec.stdout.read(CHUNK)
        if not buf:
            break
        if pausa:
            out.kill()  # no cerrar la entrada: aplay terminaría de tocar lo que tiene en cola
            out.wait()
            while pausa:
                time.sleep(0.05)
            out = abrir()
        g = VOLUMEN
        if fade_ini is not None:
            g *= 1 - (time.monotonic() - fade_ini) / FADE
            if g <= 0:
                break
        buf = (np.frombuffer(buf, np.int16) * g).astype(np.int16).tobytes()
        out.stdin.write(buf)
except BrokenPipeError:
    pass
finally:
    dec.kill()
    if fade_ini is not None:
        out.kill()  # tras el fundido ya es silencio: que suelte el altavoz sin acabar de vaciar su cola
    try:
        out.stdin.close()
    except OSError:
        pass
    out.wait()
