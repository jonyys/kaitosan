"""Modo tamagotchi: Kaito tiene hambre, ánimo y energía que bajan con las horas.

Los objetos (comida) se ganan terminando una clase (y 1 de regalo cada día) y se
arrastran hasta su cara en la pantalla. El estado se calcula al leerlo (`ahora - ultima`), sin hilos, y se guarda
como JSON en `app_settings`. Con el ajuste apagado nada de esto hace nada.
"""
import json
import random
import time

from core.settings_store import settings_get, settings_set

# Lo que baja cada hora (puntos de 0 a 100): nunca se muere, solo se pone mustio.
BAJADA_H = {"hambre": 4.0, "animo": 3.0, "energia": 2.0}
# Lo que sube cada objeto
OBJETOS = {
    "onigiri": {"es": "Onigiri", "jp": "おにぎり", "sube": {"hambre": 30}},
    "dango": {"es": "Dango", "jp": "だんご", "sube": {"animo": 20, "hambre": 10}},
    "ocha": {"es": "Té", "jp": "おちゃ", "sube": {"energia": 30}},
}
INICIAL = {"hambre": 80, "animo": 80, "energia": 80, "objetos": {"onigiri": 2, "dango": 1, "ocha": 1}}


def activo() -> bool:
    return (settings_get("tamagotchi") or "0") == "1"


def set_activo(on: bool) -> None:
    settings_set("tamagotchi", "1" if on else "0")


def _acotar(v) -> float:
    return max(0.0, min(100.0, v))


def _cargar(ahora: float) -> dict:
    try:
        e = json.loads(settings_get("tamagotchi_estado") or "")
        assert isinstance(e["objetos"], dict)
    except Exception:  # noqa: BLE001 — sin estado o roto: se empieza de cero
        e = {**INICIAL, "objetos": dict(INICIAL["objetos"]), "ultima": ahora}
        _guardar(e)  # el reloj arranca ya: si no, nunca pasaría el tiempo
    horas = max(0.0, (ahora - e.get("ultima", ahora)) / 3600)
    for k, por_hora in BAJADA_H.items():
        e[k] = _acotar(e.get(k, 80) - por_hora * horas)
    e["ultima"] = ahora
    hoy = time.strftime("%Y-%m-%d", time.localtime(ahora))
    if e.get("dia") is None:
        e["dia"] = hoy
    elif e["dia"] != hoy:  # regalo del día: nunca se queda sin nada que dar
        e["dia"] = hoy
        obj = random.choice(list(OBJETOS))
        e["objetos"][obj] = e["objetos"].get(obj, 0) + 1
        _guardar(e)
    return e


def _guardar(e: dict) -> None:
    settings_set("tamagotchi_estado", json.dumps(e))


def estado(ahora: float = None) -> dict:
    """Stats al día + objetos + `animo_cara` (feliz / normal / triste) para pintar la cara."""
    e = _cargar(ahora or time.time())
    peor = min(e["hambre"], e["animo"], e["energia"])
    return {
        **{k: round(e[k]) for k in BAJADA_H},
        "objetos": {k: n for k, n in e["objetos"].items() if k in OBJETOS},
        "cara": "triste" if peor < 25 else "feliz" if peor > 60 else "normal",
    }


def dar(objeto: str, ahora: float = None):
    """Gasta un objeto y sube sus stats. False si no hay o está apagado."""
    ahora = ahora or time.time()
    if not activo() or objeto not in OBJETOS:
        return False
    e = _cargar(ahora)
    if e["objetos"].get(objeto, 0) < 1:
        return False
    e["objetos"][objeto] -= 1
    for k, n in OBJETOS[objeto]["sube"].items():
        e[k] = _acotar(e[k] + n)
    _guardar(e)
    return True


def ganar(motivo: str = "clase", ahora: float = None):
    """Un objeto al azar por terminar una clase. Devuelve su clave (None si apagado)."""
    if not activo() or motivo != "clase":
        return None
    e = _cargar(ahora or time.time())
    obj = random.choice(list(OBJETOS))
    e["objetos"][obj] = e["objetos"].get(obj, 0) + 1
    _guardar(e)
    return obj
