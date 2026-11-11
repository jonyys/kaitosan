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


# Palabras funcionales que delatan español en una transcripción. Sin acentos
# sueltos ni partículas que también son romaji japonés (no, de, ni, to, te, yo…):
# Whisper convierte el japonés de Laura en latín raro («Vatæði var gak sejar í
# masen») y eso NO es español.
_PALABRAS_ES = frozenset(
    "sí sé que qué y el la los las es pero vale eso esto como cómo porque por para "
    "con una luego lo del al más bien también entonces está estoy cuando "
    "dónde donde cuál hay ahora".split()
)
_SOLO_ES = frozenset({"no", "si", "vale", "ok", "vale vale"})


def tiene_espanol(texto: str) -> bool:
    """¿Hay español en lo transcrito? (frase entera en español o mezclada)."""
    t = (texto or "").lower()
    if "¿" in t or "¡" in t or "ñ" in t:
        return True
    palabras = re.findall(r"[a-záéíóúü]+", t)
    if " ".join(palabras) in _SOLO_ES:
        return True
    return any(p in _PALABRAS_ES for p in palabras)


_ROMAJI = dict(zip(*[iter((
    "a あ i い u う e え o お ka か ki き ku く ke け ko こ sa さ shi し su す se せ so そ ta た chi ち tsu つ te て to と "
    "na な ni に nu ぬ ne ね no の ha は hi ひ fu ふ he へ ho ほ ma ま mi み mu む me め mo も ya や yu ゆ yo よ "
    "ra ら ri り ru る re れ ro ろ wa わ wo を ga が gi ぎ gu ぐ ge げ go ご za ざ ji じ zu ず ze ぜ zo ぞ da だ de で do ど "
    "ba ば bi び bu ぶ be べ bo ぼ pa ぱ pi ぴ pu ぷ pe ぺ po ぽ kya きゃ kyu きゅ kyo きょ sha しゃ shu しゅ sho しょ "
    "cha ちゃ chu ちゅ cho ちょ nya にゃ nyu にゅ nyo にょ hya ひゃ hyu ひゅ hyo ひょ mya みゃ myu みゅ myo みょ "
    "rya りゃ ryu りゅ ryo りょ gya ぎゃ gyu ぎゅ gyo ぎょ ja じゃ ju じゅ jo じょ bya びゃ byu びゅ byo びょ "
    "pya ぴゃ pyu ぴゅ pyo ぴょ si し ti ち tu つ hu ふ zi じ"
).split())] * 2))
_KATA = re.compile(r"[ァ-ヶ]")


def _palabra_a_kana(p: str):
    """Una palabra en romaji → hiragana, o None si no es romaji japonés entero."""
    p, out, i = p.lower().replace("ō", "ou").replace("ū", "uu"), "", 0
    while i < len(p):
        if p[i] in "nm" and (i + 1 == len(p) or p[i + 1] not in "aiueoy") and (p[i] == "n" or p[i + 1] in "bpm"):
            out, i = out + "ん", i + 1
        elif i + 1 < len(p) and p[i] == p[i + 1] and p[i] in "kstpcdgbzj":  # kk → っk
            out, i = out + "っ", i + 1
        else:
            for n in (3, 2, 1):
                if p[i:i + n] in _ROMAJI:
                    out, i = out + _ROMAJI[p[i:i + n]], i + n
                    break
            else:
                return None
    return out


def normalizar_japones(texto: str) -> str:
    """Lo que Whisper escribe de un japonés con acento (romaji, katakana) →
    hiragana, para que las comprobaciones de conjugación lo vean. El romaji solo
    se convierte si el texto no tiene español (sus palabras también «suenan» a kana)."""
    t = _KATA.sub(lambda m: m.group() if m.group() == "ー" else chr(ord(m.group()) - 0x60), texto or "")
    if not tiene_espanol(t):
        t = re.sub(r"[A-Za-zō]+", lambda m: _palabra_a_kana(m.group()) or m.group(), t)
    return re.sub(r"(?<=[぀-ゟ])\s+(?=[぀-ゟ])", "", t)


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
        if _JP.search(b) and len(b) > 1:  # 【は】【か】 sueltos son ruido en la card
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
    for s in ("Sí.", "No sé", "no", "けさ おきて, y luego desayuné", "¿のんで?", "Vale."):
        assert tiene_espanol(s), s
    for s in ("けさ おきて、コーヒーを のんで", "Watashiwa, lordes.",
              "Vatæði var gak sejar í masen.", "Okite, kohi o nonde", ""):
        assert not tiene_espanol(s), s
    print("ok")
