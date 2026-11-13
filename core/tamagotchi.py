"""Modo tamagotchi: Kaito tiene hambre, ánimo y sed que bajan con las horas.

Comida y bebida (todo japonés) se ganan terminando una clase (y 1 de regalo cada día) y se arrastran hasta
su cara en la pantalla; los juguetes no se gastan. El estado se calcula al leerlo (`ahora - ultima`), sin
hilos, y se guarda como JSON en `app_settings`. Con el ajuste apagado nada de esto hace nada.
"""
import json
import random
import time

from core.settings_store import settings_get, settings_set

# Lo que baja cada hora (puntos de 0 a 100): nunca se muere, solo se pone mustio.
BAJADA_H = {"hambre": 4.0, "animo": 3.0, "sed": 5.0}
ANIMO_POR_CHARLA = 3  # cada vez que se le habla

# Lo que sube (o baja: jugar cansa) cada objeto. cat: comida | bebida | juego. Los juegos no se gastan.
# Los nombres en pantalla van en kana (nunca kanji).
OBJETOS = {
    # comida
    "onigiri": {"cat": "comida", "es": "Onigiri", "jp": "おにぎり", "sube": {"hambre": 30}},
    "dango": {"cat": "comida", "es": "Dango", "jp": "だんご", "sube": {"animo": 20, "hambre": 10}},
    "tamagoyaki": {"cat": "comida", "es": "Tamagoyaki", "jp": "たまごやき", "sube": {"hambre": 25, "animo": 5}},
    "takoyaki": {"cat": "comida", "es": "Takoyaki", "jp": "たこやき", "sube": {"hambre": 30}},
    "ramen": {"cat": "comida", "es": "Ramen", "jp": "ラーメン", "sube": {"hambre": 45}},
    "ebigohan": {"cat": "comida", "es": "Arroz con bogavante", "jp": "いせえびごはん", "sube": {"hambre": 60, "animo": 10}},
    # bebida
    "ocha": {"cat": "bebida", "es": "Té verde", "jp": "おちゃ", "sube": {"sed": 40}},
    "mugicha": {"cat": "bebida", "es": "Té de cebada", "jp": "むぎちゃ", "sube": {"sed": 40}},
    "mizu": {"cat": "bebida", "es": "Agua", "jp": "みず", "sube": {"sed": 35}},
    "ramune": {"cat": "bebida", "es": "Ramune", "jp": "ラムネ", "sube": {"sed": 30, "animo": 10}},
    "matcha": {"cat": "bebida", "es": "Matcha", "jp": "まっちゃ", "sube": {"sed": 30, "animo": 8}},
    # juegos
    "temari": {"cat": "juego", "es": "Temari", "jp": "てまり", "sube": {"animo": 15, "hambre": -4, "sed": -4}},
    "koma": {"cat": "juego", "es": "Peonza", "jp": "こま", "sube": {"animo": 15, "hambre": -4, "sed": -4}},
    "kendama": {"cat": "juego", "es": "Kendama", "jp": "けんだま", "sube": {"animo": 20, "hambre": -5, "sed": -5}},
    "origami": {"cat": "juego", "es": "Grulla de papel", "jp": "おりづる", "sube": {"animo": 10}},
}
GASTABLES = [k for k, o in OBJETOS.items() if o["cat"] != "juego"]
INICIAL = {"hambre": 80, "animo": 80, "sed": 80,
           "objetos": {**{k: 1 for k in GASTABLES}, "onigiri": 2, "ocha": 2}}


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
        obj = random.choice(GASTABLES)
        e["objetos"][obj] = e["objetos"].get(obj, 0) + 1
        _guardar(e)
    return e


def _guardar(e: dict) -> None:
    settings_set("tamagotchi_estado", json.dumps(e))


def estado(ahora: float = None) -> dict:
    """Stats al día + lo que queda de cada cosa gastable + `cara` (feliz / normal / triste)
    + `catalogo` (lista ordenada: id, nombre, kana y categoría) para dibujar el cajón."""
    e = _cargar(ahora or time.time())
    peor = min(e["hambre"], e["animo"], e["sed"])
    return {
        **{k: round(e[k]) for k in BAJADA_H},
        "objetos": {k: e["objetos"].get(k, 0) for k in GASTABLES},
        "cara": "triste" if peor < 25 else "feliz" if peor > 60 else "normal",
        "catalogo": [{"id": k, "es": o["es"], "jp": o["jp"], "cat": o["cat"]} for k, o in OBJETOS.items()],
    }


def dar(objeto: str, ahora: float = None):
    """Gasta un objeto (los juegos no) y sube sus stats. False si no hay o está apagado."""
    ahora = ahora or time.time()
    if not activo() or objeto not in OBJETOS:
        return False
    e = _cargar(ahora)
    if objeto in GASTABLES:
        if e["objetos"].get(objeto, 0) < 1:
            return False
        e["objetos"][objeto] -= 1
    for k, n in OBJETOS[objeto]["sube"].items():
        e[k] = _acotar(e[k] + n)
    _guardar(e)
    return True


def ganar(motivo: str = "clase", ahora: float = None):
    """Una comida o bebida al azar por terminar una clase. Devuelve su clave (None si apagado)."""
    if not activo() or motivo != "clase":
        return None
    e = _cargar(ahora or time.time())
    obj = random.choice(GASTABLES)
    e["objetos"][obj] = e["objetos"].get(obj, 0) + 1
    _guardar(e)
    return obj
