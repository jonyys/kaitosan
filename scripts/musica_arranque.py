#!/usr/bin/env python3
"""Música de carga (la lanza deploy/kaito-arranque.service).

Suena entera; si recibe SIGUSR1 (la cara ya está en pantalla) baja el volumen
hasta cero en FADE s y termina. Decodifica con ffmpeg y toca con aplay: el DAC
no tiene mezclador, así que el fundido se hace sobre las muestras.
"""
import signal
import subprocess
import sys
import time

import numpy as np

FADE = 4.0
DEV = "hw:CARD=sndrpihifiberry,DEV=0"
RATE, CH = 48000, 2
CHUNK = RATE // 10 * CH * 2  # 0,1 s de s16

fade_ini = None


def _usr1(*_):
    global fade_ini
    if fade_ini is None:
        fade_ini = time.monotonic()


signal.signal(signal.SIGUSR1, _usr1)
dec = subprocess.Popen(["ffmpeg", "-nostdin", "-loglevel", "quiet", "-i", sys.argv[1],
                        "-f", "s16le", "-ar", str(RATE), "-ac", str(CH), "-"],
                       stdout=subprocess.PIPE)
# Arranca con el sistema, antes de que exista la tarjeta: reintenta hasta que aplay
# se quede abierto (la tarjeta tarda unos segundos en aparecer).
for _ in range(100):
    out = subprocess.Popen(["aplay", "-q", "-D", DEV, "-t", "raw", "-f", "S16_LE",
                            "-r", str(RATE), "-c", str(CH)], stdin=subprocess.PIPE)
    time.sleep(0.25)
    if out.poll() is None:
        break
else:
    sys.exit(1)
try:
    while True:
        buf = dec.stdout.read(CHUNK)
        if not buf:
            break
        if fade_ini is not None:
            g = 1 - (time.monotonic() - fade_ini) / FADE
            if g <= 0:
                break
            buf = (np.frombuffer(buf, np.int16) * g).astype(np.int16).tobytes()
        out.stdin.write(buf)
except BrokenPipeError:
    pass
finally:
    dec.kill()
    try:
        out.stdin.close()
    except OSError:
        pass
    out.wait()
