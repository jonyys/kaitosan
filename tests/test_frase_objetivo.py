"""Fase 06 — la producción explícita gana a la pista de comprensión."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.profesor import _extraer_frase_objetivo

NEKO = "ねこ"
MIZU = "みず"
B = "【%s】"

CASOS = [
    # (turno del profesor, frase objetivo esperada)
    ("Repite conmigo: " + B % NEKO, NEKO),                      # ya funcionaba
    ("¿Cómo se dice 'agua'? " + B % MIZU, MIZU),     # ya funcionaba
    ("¿Entiendes qué significa " + B % NEKO + "?", None),  # sin producción
    ("Repite conmigo, ¿vale?: " + B % NEKO, NEKO),        # antes daba None
    # Con kanji NO es objetivo de pronunciación (nombre de unidad colado).
    ("Hoy practicamos 「挨拶と基本表現」. Repite: " + B % NEKO, NEKO),
    ("Repite: 【今日は挨拶の練習】", None),
    ("Repite: 「はれた」", "はれた"),                      # kana entrecomillado sí
]


def test_pistas_de_produccion_y_comprension():
    for texto, esperado in CASOS:
        assert _extraer_frase_objetivo(texto) == esperado, (texto, esperado)


if __name__ == "__main__":
    test_pistas_de_produccion_y_comprension()
    print("OK")
