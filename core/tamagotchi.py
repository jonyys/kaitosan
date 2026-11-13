"""Modo tamagotchi: Kaito tiene hambre, ánimo y sed que bajan con las horas.

Comida y bebida (todo japonés) se ganan terminando una clase (y 1 de regalo cada día) o se compran en la
tienda con yenes; los yenes se ganan con las clases y con la práctica de japonés. Los juguetes no se gastan.
El estado se calcula al leerlo (`ahora - ultima`), sin hilos, y se guarda como JSON en `app_settings`.
Con el ajuste apagado nada de esto hace nada.
"""
import json
import random
import time

from core.settings_store import settings_get, settings_set

# Lo que baja cada hora (puntos de 0 a 100): hambre llega a 0 en 3 días, sed en 2 y ánimo en 5.
# Nunca se muere, solo se pone mustio.
BAJADA_H = {"hambre": 100 / 72, "animo": 100 / 120, "sed": 100 / 48}
ANIMO_POR_CHARLA = 3  # cada vez que se le habla
PROB_BOGAVANTE_CLASE = 0.03  # el plato raro: casi solo se compra

# Lo que sube (o baja: jugar cansa) cada objeto y lo que cuesta en la tienda (yenes).
# cat: comida | bebida | juego. Los juegos no se gastan ni se compran. Nombres en pantalla en kana (nunca kanji).
OBJETOS = {
    # comida
    "onigiri": {"cat": "comida", "es": "Onigiri", "jp": "おにぎり", "precio": 30, "sube": {"hambre": 30}},
    "dango": {"cat": "comida", "es": "Dango", "jp": "だんご", "precio": 40, "sube": {"animo": 20, "hambre": 10}},
    "tamagoyaki": {"cat": "comida", "es": "Tamagoyaki", "jp": "たまごやき", "precio": 50, "sube": {"hambre": 25, "animo": 5}},
    "takoyaki": {"cat": "comida", "es": "Takoyaki", "jp": "たこやき", "precio": 60, "sube": {"hambre": 30}},
    "ramen": {"cat": "comida", "es": "Ramen", "jp": "ラーメン", "precio": 90, "sube": {"hambre": 45}},
    "ebigohan": {"cat": "comida", "es": "Arroz con bogavante", "jp": "いせえびごはん", "precio": 800,
                 "sube": {"hambre": 100, "animo": 30, "sed": 20}},
    # bebida
    "ocha": {"cat": "bebida", "es": "Té verde", "jp": "おちゃ", "precio": 20, "sube": {"sed": 40}},
    "mugicha": {"cat": "bebida", "es": "Té de cebada", "jp": "むぎちゃ", "precio": 20, "sube": {"sed": 40}},
    "mizu": {"cat": "bebida", "es": "Agua", "jp": "みず", "precio": 10, "sube": {"sed": 35}},
    "ramune": {"cat": "bebida", "es": "Ramune", "jp": "ラムネ", "precio": 40, "sube": {"sed": 30, "animo": 10}},
    "matcha": {"cat": "bebida", "es": "Matcha", "jp": "まっちゃ", "precio": 60, "sube": {"sed": 30, "animo": 8}},
    # juegos
    "temari": {"cat": "juego", "es": "Temari", "jp": "てまり", "sube": {"animo": 15, "hambre": -4, "sed": -4}},
    "koma": {"cat": "juego", "es": "Peonza", "jp": "こま", "sube": {"animo": 15, "hambre": -4, "sed": -4}},
    "kendama": {"cat": "juego", "es": "Kendama", "jp": "けんだま", "sube": {"animo": 20, "hambre": -5, "sed": -5}},
    "origami": {"cat": "juego", "es": "Grulla de papel", "jp": "おりづる", "sube": {"animo": 10}},
}
GASTABLES = [k for k, o in OBJETOS.items() if o["cat"] != "juego"]
COMUNES = [k for k in GASTABLES if k != "ebigohan"]  # lo que sale al azar (regalo diario, clases)
INICIAL = {"hambre": 80, "animo": 80, "sed": 80, "yenes": 0,
           "objetos": {**{k: 1 for k in COMUNES}, "onigiri": 2, "ocha": 2}}


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
    e.setdefault("yenes", 0)
    hoy = time.strftime("%Y-%m-%d", time.localtime(ahora))
    if e.get("dia") is None:
        e["dia"] = hoy
    elif e["dia"] != hoy:  # regalo del día: nunca se queda sin nada que dar
        e["dia"] = hoy
        obj = random.choice(COMUNES)
        e["objetos"][obj] = e["objetos"].get(obj, 0) + 1
        _guardar(e)
    return e


def _guardar(e: dict) -> None:
    settings_set("tamagotchi_estado", json.dumps(e))


def estado(ahora: float = None) -> dict:
    """Stats al día, yenes, lo que queda de cada cosa gastable y `catalogo` (lista ordenada con id, nombre,
    kana, categoría, precio y lo que sube) para dibujar el cajón."""
    e = _cargar(ahora or time.time())
    return {
        **{k: round(e[k]) for k in BAJADA_H},
        "yenes": int(e["yenes"]),
        "objetos": {k: e["objetos"].get(k, 0) for k in GASTABLES},
        "catalogo": [{"id": k, "es": o["es"], "jp": o["jp"], "cat": o["cat"], "precio": o.get("precio", 0),
                      "sube": o["sube"]}
                     for k, o in OBJETOS.items()],
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
    """Una comida o bebida por terminar una clase: al azar entre las normales y, rara vez, el arroz con
    bogavante. Devuelve su clave (None si apagado)."""
    if not activo() or motivo != "clase":
        return None
    e = _cargar(ahora or time.time())
    obj = "ebigohan" if random.random() < PROB_BOGAVANTE_CLASE else random.choice(COMUNES)
    e["objetos"][obj] = e["objetos"].get(obj, 0) + 1
    _guardar(e)
    return obj


# ── Yenes ────────────────────────────────────────────────────────────────────
def ganar_yenes(n: int, ahora: float = None) -> int:
    """Suma yenes (solo con el modo activo). Devuelve lo que se ha sumado."""
    n = int(n)
    if not activo() or n <= 0:
        return 0
    e = _cargar(ahora or time.time())
    e["yenes"] += n
    _guardar(e)
    return n


# Práctica de japonés (vocabulario, gramática, kanji): yenes según la nota que te das, de 0 a 5
YENES_PRACTICA = {5: 5, 4: 4, 3: 3, 2: 1}


def cobrar_practica(calidad, ahora: float = None) -> int:
    try:
        return ganar_yenes(YENES_PRACTICA.get(int(calidad), 0), ahora)
    except Exception as ex:  # noqa: BLE001 — la práctica nunca puede fallar por esto
        print(f"⚠️ tamagotchi: no se pudo cobrar la práctica: {ex}")
        return 0


YENES_ACIERTO = 5  # cada acierto en clase: monedas al momento, además del pago al acabar


def cobrar_acierto(ahora: float = None) -> int:
    try:
        return ganar_yenes(YENES_ACIERTO, ahora)
    except Exception as ex:  # noqa: BLE001 — la clase nunca puede fallar por esto
        print(f"⚠️ tamagotchi: no se pudo cobrar el acierto: {ex}")
        return 0


def pago_clase(logros: int, nuevos: int, palabras: int) -> int:
    """Lo que vale una clase: 20 por acabarla, 60 por cada can-do conseguido, 30 más si era nuevo y 8 por cada
    palabra vista (hasta 5)."""
    return 20 + 60 * logros + 30 * nuevos + 8 * min(palabras, 5)


def cobrar_clase(logros: int, nuevos: int, palabras: int, ahora: float = None) -> int:
    try:
        return ganar_yenes(pago_clase(logros, nuevos, palabras), ahora)
    except Exception as ex:  # noqa: BLE001
        print(f"⚠️ tamagotchi: no se pudo cobrar la clase: {ex}")
        return 0


def comprar(objeto: str, ahora: float = None) -> bool:
    """Compra 1 objeto gastable con yenes. False si no existe, no se vende o no llega el dinero."""
    if not activo() or objeto not in GASTABLES:
        return False
    e = _cargar(ahora or time.time())
    precio = OBJETOS[objeto]["precio"]
    if e["yenes"] < precio:
        return False
    e["yenes"] -= precio
    e["objetos"][objeto] = e["objetos"].get(objeto, 0) + 1
    _guardar(e)
    return True


# ── Trampas (Ajustes > Mascota): para probar el modo o echar una mano ─────────────────────────────
def trampa(accion: str, ahora: float = None) -> bool:
    """llenar: todo a 100 · vaciar: todo a 5 (para ver sus caras de necesidad) · yenes: +500 ·
    objetos: +3 de cada comida y bebida (bogavante incluido). False si está apagado o no existe."""
    if not activo() or accion not in ("llenar", "vaciar", "yenes", "objetos"):
        return False
    e = _cargar(ahora or time.time())
    if accion in ("llenar", "vaciar"):
        for k in BAJADA_H:
            e[k] = 100.0 if accion == "llenar" else 5.0
    elif accion == "yenes":
        e["yenes"] += 500
    else:
        for k in GASTABLES:
            e["objetos"][k] = e["objetos"].get(k, 0) + 3
    _guardar(e)
    return True
