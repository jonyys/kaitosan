"""Modo tamagotchi: bajada con el tiempo, objetos y ajuste on/off (BD temporal)."""
import os
import sys
import tempfile

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
    e = t.estado(1000)
    assert e["hambre"] == 80 and e["objetos"]["onigiri"] == 2
    assert t.estado(1000 + 5 * 3600)["hambre"] == 60            # 5 h × 4 pts
    t.estado(1000)
    assert t.dar("onigiri", 1000 + 5 * 3600)
    assert t.estado(1000 + 5 * 3600)["hambre"] == 90 and t.estado(1000 + 5 * 3600)["objetos"]["onigiri"] == 1
    assert t.dar("onigiri", 1000 + 5 * 3600) and not t.dar("onigiri", 1000 + 5 * 3600)  # sin objetos
    assert t.estado(1000 + 500 * 3600)["cara"] == "triste"     # nunca baja de 0
    assert t.ganar("clase") in t.OBJETOS


if __name__ == "__main__":
    test_tamagotchi()
    print("ok")
