"""Modo tamagotchi: bajada con el tiempo, objetos y ajuste on/off (BD temporal)."""
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


def test_tamagotchi():
    assert not t.activo()
    assert t.ganar("clase") is None and not t.dar("onigiri")   # apagado: no hace nada
    t.set_activo(True)
    B = time.mktime((2026, 1, 5, 8, 0, 0, 0, 0, -1))  # las 8:00 de un día: +5 h sigue siendo el mismo día
    e = t.estado(B)
    assert e["hambre"] == 80 and e["objetos"]["onigiri"] == 2
    assert t.estado(B + 5 * 3600)["hambre"] == 60            # 5 h × 4 pts
    t.estado(B)
    assert t.dar("onigiri", B + 5 * 3600)
    assert t.estado(B + 5 * 3600)["hambre"] == 90 and t.estado(B + 5 * 3600)["objetos"]["onigiri"] == 1
    assert t.dar("onigiri", B + 5 * 3600) and not t.dar("onigiri", B + 5 * 3600)  # sin objetos
    assert t.estado(B + 500 * 3600)["cara"] == "triste"     # nunca baja de 0
    assert t.ganar("clase") in t.OBJETOS
    antes = sum(t.estado(B + 500 * 3600)["objetos"].values())
    assert sum(t.estado(B + 501 * 3600)["objetos"].values()) == antes   # mismo día: sin regalo
    assert sum(t.estado(B + 530 * 3600)["objetos"].values()) == antes + 1  # día nuevo: 1 regalo
    # la sed baja más deprisa que el hambre y el té la sube
    ss.settings_set("tamagotchi_estado", "")
    assert t.estado(B)["sed"] == 80
    assert t.estado(B + 4 * 3600)["sed"] == 60                 # 4 h × 5 pts
    assert t.dar("ocha", B + 4 * 3600) and t.estado(B + 4 * 3600)["sed"] == 100
    # los juguetes no se gastan, suben el ánimo y cansan (bajan hambre y sed); la comida sí se gasta
    ss.settings_set("tamagotchi_estado", "")
    t.estado(B)
    assert t.dar("kendama", B) and t.dar("kendama", B) and "kendama" not in t.estado(B)["objetos"]
    e = t.estado(B)
    assert e["animo"] == 100 and e["hambre"] == 70 and e["sed"] == 70   # 80 +20 +20 (tope 100) / 80 -5 -5
    assert t.dar("ebigohan", B) and not t.dar("ebigohan", B)         # solo había 1
    assert t.estado(B)["hambre"] == 100
    assert all(o["cat"] in ("comida", "bebida", "juego") for o in t.OBJETOS.values())
    por_cat = [sum(o["cat"] == c for o in t.OBJETOS.values()) for c in ("comida", "bebida", "juego")]
    assert por_cat == [6, 5, 4], por_cat   # 5 comidas + el arroz con bogavante, 5 bebidas, 4 juegos
    # hablarle sube el ánimo (nunca pasa de 100)
    ss.settings_set("tamagotchi_estado", "")
    t.estado(B)
    t.animar(3, B)
    assert t.estado(B)["animo"] == 83
    t.animar(50, B)
    assert t.estado(B)["animo"] == 100
    t.set_activo(False)
    t.animar(3, B)  # apagado: no hace nada
    t.set_activo(True)
    assert t.estado(B)["animo"] == 100


if __name__ == "__main__":
    test_tamagotchi()
    print("ok")
