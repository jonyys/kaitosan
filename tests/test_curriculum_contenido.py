"""Fase 05 — contenido didáctico de `curriculum.py` (ensamblado por
`scripts/generar_contenido.py` desde `scripts/_fase05_contenido.json`).

- Los 90 puntos de gramática N5 tienen `ejemplo` y `uso` no vacíos.
- El `ejemplo` de cada punto de gramática usa el patrón (o su núcleo sin `〜`).
- `meaning` sin inglés en gramática y en el vocabulario que lleva `uso`.
- Las `uso` de vocabulario presentes son texto en español (no obligatorias: la
  mayoría del vocabulario queda sin `uso` por diseño).
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM

# Palabras función inglesas que delatarían una glosa EN->ES sin traducir.
INGLES_RE = re.compile(
    r"\b(the|and|of|is|are|was|were|with|for|you|your|that|this|these|those|they|"
    r"them|their|there|what|when|where|which|who|from|have|has|had|will|would|"
    r"should|could|about|into|than|then|because)\b",
    re.IGNORECASE,
)
ES_LETRA_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]")


def _sin_citas(texto):
    return re.sub("「[^」]*」", "", texto or "")


def _tiene_ingles(texto):
    return bool(INGLES_RE.search(_sin_citas(texto)))


def _gram_items():
    return [it for u in CURRICULUM for it in u["items"] if it["kind"] == "gramatica"]


def _vocab_items():
    return [
        it for u in CURRICULUM for it in u["items"]
        if it["kind"] == "vocabulario" and it.get("tipo") != "kanji"
    ]


def _nucleos(jp):
    """Substrings que deben aparecer (sin espacios) en un ejemplo que USA el
    patrón; se relaja la cola flexiva para admitirlo conjugado."""
    p = jp.replace("（", "(").replace("）", ")")
    p = re.sub(r"\([^)]*\)", "", p)
    p = p.replace("〜", "").replace("～", "").replace("疑問詞", "")
    partes = [x.strip() for x in re.split(r"[+＋]", p) if x.strip()]
    cands = set(partes)
    for x in partes:
        for cola in ("います", "ます", "です", "いる", "る", "た", "ない"):
            if x.endswith(cola) and len(x) > len(cola):
                cands.add(x[: -len(cola)])
        cands.update(re.findall(
            r"たり|ほど|あとで|まえに|ながら|ことが|ことができ|ましょう|そう|つもり|"
            r"なくては|ないほうが|たくない|たがって|なら|ので|やすい|にくい|わかり|"
            r"好き|嫌い|上手|下手|でしょう|かもしれ|んです", x))
    corta_ok = {"ば", "と", "か", "も", "や", "へ", "は", "が", "を", "に", "で", "の", "ね", "よ"}
    return {c for c in cands if len(c) >= 2 or c in corta_ok}


def test_gramatica_tiene_ejemplo_y_uso():
    faltan = [
        it["jp"] for it in _gram_items()
        if not (it.get("ejemplo") or "").strip() or not (it.get("uso") or "").strip()
    ]
    assert not faltan, faltan
    assert len(_gram_items()) == 90, len(_gram_items())


def test_gramatica_ejemplo_usa_el_patron():
    fallos = []
    for it in _gram_items():
        ej = (it.get("ejemplo") or "").replace(" ", "").replace("　", "")
        nu = _nucleos(it["jp"])
        if nu and not any(n in ej for n in nu):
            fallos.append((it["jp"], sorted(nu), it.get("ejemplo")))
    assert not fallos, fallos


def test_gramatica_meaning_sin_ingles():
    con_ingles = [it["jp"] for it in _gram_items() if _tiene_ingles(it.get("meaning", ""))]
    assert not con_ingles, con_ingles


def test_vocab_uso_presente_es_estructural():
    """Las `uso` de vocabulario no son obligatorias; pero si están, son texto en
    español y su `meaning` no lleva inglés sin traducir."""
    sin_es, meaning_en = [], []
    for it in _vocab_items():
        uso = (it.get("uso") or "").strip()
        if not uso:
            continue
        if not ES_LETRA_RE.search(_sin_citas(uso)):
            sin_es.append(it["jp"])
        if _tiene_ingles(it.get("meaning", "")):
            meaning_en.append(it["jp"])
    assert not sin_es, sin_es
    assert not meaning_en, meaning_en


def test_fase05_landeo_contenido():
    """Guardarraíl de regresión: la Fase 05 dejó contenido nuevo (los 52 puntos
    de gramática que entraron vacíos en la Fase 03 + ~230 notas de uso)."""
    con_uso = sum(1 for it in _vocab_items() if (it.get("uso") or "").strip())
    assert con_uso >= 400, con_uso
    gram_completos = sum(
        1 for it in _gram_items()
        if (it.get("ejemplo") or "").strip() and (it.get("literal") or "").strip()
        and (it.get("uso") or "").strip()
    )
    assert gram_completos == 90, gram_completos


if __name__ == "__main__":
    test_gramatica_tiene_ejemplo_y_uso()
    test_gramatica_ejemplo_usa_el_patron()
    test_gramatica_meaning_sin_ingles()
    test_vocab_uso_presente_es_estructural()
    test_fase05_landeo_contenido()
    print("OK")
