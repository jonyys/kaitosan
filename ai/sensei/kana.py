"""Pasa texto japonés a solo kana para mostrarlo en pantalla (nunca kanji).

Los kanji se convierten a hiragana con pykakasi; la katakana y la hiragana que
ya hubiera se dejan tal cual. Sirve para enseñar en la cara del robot lo que el
sensei pide decir sin obligar a Laura a leer kanji.
"""

import re

import pykakasi

_kks = pykakasi.kakasi()

# Kanji (incl. extensión A). La katakana/​hiragana no entra aquí a propósito.
_KANJI = re.compile(r"[㐀-䶿一-鿿]")
_BLOQUE = re.compile(r"【([^【】]+)】")
_JP = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")


def a_kana(texto: str) -> str:
    """Devuelve `texto` con los kanji pasados a hiragana; el resto intacto."""
    if not texto:
        return texto
    partes = []
    for seg in _kks.convert(texto):
        orig = seg["orig"]
        # ponytail: si un segmento mezcla kanji + katakana, la katakana también
        # cae a hiragana (pykakasi da 'hira' del segmento entero). Es raro en
        # frases 【…】 cortas; separar por carácter si algún día molesta.
        partes.append(seg["hira"] if _KANJI.search(orig) else orig)
    return "".join(partes)


def bloques_japones(texto: str) -> list[str]:
    """Trozos 【…】 con japonés dentro, ya convertidos a solo kana."""
    out = []
    for b in _BLOQUE.findall(texto or ""):
        b = b.strip()
        if _JP.search(b):
            out.append(a_kana(b))
    return out


if __name__ == "__main__":
    assert a_kana("東京") == "とうきょう", a_kana("東京")
    assert a_kana("わたし") == "わたし"
    assert a_kana("コーヒーをのむ") == "コーヒーをのむ", a_kana("コーヒーをのむ")
    assert a_kana("水をのむ") == "みずをのむ", a_kana("水をのむ")
    assert a_kana("お元気ですか") == "おげんきですか", a_kana("お元気ですか")
    assert bloques_japones("Repite: 【水をのむ】 ¿vale?") == ["みずをのむ"]
    assert bloques_japones("dos 【食べる】 y 【コーヒー】 aquí") == ["たべる", "コーヒー"]
    assert bloques_japones("sin japonés 【hola】") == []
    print("ok")
