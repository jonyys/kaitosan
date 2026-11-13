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
    # de noche duerme: la energía sube (8:00 → 23:00 baja 2/h = 50; 23:00 → 07:00 sube 5/h = 90)
    ss.settings_set("tamagotchi_estado", "")
    assert t.estado(B)["energia"] == 80
    assert t.estado(B + 15 * 3600)["energia"] == 50
    assert t.estado(B + 23 * 3600)["energia"] == 90
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
