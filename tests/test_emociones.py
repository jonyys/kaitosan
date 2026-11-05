"""Emoción de la cara a partir de la respuesta del LLM, y el "gracias" sin voz."""
import pytest

from core.emociones import es_solo_gracias, extraer_emocion


@pytest.mark.parametrize("entrada, emocion, texto", [
    ("[feliz] ¡Claro que sí!", "feliz", "¡Claro que sí!"),
    ("[Feliz]¡Claro!", "feliz", "¡Claro!"),
    ("[cariño] Te quiero mucho.", "carino", "Te quiero mucho."),
    ("**[triste]** Vaya, lo siento.", "triste", "Vaya, lo siento."),
    ("[Emoción: bromista] Pues no tengo estómago.", "bromista", "Pues no tengo estómago."),
    ("[contento] Genial.", "feliz", "Genial."),
    ("(sorprendido) ¿En serio?", "sorpresa", "¿En serio?"),
    ("¡Qué bien! [feliz]", "feliz", "¡Qué bien!"),
    ("[neutral] Son las cinco.", None, "Son las cinco."),
    ("Son las cinco.", None, "Son las cinco."),
    ("[pensando en voz alta] Mmm.", None, "Mmm."),
    ("He encontrado esto: [resultado] y más.", None, "He encontrado esto: [resultado] y más."),
    ("Hola (bueno, más o menos) qué tal", None, "Hola (bueno, más o menos) qué tal"),
    ("", None, ""),
])
def test_extraer_emocion(entrada, emocion, texto):
    assert extraer_emocion(entrada) == (emocion, texto)


def test_solo_cuenta_la_primera_etiqueta():
    assert extraer_emocion("[feliz] Hola. [triste] Adiós.") == ("feliz", "Hola. Adiós.")


@pytest.mark.parametrize("texto", [
    "Gracias", "gracias.", "¡Muchas gracias!", "Muchísimas gracias, Kaito",
    "vale, gracias", "Gracias por todo", "mil gracias", "Arigatou", "arigato gozaimasu",
    "thank you", "gracias guapo",
])
def test_es_solo_gracias(texto):
    assert es_solo_gracias(texto)


@pytest.mark.parametrize("texto", [
    "", "hola", "gracias, ¿y qué tiempo hace mañana?", "dale las gracias a mi madre",
    "gracias pero no era eso", "de nada",
])
def test_no_es_solo_gracias(texto):
    assert not es_solo_gracias(texto)


def test_gracias_elige_gestos_buenos_que_existen_y_no_repite():
    from pathlib import Path
    import re
    from core.emociones import GESTOS_GRACIAS, gesto_para_gracias

    motor = Path("templates/partials/face/_scripts.html").read_text(encoding="utf-8")
    kawaii = motor[motor.index("const KAWAII = {"):motor.index("function sortearKawaii")]
    for g in GESTOS_GRACIAS:
        assert re.search(rf"^\s+{g}: \{{", kawaii, re.M), g
    assert not {"dormirse", "apuro", "sorpresa"} & set(GESTOS_GRACIAS)

    vistos, anterior = set(), None
    for _ in range(300):
        g = gesto_para_gracias()
        assert g != anterior
        vistos.add(g)
        anterior = g
    assert vistos == set(GESTOS_GRACIAS)
