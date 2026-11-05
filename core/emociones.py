"""Emociones de la cara a partir de lo que se dice.

- `extraer_emocion`: el LLM empieza su respuesta con una etiqueta como
  `[feliz]`. Se saca la emoción y se devuelve el texto sin etiqueta, que es lo
  que se lee en voz alta. Es tolerante a propósito: si el modelo no la pone, la
  escribe mal o la mete en medio, la respuesta sale igual y la cara se queda
  neutra. Nunca puede romper lo que se dice.
- `es_solo_gracias`: un "gracias" suelto no se contesta con voz, solo con cara.
"""
import re
import unicodedata

# Las que entiende la cara (_scripts.html, EMOCIONES). "neutral" = no hacer nada.
EMOCIONES = ("feliz", "carino", "bromista", "sorpresa", "triste", "pensativo", "neutral")

# Lo que los modelos escriben a veces en lugar de la etiqueta pedida
SINONIMOS = {
    "alegre": "feliz", "contento": "feliz", "contenta": "feliz", "alegria": "feliz",
    "entusiasmado": "feliz", "emocionado": "feliz", "happy": "feliz",
    "carinoso": "carino", "carinosa": "carino", "tierno": "carino", "amor": "carino",
    "afecto": "carino", "dulce": "carino",
    "broma": "bromista", "gracioso": "bromista", "divertido": "bromista",
    "jugueton": "bromista", "humor": "bromista", "ironico": "bromista",
    "sorprendido": "sorpresa", "sorprendida": "sorpresa", "asombro": "sorpresa",
    "asombrado": "sorpresa",
    "pena": "triste", "tristeza": "triste", "preocupado": "triste",
    "preocupada": "triste", "apenado": "triste", "lo siento": "triste", "sad": "triste",
    "pensando": "pensativo", "pensativa": "pensativo", "curioso": "pensativo",
    "curiosa": "pensativo", "duda": "pensativo", "reflexivo": "pensativo",
    "normal": "neutral", "neutro": "neutral", "tranquilo": "neutral", "serio": "neutral",
}

# [feliz], **[feliz]**, [Emoción: feliz], [ cariño ] ...
_ETIQUETA = re.compile(r"[*_]*\[\s*([^\[\]\n]{1,30}?)\s*\][*_]*")
# (feliz) solo si va al principio: entre paréntesis en medio puede ser texto normal
_PARENTESIS_INICIAL = re.compile(r"^\s*[*_]*\(\s*([^()\n]{1,20}?)\s*\)[*_]*\s*")
# Cualquier [palabra] suelta al principio sobra aunque no sea una emoción: no se lee
_CORCHETE_INICIAL = re.compile(r"^\s*\[[^\[\]\n]{1,30}\]\s*")


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", (texto or "").strip().lower())
        if unicodedata.category(c) != "Mn"
    )
    return sin_tildes


def _a_emocion(crudo: str):
    e = _normalizar(crudo)
    if ":" in e:  # "emocion: feliz"
        e = e.split(":")[-1].strip()
    e = e.strip(" .!*_-")
    if e in EMOCIONES:
        return e
    return SINONIMOS.get(e)


def extraer_emocion(texto: str):
    """Devuelve (emocion | None, texto_sin_etiquetas).

    None si no hay etiqueta reconocible o es "neutral".
    """
    if not texto:
        return None, texto
    encontrada = None

    def quitar(m):
        nonlocal encontrada
        e = _a_emocion(m.group(1))
        if e is None:
            return m.group(0)  # [resultado] u otro texto entre corchetes: se respeta
        if encontrada is None:
            encontrada = e
        return " "

    limpio = _ETIQUETA.sub(quitar, texto)

    m = _PARENTESIS_INICIAL.match(limpio)
    if m and _a_emocion(m.group(1)):
        if encontrada is None:
            encontrada = _a_emocion(m.group(1))
        limpio = limpio[m.end():]

    limpio = _CORCHETE_INICIAL.sub("", limpio)
    limpio = re.sub(r"[ \t]{2,}", " ", limpio)
    limpio = re.sub(r" +([,.;:!?])", r"\1", limpio)
    limpio = "\n".join(l.strip() for l in limpio.strip().split("\n"))

    if encontrada == "neutral":
        encontrada = None
    return encontrada, limpio


# ── "Gracias" suelto ──────────────────────────────────────────────────────────
_PALABRAS_GRACIAS = {"gracias", "arigato", "arigatou", "arigatoo", "thanks", "thank"}
# Lo que puede acompañar a un gracias sin que haga falta contestar
_RELLENO_GRACIAS = {
    "muchas", "muchisimas", "mil", "un", "millon", "pues", "vale", "ok", "okay",
    "genial", "perfecto", "bueno", "de", "verdad", "por", "todo", "eh", "tio",
    "kaito", "kaitosan", "san", "guapo", "majo", "bonito", "carino", "crack",
    "gozaimasu", "gozaimas", "domo", "doumo", "you", "so", "much", "very", "a", "lot",
}


def es_solo_gracias(texto: str) -> bool:
    """True si lo dicho es solo un agradecimiento ("gracias", "muchas gracias
    Kaito", "vale, gracias", "arigatou")."""
    t = re.sub(r"[^\w\s]", " ", _normalizar(texto))
    palabras = t.split()
    if not palabras or len(palabras) > 6:
        return False
    if not any(p in _PALABRAS_GRACIAS for p in palabras):
        return False
    return all(p in _PALABRAS_GRACIAS or p in _RELLENO_GRACIAS for p in palabras)
