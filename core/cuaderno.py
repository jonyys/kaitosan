"""Cuaderno de Laura: notas libres (apuntes del libro, frases, dudas) ligadas a
sus flashcards.

- Las notas viven en la tabla `cuaderno_notas` de la misma BD (mismo patrón que
  cards_propias: `jm._conectar()`).
- El enlace con las cards es por texto: `tarjetas_en(texto, jm)` busca en la nota
  cualquier card conocida (kanji, vocabulario, gramática) y `notas_con(jm, jp)`
  hace el camino inverso para la ficha del kanji.
"""
import re
from datetime import datetime

from ai.sensei.curriculum import CURRICULUM
from ai.sensei.kanji_n5 import KANJI_N5

_KANJI_KATA = re.compile("[一-鿿゠-ヿ]")   # kanji o katakana
_HIRAGANA = re.compile("[぀-ゟ]+")


def _tabla(c):
    c.execute("CREATE TABLE IF NOT EXISTS cuaderno_notas ("
              "id INTEGER PRIMARY KEY, titulo TEXT, texto TEXT, creada TEXT, editada TEXT)")


def _fila(r):
    nota = dict(zip(("id", "titulo", "texto", "creada", "editada"), r))
    primera = next((l.strip() for l in nota["texto"].splitlines() if l.strip()), "")
    nota["etiqueta"] = nota["titulo"] or (primera[:40] or "Sin título")
    return nota


def listar(jm):
    """Notas, la última editada primero."""
    with jm._conectar() as c:
        _tabla(c)
        filas = c.execute("SELECT id, titulo, COALESCE(texto, ''), creada, editada "
                          "FROM cuaderno_notas ORDER BY editada DESC, id DESC").fetchall()
    return [_fila(r) for r in filas]


def obtener(jm, nota_id):
    with jm._conectar() as c:
        _tabla(c)
        r = c.execute("SELECT id, titulo, COALESCE(texto, ''), creada, editada "
                      "FROM cuaderno_notas WHERE id = ?", (nota_id,)).fetchone()
    return _fila(r) if r else None


def guardar(jm, nota_id, titulo, texto):
    """Crea (nota_id falsy) o actualiza. Devuelve el id, o None si no hay nada
    que guardar (nota nueva y vacía) o la nota ya no existe."""
    titulo, texto = (titulo or "").strip(), (texto or "").strip()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with jm._conectar() as c:
        _tabla(c)
        if nota_id:
            n = c.execute("UPDATE cuaderno_notas SET titulo = ?, texto = ?, editada = ? WHERE id = ?",
                          (titulo, texto, ahora, nota_id)).rowcount
            return int(nota_id) if n else None
        if not (titulo or texto):
            return None
        return c.execute("INSERT INTO cuaderno_notas (titulo, texto, creada, editada) VALUES (?, ?, ?, ?)",
                         (titulo, texto, ahora, ahora)).lastrowid


def borrar(jm, nota_id):
    with jm._conectar() as c:
        _tabla(c)
        c.execute("DELETE FROM cuaderno_notas WHERE id = ?", (nota_id,))


def notas_con(jm, jp):
    """Notas cuyo texto contiene `jp` (para «En tu cuaderno» en la ficha)."""
    return [n for n in listar(jm) if jp and jp in n["texto"]]


def cartas_conocidas(jm):
    """[{kind, jp, reading, meaning}] de todo lo que Laura puede tener como card.
    CURRICULUM/KANJI_N5 ya llevan aplicadas las ediciones de cards_propias."""
    cartas = {}

    def add(kind, jp, reading, meaning):
        jp = (jp or "").strip()
        if jp and jp not in cartas:
            r = (reading or "").strip()
            cartas[jp] = {"kind": kind, "jp": jp, "reading": "" if r == jp else r,
                          "meaning": (meaning or "").replace(" (kanji)", "").strip()}

    for k in KANJI_N5:      # primero: los kanji ganan a su copia en CURRICULUM
        add("kanji", k["jp"], k.get("reading_card") or k.get("reading") or k.get("kun") or k.get("on"),
            k.get("meaning"))
    for u in CURRICULUM:
        for it in u.get("items", []):
            add("kanji" if it.get("tipo") == "kanji" else it.get("kind", "vocabulario"),
                it.get("jp"), it.get("reading"), it.get("meaning"))
    for jp, r in jm.vocab_rows().items():
        add("vocabulario", jp, r.get("reading"), r.get("meaning"))
    for jp, r in jm.gram_rows().items():
        add("gramatica", jp, "", r.get("description"))
    return list(cartas.values())


def _clave(carta):
    """Texto a buscar de una card, o None si dispararía falsos positivos: vale si
    lleva algún kanji/katakana, o si es hiragana puro de 3+ caracteres."""
    jp = carta["jp"].strip()
    if carta["kind"] == "gramatica":
        jp = jp.strip("〜～")
        if len(jp) < 2:
            return None
    if _KANJI_KATA.search(jp) or (len(jp) >= 3 and _HIRAGANA.fullmatch(jp)):
        return jp
    return None


def encontrar(texto, cartas):
    """Cards cuyo `jp` aparece en `texto`, por orden de aparición. Las más largas
    primero y sin solaparse (出口 no deja también 口); una card no sale dos veces."""
    usado = [False] * len(texto)
    hallazgos = {}
    claves = sorted(((_clave(c), c) for c in cartas), key=lambda kc: -len(kc[0] or ""))
    for clave, carta in claves:
        if not clave or carta["jp"] in hallazgos:
            continue
        i = texto.find(clave)
        while i >= 0:
            if not any(usado[i:i + len(clave)]):
                usado[i:i + len(clave)] = [True] * len(clave)
                hallazgos[carta["jp"]] = (i, carta)
                break
            i = texto.find(clave, i + 1)
    return [c for _, c in sorted(hallazgos.values(), key=lambda h: h[0])]


def tarjetas_en(jm, texto):
    return encontrar(texto, cartas_conocidas(jm))


if __name__ == "__main__":
    import os
    import tempfile
    from core.japanese_memory import JapaneseMemory

    def c(jp, kind="vocabulario"):
        return {"kind": kind, "jp": jp}
    cs = [c("出口"), c("学生"), c("は"), c("です"), c("～です", "gramatica"), c("口"),
          c("〜ます", "gramatica"), c("〜に行く", "gramatica"), c("わたし"), c("テレビ")]
    r = [x["jp"] for x in encontrar("今日は出口で待つ。わたしは学生です", cs)]
    assert r == ["出口", "わたし", "学生"], r          # sin は/です/～です; 口 no sale dentro de 出口
    assert [x["jp"] for x in encontrar("テレビを見る。出口の口", cs)] == ["テレビ", "出口", "口"]
    assert [x["jp"] for x in encontrar("駅に行く", cs)] == ["〜に行く"]    # la 〜 se ignora
    assert encontrar("行く", cs) == [] and encontrar("ます", [c("〜ます", "gramatica")]) == []

    jm = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    assert listar(jm) == [] and guardar(jm, None, "", "  ") is None
    a = guardar(jm, None, "Lección 1", "出口はどこですか")
    b = guardar(jm, None, "", "segunda nota")
    assert listar(jm)[0]["id"] == b and obtener(jm, b)["etiqueta"] == "segunda nota"
    assert guardar(jm, a, "Lección 1b", "出口と入口") == a
    assert obtener(jm, a)["titulo"] == "Lección 1b" and listar(jm)[0]["id"] == a
    assert [n["id"] for n in notas_con(jm, "入口")] == [a] and notas_con(jm, "駅") == []
    assert guardar(jm, 999, "x", "y") is None
    assert isinstance(tarjetas_en(jm, "出口"), list)
    borrar(jm, a)
    assert obtener(jm, a) is None and len(listar(jm)) == 1
    print("ok")
