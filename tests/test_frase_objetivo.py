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
]


def test_pistas_de_produccion_y_comprension():
    for texto, esperado in CASOS:
        assert _extraer_frase_objetivo(texto) == esperado, (texto, esperado)


if __name__ == "__main__":
    test_pistas_de_produccion_y_comprension()
    print("OK")
