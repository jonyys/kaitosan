"""Fase 06 — la producción explícita gana a la pista de comprensión."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.profesor import _extraer_frase_objetivo, _partir_objetivo_centinela

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
    # Frase-función N5 con kanji ligero (もう一度/お願い) SÍ es objetivo, y si viene
    # partida en bloques adyacentes se junta entera.
    ("Ahora repite: " + B % "ちょっと" + "…" + B % "もう一度お願いします" + ".",
     "ちょっと もう一度お願いします"),
    ("Di conmigo: " + B % "もう一度お願いします", "もう一度お願いします"),
    # Bloques separados por texto real → solo el último.
    ("Repite " + B % "はれた" + " y luego, cuando quieras, " + B % "くもり",
     "くもり"),
]


def test_pistas_de_produccion_y_comprension():
    for texto, esperado in CASOS:
        assert _extraer_frase_objetivo(texto) == esperado, (texto, esperado)


def test_centinela_objetivo():
    # Caso normal: se separa la línea y se queda la forma canónica.
    limpia, obj = _partir_objetivo_centinela(
        "Muy bien. Ahora dilo todo junto, con calma.\n"
        "@@OBJETIVO: ちょっと、もう一度お願いします@@"
    )
    assert limpia == "Muy bien. Ahora dilo todo junto, con calma.", repr(limpia)
    assert obj == "ちょっと、もう一度お願いします", repr(obj)

    # Con 【】 dentro del centinela: se limpian.
    _, obj = _partir_objetivo_centinela("Repite: 【はれた】 @@ OBJETIVO : 【はれた】 @@")
    assert obj == "はれた", repr(obj)

    # Sin centinela: no toca la respuesta, objetivo None (cae a la heurística).
    limpia, obj = _partir_objetivo_centinela("Repite: 【ねこ】")
    assert (limpia, obj) == ("Repite: 【ねこ】", None)

    # Centinela vacío → None, no cadena vacía.
    _, obj = _partir_objetivo_centinela("Hola @@OBJETIVO: @@")
    assert obj is None

    # El modelo se deja el "@@" de cierre: aun así se separa y no se habla.
    limpia, obj = _partir_objetivo_centinela(
        "¿Me lo dices todo junto ahora?\n@@OBJETIVO: 【ちょっと】"
    )
    assert limpia == "¿Me lo dices todo junto ahora?", repr(limpia)
    assert obj == "ちょっと", repr(obj)

    # Centinela sin cierre y vacío: se recorta igual, objetivo None.
    limpia, obj = _partir_objetivo_centinela("Dime la frase entera. @@OBJETIVO:")
    assert limpia == "Dime la frase entera.", repr(limpia)
    assert obj is None


if __name__ == "__main__":
    test_pistas_de_produccion_y_comprension()
    test_centinela_objetivo()
    print("OK")
