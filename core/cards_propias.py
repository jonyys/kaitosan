"""Edición y alta manual de cards (vocabulario / gramática / kanji) desde la web.

El temario (ai/sensei/curriculum.py, kanji_n5.py) es de solo lectura, así que lo
que Laura edita o añade vive en la tabla `cards_editadas` y se aplica ENCIMA, en
memoria, sobre las mismas listas (CURRICULUM, KANJI_N5): así la web, la práctica
y el sensei ven el cambio sin tocar ningún otro consumidor.

- Editar: cualquier card (del temario o ya en la BD). El texto japonés no se
  cambia (es la clave del progreso); para eso, borrar y volver a añadir.
- Añadir: fila nueva en la BD (japanese_items.añadir, sin cambio de SRS) + sus
  campos extra aquí. Las de vocabulario/gramática salen en la unidad «extra»;
  las de kanji en la categoría «Mis kanjis» (`sincronizar_kanji`).
"""
import json

from ai.sensei.curriculum import CURRICULUM, ITEM_POR_JP
from ai.sensei.kanji_n5 import KANJI_N5, _item as _kanji_item
from core import japanese_items

CAMPOS = {
    "vocabulario": ("reading", "meaning", "tipo", "ejemplo", "literal", "uso"),
    "gramatica": ("reading", "meaning", "tipo", "ejemplo", "literal", "uso"),
    "kanji": ("meaning", "on", "kun", "trazos", "radical", "ejemplo", "vocab_ejemplo"),
}
CAT_PROPIOS = ("propios", "Mis kanjis")
# "unidad" (unidad del temario o categoría de kanji) se guarda junto a los campos,
# pero no es un campo de la ficha: solo se usa al crear.

_COL_SIGNIFICADO = {"vocabulario": "meaning", "gramatica": "description", "kanji": "meaning"}


def _tabla(c):
    c.execute("CREATE TABLE IF NOT EXISTS cards_editadas ("
              "kind TEXT, jp TEXT, data TEXT, PRIMARY KEY (kind, jp))")


def todas(jm, kind=None):
    """{(kind, jp): {campo: valor}} (o {jp: {...}} si se da `kind`)."""
    with jm._conectar() as c:
        _tabla(c)
        filas = c.execute("SELECT kind, jp, data FROM cards_editadas").fetchall()
    d = {(k, jp): json.loads(data) for k, jp, data in filas}
    return {jp: v for (k, jp), v in d.items() if k == kind} if kind else d


def _items_temario(kind, jp):
    if kind == "kanji":
        return [k for k in KANJI_N5 if k["jp"] == jp]
    return [it for u in CURRICULUM for it in u.get("items", [])
            if it.get("jp") == jp and it.get("kind") == kind
            and it.get("tipo") != "kanji"]


def _item_kanji_curriculum(jp):
    return [it for u in CURRICULUM for it in u.get("items", [])
            if it.get("jp") == jp and it.get("tipo") == "kanji"]


def _en_bd(jm, kind, jp):
    cfg = japanese_items._CFG[kind]
    with jm._conectar() as c:
        return c.execute(f"SELECT 1 FROM {cfg['tabla']} WHERE {cfg['col']} = ?",
                         (jp,)).fetchone() is not None


def opciones_unidad(kind):
    """[(id, nombre)] donde se puede colocar una card nueva de ese tipo."""
    if kind == "kanji":
        vistos = {}
        for k in KANJI_N5:
            if not k.get("propio"):
                vistos.setdefault(k["categoria"], k["categoria_nombre"].split("—")[-1].strip())
        return list(vistos.items())
    return [(u["id"], u["nombre"]) for u in CURRICULUM
            if not all(it.get("tipo") == "kanji" for it in u.get("items", [])) or not u.get("items")]


def _colocar(jm, kind, jp, datos):
    """Mete una card (vocabulario/gramática) de la BD en la unidad elegida del
    temario en memoria. Los kanji los coloca sincronizar_kanji."""
    u = next((u for u in CURRICULUM if u["id"] == datos.get("unidad")), None)
    if kind == "kanji" or not u or _items_temario(kind, jp) or not _en_bd(jm, kind, jp):
        return
    it = {"kind": kind, "jp": jp, "reading": datos.get("reading") or jp, "propio": True}
    u["items"].append(it)
    ITEM_POR_JP.setdefault(jp, it)


def _parchear(kind, jp, datos):
    """Aplica `datos` sobre los dicts del temario (en el sitio)."""
    if kind == "kanji":
        for it in _items_temario("kanji", jp) + _item_kanji_curriculum(jp):
            ra = lambda c: datos.get(c) or "—"          # noqa: E731
            nuevo = _kanji_item((
                jp, datos["meaning"], ra("on"), ra("kun"), ra("trazos"),
                ra("radical"), datos.get("ejemplo", ""), it.get("literal", ""),
                it.get("mnemo", ""), datos.get("vocab_ejemplo", "")))
            nuevo.update({k: it[k] for k in ("categoria", "categoria_nombre", "propio") if k in it})
            it.clear()
            it.update(nuevo)
        return
    for it in _items_temario(kind, jp):
        for c, v in datos.items():
            if v or c not in ("reading", "meaning"):    # lectura/significado no se vacían
                it[c] = v


def guardar(jm, kind, form):
    """Crea (form['nuevo']=='1') o edita una card. Devuelve None si todo fue bien
    o el mensaje de error."""
    jp = (form.get("jp") or "").strip()
    datos = {c: (form.get(c) or "").strip() for c in CAMPOS[kind]}
    if not (jp and datos["meaning"]):
        return "El texto japonés y el significado son obligatorios"
    nuevo = form.get("nuevo") == "1"
    if nuevo:
        datos["unidad"] = (form.get("unidad") or "").strip()
    existe = bool(_items_temario(kind, jp)) or _en_bd(jm, kind, jp)
    if nuevo and existe:
        return f"'{jp}' ya existe: ábrela y edítala"
    if not nuevo and not existe:
        return f"'{jp}' no existe"
    if nuevo:
        japanese_items.añadir(jm, kind, jp, datos["meaning"])
    cfg = japanese_items._CFG[kind]
    with jm._conectar() as c:
        _tabla(c)
        c.execute("INSERT OR REPLACE INTO cards_editadas VALUES (?, ?, ?)",
                  (kind, jp, json.dumps(datos, ensure_ascii=False)))
        c.execute(f"UPDATE {cfg['tabla']} SET {_COL_SIGNIFICADO[kind]} = ? "
                  f"WHERE {cfg['col']} = ?", (datos["meaning"], jp))
        if kind == "vocabulario":
            c.execute("UPDATE japanese_vocabulary SET "
                      "reading = COALESCE(NULLIF(?, ''), reading), "
                      "type = COALESCE(NULLIF(?, ''), type) WHERE word = ?",
                      (datos["reading"], datos["tipo"], jp))
    if nuevo:
        _colocar(jm, kind, jp, datos)
    _parchear(kind, jp, datos)
    if kind == "kanji":
        sincronizar_kanji(jm)
    return None


def sincronizar_kanji(jm):
    """Deja en KANJI_N5 los kanji propios que siguen en la BD (borrar la fila en
    el panel los quita de la web) y reaplica las ediciones del temario."""
    KANJI_N5[:] = [k for k in KANJI_N5 if not k.get("propio")]
    cats = dict(opciones_unidad("kanji"))
    for jp, datos in todas(jm, "kanji").items():
        if _items_temario("kanji", jp):
            continue
        if _en_bd(jm, "kanji", jp):
            it = _kanji_item((jp, datos["meaning"], datos.get("on") or "—",
                              datos.get("kun") or "—", datos.get("trazos") or "—",
                              datos.get("radical") or "—", datos.get("ejemplo", ""),
                              "", "", datos.get("vocab_ejemplo", "")))
            cat = datos.get("unidad") if datos.get("unidad") in cats else CAT_PROPIOS[0]
            KANJI_N5.append(dict(it, propio=True, categoria=cat,
                                 categoria_nombre=cats.get(cat, CAT_PROPIOS[1])))


def aplicar(jm):
    """Al arrancar: reaplica todas las ediciones sobre el temario en memoria."""
    for (kind, jp), datos in todas(jm).items():
        if kind == "kanji" and not _items_temario("kanji", jp):
            continue                                    # propio: lo gestiona sincronizar
        _colocar(jm, kind, jp, datos)
        _parchear(kind, jp, datos)
    sincronizar_kanji(jm)


if __name__ == "__main__":
    import tempfile, os
    from core.japanese_memory import JapaneseMemory
    jm = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    orig = next(it for u in CURRICULUM for it in u["items"] if it["kind"] == "vocabulario" and it.get("tipo") != "kanji")
    f = {"jp": orig["jp"], "meaning": "EDITADO", "ejemplo": "ej"}
    assert guardar(jm, "vocabulario", f) is None and orig["meaning"] == "EDITADO"
    assert guardar(jm, "vocabulario", {**f, "jp": "ぜんぜんないよ", "nuevo": "1"}) is None
    assert guardar(jm, "vocabulario", {**f, "jp": "ぜんぜんないよ", "nuevo": "1"}) is not None
    assert guardar(jm, "kanji", {"jp": "鬱", "meaning": "melancolía", "nuevo": "1"}) is None
    assert any(k["jp"] == "鬱" for k in KANJI_N5)
    uid, _ = opciones_unidad("vocabulario")[0]
    assert guardar(jm, "vocabulario", {**f, "jp": "ぜんぜん2", "nuevo": "1", "unidad": uid}) is None
    assert any(it["jp"] == "ぜんぜん2" for it in next(u for u in CURRICULUM if u["id"] == uid)["items"])
    cid, cn = opciones_unidad("kanji")[0]
    assert guardar(jm, "kanji", {"jp": "鯨", "meaning": "ballena", "nuevo": "1", "unidad": cid}) is None
    assert next(k for k in KANJI_N5 if k["jp"] == "鯨")["categoria"] == cid
    assert guardar(jm, "kanji", {"jp": "鯨", "meaning": "ballena2"}) is None
    assert sum(k["jp"] == "鯨" for k in KANJI_N5) == 1
    k0 = KANJI_N5[0]
    assert guardar(jm, "kanji", {"jp": k0["jp"], "meaning": "otro", "on": "X"}) is None and k0["meaning"] == "otro (kanji)"
    print("ok")
