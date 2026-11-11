"""Forma て determinista: qué formas て (bien o mal) hay en lo que dijo Laura.

Sin LLM: las reglas de conjugación son fijas, así que el código las comprueba y
el profesor solo tiene que decirlo bonito (ver ai/sensei/clase.py).
"""

import re

from ai.sensei.curriculum import CURRICULUM

# Acaban en -iru/-eru pero son godan (る → って). Lista de N5 y alrededores.
_GODAN_RU = {"帰る", "入る", "走る", "知る", "切る", "要る", "喋る", "減る", "握る",
             "焦る", "滑る", "散る", "蹴る", "限る", "参る", "しゃべる"}
_FILA_I_E = set("いきぎしじちぢにひびぴみりえけげせぜてでねへべぺめれ")
_A_I = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し", "つ": "ち", "ぬ": "に",
        "ぶ": "び", "む": "み", "る": "り"}
_TE_GODAN = {"う": "って", "つ": "って", "る": "って", "む": "んで", "ぶ": "んで",
             "ぬ": "んで", "く": "いて", "ぐ": "いで", "す": "して"}


def grupo(jp, reading):
    if reading in ("する", "くる") or jp in ("する", "来る", "くる"):
        return "irregular"
    if reading.endswith("る") and jp not in _GODAN_RU and reading[-2:-1] in _FILA_I_E:
        return "ichidan"
    return "godan"


def forma_te(s, g):
    """s = diccionario (kana o kanji+okurigana), g = grupo."""
    if s in ("する",):
        return "して"
    if s in ("くる", "来る"):
        return s[:-1] + "て" if s == "来る" else "きて"
    if s in ("行く", "いく"):
        return s[:-1] + "って"
    if g == "ichidan":
        return s[:-1] + "て"
    return s[:-1] + _TE_GODAN[s[-1]]


def _motivo(jp, reading, g):
    if jp == "行く":
        return "行く es la excepción de los godan en く: 行って, no 行いて ni 行きて"
    if g == "irregular":
        return f"{jp} es irregular"
    if g == "ichidan":
        return f"{jp} es ichidan: se quita る y se añade て"
    if jp in _GODAN_RU:
        return f"{jp} es godan aunque acabe en -eru/-iru, así que る pasa a って"
    return f"{jp} es godan en {reading[-1]}: {reading[-1]} pasa a {_TE_GODAN[reading[-1]]}"


def _verbos():
    out = []
    for u in CURRICULUM:
        for it in u.get("items", []):
            if it.get("tipo") != "verbo":
                continue
            jp, rd = it["jp"], (it.get("reading") or "").split(" ")[0]
            if jp.endswith(("う", "く", "ぐ", "す", "つ", "ぬ", "ぶ", "む", "る")) and rd:
                out.append((jp, rd))
    return out


def _a_ta(f):
    """Forma た = forma て con て→た, で→だ."""
    return f[:-1] + ("だ" if f.endswith("で") else "た")


def _masu(s, g):
    if s in ("する", "くる", "来る"):
        return {"する": "し", "くる": "き", "来る": "来"}[s] + "ました"
    return s[:-1] + ("" if g == "ichidan" else _A_I[s[-1]]) + "ました"


def _tablas(forma):
    bien, mal = {}, {}
    conv = (lambda f: f) if forma == "te" else _a_ta
    for jp, rd in _verbos():
        g = grupo(jp, rd)
        for s in {jp, rd}:
            correcta = conv(forma_te(s, g))
            # いって = 行く / 言う / 要る: para la corrección de ます manda 行く.
            # ponytail: el más frecuente gana; el contexto no se mira.
            if jp == "行く" or correcta not in bien:
                bien[correcta] = _masu(s, g)
            if g == "irregular":
                continue
            raiz = s[:-1] + ("" if g == "ichidan" else _A_I[s[-1]])
            # のみて, いきて (raíz de ます + て). Nada de raíz + で: choca con です
            # (「やすみです」, 「がくせいです」).
            erroneas = {raiz + "て"}
            if g == "godan" and s[-1] == "る":
                erroneas.add(s[:-1] + "て")            # かえて (lo trata como ichidan)
            if g == "ichidan":
                erroneas.add(s[:-1] + "って")          # たべって
            for e in map(conv, erroneas):
                if len(e) >= 3:  # de 2 caracteres salen dentro de cualquier frase
                    mal.setdefault(e, (correcta, _motivo(jp, rd, g)))
    # Nunca marcar como error algo que es correcto de otro verbo; ni formas
    # correctas de verbos fuera del temario (お腹が空いて, 飽きて).
    # ponytail: lista a mano; amplíala si aparecen falsos positivos en sesión.
    for f in list(bien) + [conv("すいて"), conv("あきて")]:
        mal.pop(f, None)
    return bien, mal


_TABLAS = {f: _tablas(f) for f in ("te", "ta")}
_LARGO = max(len(x) for b, m in _TABLAS.values() for x in list(b) + list(m))
_TE_MASU = re.compile(r"\s*ま(?:す|した)")


def analizar(texto, forma="te"):
    """{'correctas': [forma], 'errores': [(dicho, correcta, motivo)]} para la
    forma て ("te") o た ("ta"). Recorrido de izquierda a derecha quedándose con
    la coincidencia más larga, para que 「よみて」 no se lea como 「見て」 dentro."""
    bien, mal = _TABLAS[forma]
    correctas, errores = [], []
    i = 0
    while i < len(texto):
        for n in range(min(_LARGO, len(texto) - i), 1, -1):
            trozo = texto[i:i + n]
            if trozo in mal:
                errores.append((trozo, *mal[trozo]))
                break
            if trozo in bien:
                correctas.append(trozo)
                # 「いって ました」: forma て + ます/ました no existe; el tiempo
                # lo lleva el último verbo, en ます. (〜ています va con い.)
                if forma == "te" and _TE_MASU.match(texto, i + n):
                    errores.append((trozo + "ました", bien[trozo],
                                    "con forma て no se añade ます: el último verbo va en su forma ます normal"))
                break
        else:
            n = 1
        i += n
    return {"correctas": correctas, "errores": errores}


if __name__ == "__main__":
    a = analizar("けさ おきて、コーヒー を のんで、かいしゃ に いきて ました")
    assert a["correctas"] == ["おきて", "のんで"], a
    assert a["errores"][0][:2] == ("いきて", "いって"), a
    a = analizar("うち に かえて、メール を よみて、会議に出て")
    assert [e[1] for e in a["errores"]] == ["かえって", "よんで"], a
    assert "出て" in a["correctas"], a  # 出る es ichidan
    assert not analizar("うちにかえって、たべて、みて")["errores"]
    for t in ("あしたはやすみです", "わたしはがくせいです", "それはいいですね"):
        assert not analizar(t)["errores"], t
    a = analizar("かいしゃに いって ました")
    assert a["errores"] == [("いってました", "いきました", a["errores"][0][2])], a
    assert not analizar("いま たべています")["errores"]
    a = analizar("きのう のみた、いった、たべった", "ta")
    assert [e[1] for e in a["errores"]] == ["のんだ", "たべた"] and "いった" in a["correctas"], a
    print("ok")
