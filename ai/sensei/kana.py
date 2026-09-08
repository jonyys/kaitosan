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

# Tramo corrido de japonés: puntuación CJK (、。〜…「」), kana, kanji y katakana
# de media anchura. Los 【】 se quitan antes, así que no estorban aquí.
_JP_RUN = re.compile(
    r"[　-〿぀-ヿㇰ-ㇿ一-鿿｡-ﾟ]+"
)


def normalizar_bloques_jp(texto: str) -> str:
    """Reescribe el marcado 【】: quita TODOS los corchetes y vuelve a envolver
    cada tramo corrido de japonés en un único 【】.

    El modelo a veces genera 【】 anidados (【いいね、【こんにちは】は…】) o japonés
    suelto fuera de 【】; ambos rompen la segmentación de voz (trozos "sueltos"
    en japonés, corchetes que van a la voz española, a veces un fallo de TTS).
    Tras esto: cero anidamiento, cero japonés fuera de 【】. El contenido del
    bloque se conserva tal cual (solo se recortan espacios en los bordes)."""
    if not texto:
        return texto
    sin = texto.replace("【", "").replace("】", "")

    def _envolver(m):
        s = m.group(0).strip("　 \t")
        return f"【{s}】" if s else m.group(0)

    return _JP_RUN.sub(_envolver, sin)


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


def romaji(texto: str) -> str:
    """Transcripción Hepburn de `texto` (kana o kanji), para mostrar la lectura."""
    if not texto:
        return texto
    return "".join(seg["hepburn"] for seg in _kks.convert(texto))


def bloques_japones(texto: str) -> list[str]:
    """Trozos 【…】 con japonés dentro, en solo kana y SIN repetidos.

    El profesor a veces repite la misma palabra varias veces en un turno
    ("Repite: 【おはようございます】 … 【おはようございます】"); en la card se
    muestra una sola vez, en el orden en que apareció. Antes se normaliza el
    marcado (【】 anidados / japonés suelto)."""
    out = []
    for b in _BLOQUE.findall(normalizar_bloques_jp(texto or "")):
        b = b.strip()
        if _JP.search(b):
            kana = a_kana(b)
            if kana not in out:
                out.append(kana)
    return out


def frases_para_card(respuesta: str, objetivo: str | None = None) -> list[str]:
    """Lo que se muestra en la card del sensei, siempre en solo kana.

    Si el turno fijó una frase objetivo (línea @@OBJETIVO@@ o heurística sobre
    【】), se muestra ESA entera: es lo que Laura tiene que decir y contra lo que
    se puntúa. Si no hay objetivo, los trozos 【…】 sueltos del turno."""
    return [a_kana(objetivo)] if objetivo else bloques_japones(respuesta)


if __name__ == "__main__":
    assert a_kana("東京") == "とうきょう", a_kana("東京")
    assert a_kana("わたし") == "わたし"
    assert a_kana("コーヒーをのむ") == "コーヒーをのむ", a_kana("コーヒーをのむ")
    assert a_kana("水をのむ") == "みずをのむ", a_kana("水をのむ")
    assert a_kana("お元気ですか") == "おげんきですか", a_kana("お元気ですか")
    assert bloques_japones("Repite: 【水をのむ】 ¿vale?") == ["みずをのむ"]
    assert bloques_japones("dos 【食べる】 y 【コーヒー】 aquí") == ["たべる", "コーヒー"]
    assert bloques_japones("Repite: 【おはよう】 … 【おはよう】") == ["おはよう"]
    assert frases_para_card("di 【ねこ】", "ちょっと、もう一度お願いします") == ["ちょっと、もういちどおねがいします"]
    assert frases_para_card("di 【ねこ】", None) == ["ねこ"]
    assert bloques_japones("sin japonés 【hola】") == []
    # 【】 anidados → un bloque limpio y continuo, sin "suelto" (contenido tal cual)
    assert bloques_japones("【いいね、【こんにちは】は午後です。】") == ["いいね、こんにちははごごです。"], \
        bloques_japones("【いいね、【こんにちは】は午後です。】")
    # japonés fuera de 【】 → se envuelve igualmente (nada queda "suelto")
    assert bloques_japones("【おつかれさま】、今日も頑張ったね。") == ["おつかれさま、きょうもがんばったね。"], \
        bloques_japones("【おつかれさま】、今日も頑張ったね。")
    assert normalizar_bloques_jp("hola こんにちは adios") == "hola 【こんにちは】 adios"
    assert normalizar_bloques_jp("【〜ます】") == "【〜ます】", normalizar_bloques_jp("【〜ます】")
    assert normalizar_bloques_jp("【みず。】") == "【みず。】", normalizar_bloques_jp("【みず。】")
    assert normalizar_bloques_jp("【a【b】c】 y 日本語 suelto") == "abc y 【日本語】 suelto", \
        normalizar_bloques_jp("【a【b】c】 y 日本語 suelto")
    assert romaji("がくせい") == "gakusei", romaji("がくせい")
    assert romaji("すみません") == "sumimasen", romaji("すみません")
    print("ok")
