"""Cuaderno de Laura: páginas escritas a mano (como las Notas de iOS), ligadas
a sus flashcards.

- `cuaderno_paginas`: una página de 1200x1600 lógicos; `trazos` es un JSON con la
  lista de trazos {c, w, e, p:[[x,y]…]} y `miniatura` un PNG pequeño (data URL)
  que genera el navegador para la lista.
- `cuaderno_vinculos`: qué cards (kind, jp) están ligadas a cada página, a mano
  (sin OCR). Mismo patrón que cards_propias: `jm._conectar()`.
- La vieja tabla `cuaderno_notas` (cuaderno de texto) se deja intacta en la BD.
"""
import json
import unicodedata
from datetime import datetime

from ai.sensei.curriculum import CURRICULUM
from ai.sensei.kanji_n5 import KANJI_N5

KINDS = ("kanji", "vocabulario", "gramatica")
MAX_TRAZOS_BYTES = 8_000_000   # tope de seguridad por página
MAX_MINIATURA = 200_000


def _tabla(c):
    c.execute("CREATE TABLE IF NOT EXISTS cuaderno_paginas ("
              "id INTEGER PRIMARY KEY, titulo TEXT, fondo TEXT, trazos TEXT, "
              "miniatura TEXT, creada TEXT, editada TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS cuaderno_vinculos ("
              "pagina_id INTEGER, kind TEXT, jp TEXT, PRIMARY KEY (pagina_id, kind, jp))")


def _ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def _fondo(f):
    return f if f in ("liso", "rayas", "cuadricula", "kanji", "puntos") else "liso"


def listar(jm):
    """Páginas (sin trazos), la última editada primero."""
    with jm._conectar() as c:
        _tabla(c)
        filas = c.execute("SELECT id, titulo, fondo, COALESCE(miniatura, ''), creada, editada "
                          "FROM cuaderno_paginas ORDER BY editada DESC, id DESC").fetchall()
    return [dict(zip(("id", "titulo", "fondo", "miniatura", "creada", "editada"), r)) for r in filas]


def obtener(jm, pagina_id):
    with jm._conectar() as c:
        _tabla(c)
        r = c.execute("SELECT id, titulo, fondo, COALESCE(trazos, '[]'), creada, editada "
                      "FROM cuaderno_paginas WHERE id = ?", (pagina_id,)).fetchone()
    if not r:
        return None
    p = dict(zip(("id", "titulo", "fondo", "trazos", "creada", "editada"), r))
    p["trazos"] = json.loads(p["trazos"])
    return p


def crear(jm, titulo="", fondo="liso"):
    ahora = _ahora()
    with jm._conectar() as c:
        _tabla(c)
        return c.execute("INSERT INTO cuaderno_paginas (titulo, fondo, trazos, miniatura, creada, editada) "
                         "VALUES (?, ?, '[]', '', ?, ?)", (titulo or "", _fondo(fondo), ahora, ahora)).lastrowid


def guardar(jm, pagina_id, titulo, fondo, trazos, miniatura=None):
    """Actualiza la página. `trazos` es la lista ya decodificada. Devuelve False
    si la página no existe o los datos no valen."""
    if not isinstance(trazos, list):
        return False
    datos = json.dumps(trazos, separators=(",", ":"))
    if len(datos) > MAX_TRAZOS_BYTES:
        return False
    mini = (miniatura if isinstance(miniatura, str) and miniatura.startswith("data:image/png")
            and len(miniatura) <= MAX_MINIATURA else None)
    with jm._conectar() as c:
        _tabla(c)
        n = c.execute("UPDATE cuaderno_paginas SET titulo = ?, fondo = ?, trazos = ?, editada = ?, "
                      "miniatura = COALESCE(?, miniatura) WHERE id = ?",
                      ((titulo or "").strip()[:80], _fondo(fondo), datos, _ahora(), mini, pagina_id)).rowcount
    return bool(n)


def borrar(jm, pagina_id):
    with jm._conectar() as c:
        _tabla(c)
        c.execute("DELETE FROM cuaderno_paginas WHERE id = ?", (pagina_id,))
        c.execute("DELETE FROM cuaderno_vinculos WHERE pagina_id = ?", (pagina_id,))


def vincular(jm, pagina_id, kind, jp):
    jp = (jp or "").strip()
    if kind not in KINDS or not jp:
        return False
    with jm._conectar() as c:
        _tabla(c)
        if not c.execute("SELECT 1 FROM cuaderno_paginas WHERE id = ?", (pagina_id,)).fetchone():
            return False
        c.execute("INSERT OR IGNORE INTO cuaderno_vinculos (pagina_id, kind, jp) VALUES (?, ?, ?)",
                  (pagina_id, kind, jp))
    return True


def desvincular(jm, pagina_id, kind, jp):
    with jm._conectar() as c:
        _tabla(c)
        c.execute("DELETE FROM cuaderno_vinculos WHERE pagina_id = ? AND kind = ? AND jp = ?",
                  (pagina_id, kind, jp))


def paginas_de(jm, kind, jp):
    """[{id, titulo, editada}] de las páginas ligadas a esa card."""
    with jm._conectar() as c:
        _tabla(c)
        filas = c.execute("SELECT p.id, p.titulo, p.editada FROM cuaderno_paginas p "
                          "JOIN cuaderno_vinculos v ON v.pagina_id = p.id "
                          "WHERE v.kind = ? AND v.jp = ? ORDER BY p.editada DESC", (kind, jp)).fetchall()
    return [dict(zip(("id", "titulo", "editada"), r)) for r in filas]


def tarjetas_de(jm, pagina_id):
    """Cards ligadas a una página, con lectura y significado (los que conocemos)."""
    with jm._conectar() as c:
        _tabla(c)
        filas = c.execute("SELECT kind, jp FROM cuaderno_vinculos WHERE pagina_id = ? "
                          "ORDER BY rowid", (pagina_id,)).fetchall()
    if not filas:
        return []
    conocidas = {(x["kind"], x["jp"]): x for x in cartas_conocidas(jm)}
    return [conocidas.get((k, jp), {"kind": k, "jp": jp, "reading": "", "meaning": ""}) for k, jp in filas]


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


def _plano(s):
    """Minúsculas y sin acentos, para que «dia» encuentre «día»."""
    return "".join(ch for ch in unicodedata.normalize("NFD", (s or "").lower())
                   if not unicodedata.combining(ch))


def buscar_cartas(jm, q, limite=20):
    """Cards cuyo jp, lectura o significado contienen `q` (primero las que empiezan por q)."""
    q = _plano(q).strip()
    if not q:
        return []
    hallados = []
    for c in cartas_conocidas(jm):
        campos = [_plano(c["jp"]), _plano(c["reading"]), _plano(c["meaning"])]
        if any(q in f for f in campos):
            hallados.append((not any(f.startswith(q) for f in campos), c))
    hallados.sort(key=lambda h: h[0])   # estable: las que empiezan por q, delante
    return [c for _, c in hallados[:limite]]


if __name__ == "__main__":
    import os
    import tempfile
    from core.japanese_memory import JapaneseMemory

    jm = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    assert listar(jm) == []
    a = crear(jm, "Lección 1")
    b = crear(jm, "", "cuadricula")
    assert obtener(jm, b)["fondo"] == "cuadricula" and obtener(jm, a)["trazos"] == []
    tr = [{"c": "#000000", "w": 3, "e": 0, "p": [[1, 2], [3, 4]]}]
    assert guardar(jm, a, "L1", "rayas", tr, "data:image/png;base64,AAAA")
    assert listar(jm)[0]["id"] == a and listar(jm)[0]["miniatura"].startswith("data:image/png")
    assert obtener(jm, a)["trazos"] == tr and obtener(jm, a)["fondo"] == "rayas"
    assert guardar(jm, a, "L1", "rayas", tr) and listar(jm)[0]["miniatura"]   # sin miniatura nueva: se conserva
    assert not guardar(jm, 999, "x", "liso", []) and not guardar(jm, a, "x", "liso", "no")
    assert vincular(jm, a, "kanji", "日") and vincular(jm, a, "kanji", "日") and not vincular(jm, 999, "kanji", "日")
    assert not vincular(jm, a, "otro", "日")
    assert [p["id"] for p in paginas_de(jm, "kanji", "日")] == [a] and paginas_de(jm, "vocabulario", "日") == []
    assert tarjetas_de(jm, a)[0]["jp"] == "日"
    desvincular(jm, a, "kanji", "日")
    assert paginas_de(jm, "kanji", "日") == []
    vincular(jm, a, "kanji", "日")
    borrar(jm, a)
    assert obtener(jm, a) is None and paginas_de(jm, "kanji", "日") == [] and len(listar(jm)) == 1
    k = next(x for x in KANJI_N5 if x["jp"] == "日")
    assert any(x["jp"] == "日" for x in buscar_cartas(jm, "日"))
    rd = (k.get("reading_card") or k.get("reading") or k.get("kun") or "").strip()
    assert rd and any(x["jp"] == "日" for x in buscar_cartas(jm, rd, 500)), rd
    es = k["meaning"].replace(" (kanji)", "").split(",")[0].split("/")[0].strip()
    assert any(x["jp"] == "日" for x in buscar_cartas(jm, es, 500)), es
    assert buscar_cartas(jm, "") == [] and len(buscar_cartas(jm, "a", 5)) <= 5
    print("ok")
