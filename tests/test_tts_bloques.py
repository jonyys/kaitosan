"""Fase 05 — un bloque 【】 es un solo segmento de voz japonesa."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# El entorno de test no tiene las dependencias de audio (solo la Raspberry).
for _mod in ("edge_tts", "sounddevice", "soundfile", "numpy"):
    try:
        __import__(_mod)
    except ImportError:
        sys.modules[_mod] = MagicMock()

from ai.text_to_speech import TextToSpeech

# Sin __init__: no hay tarjeta de sonido en el entorno de test.
tts = TextToSpeech.__new__(TextToSpeech)
tts.voice_es = "es-ES-AlvaroNeural"
tts.voice_ja = "ja-JP-KeitaNeural"

CASOS = [
    ("【ねこ】", "ねこ"),
    ("【〜ます】", "〜ます"),
    ("【みずをください。】",
     "みずをください。"),
    ("【こんにちは、ラウラさん】",
     "こんにちは、ラウラさん"),
]


def test_cada_bloque_es_un_solo_segmento():
    for texto, esperado in CASOS:
        segs = tts._dividir_texto(texto)
        assert segs == [(esperado, tts.voice_ja)], (texto, segs)


def test_el_bloque_no_contamina_la_voz_espanola():
    # El bloque sale entero por la voz japonesa y el español va aparte.
    texto = "Repite conmigo: 【みずをください。】 y ya está."
    segs = tts._dividir_texto(texto)
    voces = [v for _, v in segs]
    assert voces == [tts.voice_es, tts.voice_ja, tts.voice_es], segs
    assert segs[1][0] == "みずをください。"


if __name__ == "__main__":
    test_cada_bloque_es_un_solo_segmento()
    test_el_bloque_no_contamina_la_voz_espanola()
    print("OK")
