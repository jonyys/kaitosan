"""Modo tamagotchi: Kaito tiene hambre, ánimo y sed que bajan con las horas.

Los objetos (comida) se ganan terminando una clase (y 1 de regalo cada día) y se
arrastran hasta su cara en la pantalla. El estado se calcula al leerlo (`ahora - ultima`), sin hilos, y se guarda
como JSON en `app_settings`. Con el ajuste apagado nada de esto hace nada.
"""
import json
import random
import time

from core.settings_store import settings_get, settings_set

# Lo que baja cada hora (puntos de 0 a 100): nunca se muere, solo se pone mustio.
BAJADA_H = {"hambre": 4.0, "animo": 3.0, "sed": 5.0}
ANIMO_POR_CHARLA = 3  # cada vez que se le habla
# Lo que sube cada objeto
OBJETOS = {
    "onigiri": {"es": "Onigiri", "jp": "おにぎり", "sube": {"hambre": 30}},
    "dango": {"es": "Dango", "jp": "だんご", "sube": {"animo": 20, "hambre": 10}},
    "ocha": {"es": "Té", "jp": "おちゃ", "sube": {"sed": 40}},
}
INICIAL = {"hambre": 80, "animo": 80, "sed": 80, "objetos": {"onigiri": 2, "dango": 1, "ocha": 1}}


def activo() -> bool:
    return (settings_get("tamagotchi") or "0") == "1"


def set_activo(on: bool) -> None:
    settings_set("tamagotchi", "1" if on else "0")


def _acotar(v) -> float:
    return max(0.0, min(100.0, v))


def animar(n: int = ANIMO_POR_CHARLA, ahora: float = None) -> None:
    """Hablarle le sube el ánimo. No hace nada con el modo apagado y nunca rompe una conversación."""
    try:
        if not activo():
            return
        e = _cargar(ahora or time.time())
        e["animo"] = _acotar(e["animo"] + n)
        _guardar(e)
    except Exception as ex:  # noqa: BLE001
        print(f"⚠️ tamagotchi: no se pudo subir el ánimo: {ex}")


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
    peor = min(e["hambre"], e["animo"], e["sed"])
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
