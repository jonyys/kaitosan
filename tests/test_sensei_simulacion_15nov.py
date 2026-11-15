"""Fallos de la simulación del 15-nov (12 clases con Lauras simuladas)."""
from ai.sensei.curriculum import CURRICULUM
from ai.sensei.profesor import ProfesorJapones, _frases_japonesas


def test_frases_japonesas_quita_el_comentario_en_espanol():
    assert _frases_japonesas("Vale, ahora sí. これは わたしの いぬです。") == "これは わたしの いぬです。"
    assert _frases_japonesas("それは ペンです。 ¿Eso es lo que cerca tengo yo?") == "それは ペンです。"
    # kana citado dentro de una pregunta en español: no es un intento
    assert _frases_japonesas("Oye, ¿y どれ y どっち son lo mismo?") == ""


class _Mem:
    def __init__(self, prog):
        self.prog = prog

    def can_dos_progreso(self):
        return self.prog


def test_lo_empezado_de_la_unidad_siguiente_es_pendiente():
    # 2.ª clase: demostrativos casi dominados, partículas (unidad siguiente) empezadas ayer.
    demo = next(u for u in CURRICULUM if u["id"] == "demostrativos")
    part = next(u for u in CURRICULUM if u["id"] == "particulas_basicas")
    prog = {cd["id"]: {"estado": "dominado", "ultima_sesion": 1} for cd in demo["can_dos"]}
    prog.update({cd["id"]: {"estado": "en_progreso", "ultima_sesion": 1} for cd in part["can_dos"]})
    p = ProfesorJapones.__new__(ProfesorJapones)
    p.jap_memory, p._foco_unidad = _Mem(prog), demo
    p.clase = {"hechos": [], "nuevos": 0}
    cd, tipo = p._siguiente()
    assert tipo == "pendiente" and cd["id"] in {c["id"] for c in part["can_dos"]}  # antes: (None, None) → charla libre


def test_mezcla_solo_dentro_de_la_misma_frase():
    from ai.sensei.profesor import _frase_mezclada
    assert _frase_mezclada("けさ おきて, y luego desayuné")
    assert not _frase_mezclada("Vale, ahora sí. これは わたしの いぬです。")
    assert not _frase_mezclada("Oye, ¿y どれ y どっち son lo mismo?")
    assert not _frase_mezclada("しごと ya lo sabía, es trabajo.")  # citar y comentar no es mezcla
    assert not _frase_mezclada("Vale, creo que lo pillo: と pegado a una persona es con.")


def test_japones_detras_de_un_comentario_en_espanol():
    assert _frases_japonesas("Kaito, que lo he dicho bien: わたしの ちちは ホセです。") == "わたしの ちちは ホセです。"
    assert _frases_japonesas("Bebo agua: みずを のみます。") == "みずを のみます。"
