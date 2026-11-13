"""Modo tamagotchi: bajada con el tiempo, objetos, juegos, yenes y tienda (BD temporal)."""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.memory
import core.settings_store as ss

ss.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
ss._inicializada = False
from core import tamagotchi as t

B = time.mktime((2026, 1, 5, 8, 0, 0, 0, 0, -1))  # las 8:00 de un día: +5 h sigue siendo el mismo día
H = 3600


def _de_cero():
    ss.settings_set("tamagotchi_estado", "")
    t.estado(B)  # arranca el reloj


def test_apagado_no_hace_nada():
    assert not t.activo()
    assert t.ganar("clase") is None and not t.dar("onigiri") and not t.comprar("onigiri")
    assert t.ganar_yenes(50) == 0 and t.cobrar_practica(5) == 0
    t.set_activo(True)


def test_ritmos_de_bajada():
    # de 100 a 0: hambre en 3 días, sed en 2 y ánimo en 5
    assert round(100 / t.BAJADA_H["hambre"]) == 72
    assert round(100 / t.BAJADA_H["sed"]) == 48
    assert round(100 / t.BAJADA_H["animo"]) == 120
    _de_cero()
    e = t.estado(B + 12 * H)
    assert e["hambre"] == round(80 - 12 * 100 / 72) and e["sed"] == round(80 - 12 * 100 / 48)
    assert all(t.estado(B + 500 * H)[k] == 0 for k in ("hambre", "sed", "animo"))   # nunca baja de 0


def test_comida_y_regalo():
    _de_cero()
    assert t.estado(B)["objetos"]["onigiri"] == 2
    assert t.dar("onigiri", B) and t.dar("onigiri", B) and not t.dar("onigiri", B)   # solo había 2
    assert t.ganar("clase") in t.OBJETOS
    antes = sum(t.estado(B + 100 * H)["objetos"].values())
    assert sum(t.estado(B + 101 * H)["objetos"].values()) == antes        # mismo día: sin regalo
    assert sum(t.estado(B + 130 * H)["objetos"].values()) == antes + 1    # día nuevo: 1 regalo
    por_cat = [sum(o["cat"] == c for o in t.OBJETOS.values()) for c in ("comida", "bebida", "juego")]
    assert por_cat == [6, 5, 4], por_cat   # 5 comidas + el arroz con bogavante, 5 bebidas, 4 juegos


def test_juegos_no_se_gastan_y_cansan():
    _de_cero()
    assert t.dar("kendama", B) and t.dar("kendama", B) and "kendama" not in t.estado(B)["objetos"]
    e = t.estado(B)
    assert e["animo"] == 100 and e["hambre"] == 70 and e["sed"] == 70   # 80 +20 +20 (tope 100) / 80 -5 -5


def test_bogavante_raro_y_mucho_mejor():
    assert "ebigohan" not in t.COMUNES                          # nunca sale en el regalo diario
    _de_cero()
    assert not t.dar("ebigohan", B)                             # no se tiene de inicio
    ss.settings_set("tamagotchi_estado", "")
    t.estado(B)
    assert t.ganar_yenes(900, B) == 900 and t.comprar("ebigohan", B)
    assert t.estado(B)["yenes"] == 100
    assert t.dar("ebigohan", B)
    e = t.estado(B)
    assert e["hambre"] == 100 and e["animo"] == 100 and e["sed"] == 100   # todo sube hasta el tope
    assert t.OBJETOS["ebigohan"]["sube"]["hambre"] > 2 * max(
        o["sube"].get("hambre", 0) for k, o in t.OBJETOS.items() if k != "ebigohan")


def test_yenes_y_tienda():
    _de_cero()
    assert t.estado(B)["yenes"] == 0 and not t.comprar("ramen", B)      # sin dinero
    assert t.cobrar_practica(5, B) == 5 and t.cobrar_practica(3, B) == 3 and t.cobrar_practica(1, B) == 0
    assert t.estado(B)["yenes"] == 8
    # una clase: 20 + 60 por can-do + 30 si era nuevo + 8 por palabra (hasta 5)
    assert t.pago_clase(0, 0, 0) == 20 and t.pago_clase(2, 1, 3) == 20 + 120 + 30 + 24
    assert t.pago_clase(1, 0, 9) == 20 + 60 + 40
    assert t.cobrar_clase(1, 1, 2, B) == 20 + 60 + 30 + 16
    y = t.estado(B)["yenes"]
    assert t.comprar("mizu", B) and t.estado(B)["yenes"] == y - 10 and t.estado(B)["objetos"]["mizu"] == 2
    assert not t.comprar("kendama", B)                                  # los juegos no se venden
    assert not t.comprar("nada", B)


def test_hablarle_sube_el_animo():
    _de_cero()
    t.animar(3, B)
    assert t.estado(B)["animo"] == 83
    t.animar(50, B)
    assert t.estado(B)["animo"] == 100
    t.set_activo(False)
    t.animar(3, B)  # apagado: no hace nada
    t.set_activo(True)


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f()
    print("ok")
