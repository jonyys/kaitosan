"""Fase 11 — Boletín can-do: ruta /japones/boletin (solo lectura).

`import app` no arranca en este entorno (depende de `picamera2`, hardware de la
Pi; ver traceback: `core/camera.py` -> `from picamera2 import Picamera2`). El
test de ruta se sustituye por:
  - una app Flask mínima que registra la vista con el MISMO helper
    (`JapaneseMemory.boletin`) y la MISMA plantilla que usa `app.py`, y hace
    `GET /japones/boletin` con el test client -> 200;
  - con datos sembrados, el % de can-dos dominados y los contadores de
    inventario que arma la página coinciden con `SELECT COUNT(*)` directo por
    estado.
"""
import os
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template

from ai.sensei.curriculum import CURRICULUM
from core.japanese_memory import JapaneseMemory

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _jm():
    return JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))


def _curr_ids():
    """(vocab_no_kanji, gramatica, can_do_ids) del temario, sin duplicados y en
    orden de aparición — el mismo universo que cuenta `JapaneseMemory.boletin`."""
    vocab, gram, cds = [], [], []
    for u in CURRICULUM:
        for cd in u.get("can_dos", []):
            cds.append(cd["id"])
        for e in u.get("items", []):
            jp = str(e.get("jp") or "").strip()
            if not jp:
                continue
            if e.get("kind") == "gramatica" and jp not in gram:
                gram.append(jp)
            elif (e.get("kind") == "vocabulario" and e.get("tipo") != "kanji"
                    and jp not in vocab):
                vocab.append(jp)
    return vocab, gram, cds


def _sembrar(jm):
    """Siembra vocab/gram en varios status y can_dos en varios estados.
    Devuelve los conteos esperados calculados aparte, con SELECT directo."""
    vocab, gram, cds = _curr_ids()
    with jm._conectar() as c:
        # 3 vocab 'sabido' (reps>=2), 2 'sabido' por status, 2 'en_progreso'
        for w in vocab[:3]:
            c.execute("INSERT INTO japanese_vocabulary (word, status, reps) "
                      "VALUES (?, 'learning', 3)", (w,))
        for w in vocab[3:5]:
            c.execute("INSERT INTO japanese_vocabulary (word, status, reps) "
                      "VALUES (?, 'learned', 0)", (w,))
        for w in vocab[5:7]:
            c.execute("INSERT INTO japanese_vocabulary (word, status, reps) "
                      "VALUES (?, 'learning', 0)", (w,))
        # 4 gram 'sabido' (reps>=2), 2 'en_progreso'
        for g in gram[:4]:
            c.execute("INSERT INTO japanese_grammar (grammar_point, reps) "
                      "VALUES (?, 2)", (g,))
        for g in gram[4:6]:
            c.execute("INSERT INTO japanese_grammar (grammar_point, reps) "
                      "VALUES (?, 0)", (g,))
        # can_dos: 5 dominado, 3 en_progreso, 2 no_intentado
        for cid in cds[:5]:
            c.execute("INSERT INTO can_do_progreso (can_do_id, estado, veces_ok, "
                      "ultima_sesion) VALUES (?, 'dominado', 2, 7)", (cid,))
        for cid in cds[5:8]:
            c.execute("INSERT INTO can_do_progreso (can_do_id, estado, veces_ok) "
                      "VALUES (?, 'en_progreso', 1)", (cid,))
        for cid in cds[8:10]:
            c.execute("INSERT INTO can_do_progreso (can_do_id, estado) "
                      "VALUES (?, 'no_intentado')", (cid,))

    with jm._conectar() as c:
        vocab_sabido = c.execute(
            "SELECT COUNT(*) FROM japanese_vocabulary "
            "WHERE reps >= 2 OR status IN ('learned', 'mastered')"
        ).fetchone()[0]
        gram_sabido = c.execute(
            "SELECT COUNT(*) FROM japanese_grammar "
            "WHERE COALESCE(reps, 0) >= 2 OR COALESCE(mastery, 0) >= 100"
        ).fetchone()[0]
        cd_dominados = c.execute(
            "SELECT COUNT(*) FROM can_do_progreso WHERE estado = 'dominado'"
        ).fetchone()[0]
    return vocab_sabido, gram_sabido, cd_dominados


def _mini_app(jm):
    app = Flask("boletin_test",
                template_folder=os.path.join(_RAIZ, "templates"))

    @app.route("/japones/boletin")
    def japones_boletin():
        return render_template("japones_boletin.html", **jm.boletin())

    return app


def test_boletin():
    jm = _jm()
    vocab_sabido, gram_sabido, cd_dominados = _sembrar(jm)

    # 1) GET /japones/boletin -> 200 con la plantilla real
    cliente = _mini_app(jm).test_client()
    resp = cliente.get("/japones/boletin")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # 2) los contadores del helper coinciden con el SELECT COUNT(*) directo
    bol = jm.boletin()
    _, _, cds = _curr_ids()
    cd_total = len(cds)

    assert bol["vocab_sabido"] == vocab_sabido
    assert bol["gram_sabido"] == gram_sabido
    assert bol["candos_dominados"] == cd_dominados
    assert bol["candos_total"] == cd_total
    assert bol["candos_pct"] == round(cd_dominados * 100 / cd_total)
    assert bol["vocab_total"] == len(set(_curr_ids()[0]))
    assert bol["gram_total"] == len(set(_curr_ids()[1]))

    # 3) los números renderizados en la página son los del helper
    assert "{} / {}".format(bol["vocab_sabido"], bol["vocab_total"]) in html
    assert "{} / {}".format(bol["gram_sabido"], bol["gram_total"]) in html
    assert "{} / {}".format(bol["candos_dominados"], bol["candos_total"]) in html
    # símbolos de estado y la sesión de un dominado
    assert "●" in html  # ●
    assert "sesión 7" in html


def test_boletin_db_vacia():
    """Sin datos: 200, todo a cero, sin excepción."""
    jm = _jm()
    cliente = _mini_app(jm).test_client()
    resp = cliente.get("/japones/boletin")
    assert resp.status_code == 200

    bol = jm.boletin()
    assert bol["vocab_sabido"] == 0
    assert bol["gram_sabido"] == 0
    assert bol["candos_dominados"] == 0
    assert bol["candos_pct"] == 0
    assert bol["candos_total"] > 0
    assert bol["vocab_total"] == 710
    assert bol["gram_total"] == 90


# ── Fase 12 — Práctica de vocabulario por lección ──────────────────────────────
#
# `import app` sigue sin arrancar aquí (picamera2 / google.generativeai, deps de
# la Pi). Igual que `test_boletin`, se monta una app Flask mínima que registra la
# vista de esta fase con el MISMO cuerpo que `app.py:japones_vocabulario_practicar`
# (copiado literal), usando un `JapaneseMemory` real sobre BD tmp y el `CURRICULUM`
# real: los `review()`/`get_due_items()`/`add_item()`/`vocab_rows()` que ejercita
# son los de producción. Los valores SM-2 se comparan contra `review(.., "kanji")`
# con las mismas quality sobre una fila espejo.
import re

_RE_WORD = re.compile(r'name="word"\s+value="([^"]*)"')


def _unidad_vocab(uid):
    u = next((x for x in CURRICULUM if x.get("id") == uid), None)
    if not u:
        return None, []
    items, vistos = [], set()
    for e in u.get("items", []):
        if e.get("kind") != "vocabulario" or e.get("tipo") == "kanji":
            continue
        jp = str(e.get("jp") or "").strip()
        if not jp or jp in vistos:
            continue
        vistos.add(jp)
        items.append({
            "jp": jp,
            "reading": (e.get("reading") or "").strip(),
            "meaning": (e.get("meaning") or "").strip(),
            "ejemplo": (e.get("ejemplo") or "").strip(),
        })
    return u.get("nombre", "N5"), items


def _primera_unidad_vocab():
    for u in CURRICULUM:
        nombre, items = _unidad_vocab(u["id"])
        if len(items) >= 3:
            return u["id"], nombre, items
    raise AssertionError("sin unidad de vocabulario en CURRICULUM")


def _mini_practica_app(jm):
    import random as _random
    from flask import redirect, request, url_for

    app = Flask("practica_test",
                template_folder=os.path.join(_RAIZ, "templates"))

    @app.route("/japones/vocabulario/practicar", methods=["GET", "POST"],
               endpoint="japones_vocabulario_practicar")
    def vista():
        uid = (request.values.get("unidad") or "").strip()
        nombre, items = _unidad_vocab(uid)
        if nombre is None:
            return "no unit", 302
        por_jp = {it["jp"]: it for it in items}

        if request.method == "POST":
            jp = (request.form.get("word") or "").strip()
            try:
                quality = int(request.form.get("quality", 3))
            except ValueError:
                quality = 3
            quality = max(0, min(5, quality))
            it = por_jp.get(jp)
            if it:
                item_id = jm.get_item_id(jp, "vocabulario")
                if item_id is None:
                    jm.add_item("vocabulario", jp, reading=it["reading"],
                                meaning=it["meaning"], tipo="vocabulario")
                    item_id = jm.get_item_id(jp, "vocabulario")
                if item_id is not None:
                    jm.review(item_id, quality, "vocabulario")
            return redirect(url_for("japones_vocabulario_practicar", unidad=uid))

        due = [d for d in jm.get_due_items(limit=500, kind="vocabulario")
               if d["jp"] in por_jp]
        rows = jm.vocab_rows()
        nuevos = [jp for jp in por_jp
                  if jp not in rows or (rows[jp].get("reps") or 0) == 0]
        if due:
            jp, reps = due[0]["jp"], (due[0].get("reps") or 0)
        elif nuevos:
            jp, reps = _random.choice(nuevos), 0
        else:
            return render_template("japones_vocab_practica.html", unidad=uid,
                                   unidad_nombre=nombre, pendientes=0,
                                   al_dia=True, v=None)
        it = por_jp[jp]
        sentido = "es_jp" if reps % 2 == 0 else "jp_es"
        reading = it["reading"] if it["reading"] and it["reading"] != jp else ""
        v = {
            "jp": jp, "reading": reading, "meaning": it["meaning"],
            "ejemplo": it["ejemplo"], "sentido": sentido,
            "pregunta": it["meaning"] if sentido == "es_jp" else jp,
            "respuesta": jp if sentido == "es_jp" else it["meaning"],
        }
        return render_template("japones_vocab_practica.html", unidad=uid,
                               unidad_nombre=nombre, pendientes=len(due),
                               al_dia=False, v=v)

    return app


def _fila(jm, tabla, col, jp):
    with jm._conectar() as c:
        return c.execute(
            f"SELECT reps, ease_factor, interval_days, next_review, "
            f"{'status' if tabla != 'japanese_grammar' else 'mastery'} "
            f"FROM {tabla} WHERE {col} = ?", (jp,)
        ).fetchone()


def test_practica_vocab():
    uid, _nombre, items = _primera_unidad_vocab()
    jps = {it["jp"] for it in items}
    jm = _jm()
    cliente = _mini_practica_app(jm).test_client()

    # 1) GET → 200 y el ítem servido pertenece a la unidad
    for _ in range(6):
        resp = cliente.get("/japones/vocabulario/practicar?unidad=" + uid)
        assert resp.status_code == 200
        m = _RE_WORD.search(resp.get_data(as_text=True))
        assert m and m.group(1) in jps

    # unidad inexistente → no 200
    assert cliente.get("/japones/vocabulario/practicar?unidad=__nope__").status_code == 302

    # 2) POST de 5 calificaciones sobre un ítem: mismos valores SM-2 que kanji
    jp = sorted(jps)[0]
    it = next(i for i in items if i["jp"] == jp)
    jm.add_item("kanji", jp, reading=it["reading"], meaning=it["meaning"], tipo="kanji")
    kid = jm.get_item_id(jp, "kanji")

    secuencia = [5, 5, 5, 1, 5]  # q5×3 → learned; luego q1 (vuelve pronto); q5
    for i, q in enumerate(secuencia, 1):
        cliente.post("/japones/vocabulario/practicar",
                     data={"unidad": uid, "word": jp, "quality": str(q)})
        jm.review(kid, q, "kanji")

        v = _fila(jm, "japanese_vocabulary", "word", jp)
        k = _fila(jm, "japanese_kanji", "kanji", jp)
        assert v == k, f"paso {i} q={q}: vocab {v} != kanji {k}"

        if i == 3:  # q5 ×3 → status 'learned'
            assert v[4] == "learned", v
        if i == 4:  # q1 = 'No' → vuelve a salir pronto (next_review ~hoy)
            assert v[0] == 0 and v[2] == 1, v  # reps reseteado, interval 1 día
            from datetime import date, timedelta
            assert v[3] <= (date.today() + timedelta(days=1)).isoformat()


# ── Fase 13 — Práctica de gramática por lección ────────────────────────────────
#
# Gemela de test_practica_vocab. Misma razón para no `import app` (deps de la Pi):
# app Flask mínima con el cuerpo real de app.py:japones_gramatica_practicar sobre
# un JapaneseMemory real (BD tmp) y el CURRICULUM real. Los valores SM-2 se
# comparan contra review(.., "kanji") sobre una fila espejo; `mastery` es columna
# propia de japanese_grammar y la recalcula review() en cada paso — se comprueba
# aparte (100 tras cada q5, baja tras el q1).

_GRAM_TILDE = "〜～"


def _unidad_gram(uid):
    u = next((x for x in CURRICULUM if x.get("id") == uid), None)
    if not u:
        return None, []
    items, vistos = [], set()
    for e in u.get("items", []):
        if e.get("kind") != "gramatica":
            continue
        jp = str(e.get("jp") or "").strip()
        if not jp or jp in vistos:
            continue
        vistos.add(jp)
        items.append({
            "jp": jp,
            "meaning": (e.get("meaning") or "").strip(),
            "ejemplo": (e.get("ejemplo") or "").strip(),
            "literal": (e.get("literal") or "").strip(),
            "uso": (e.get("uso") or "").strip(),
        })
    return u.get("nombre", "N5"), items


def _gram_ejercicio(it):
    jp, ej = it["jp"], it["ejemplo"]
    core = jp.strip(_GRAM_TILDE)
    if core and ej and not any(t in core for t in _GRAM_TILDE) and core in ej:
        return {"modo": "hueco", "pregunta": ej.replace(core, "＿＿＿", 1),
                "respuesta": core, "patron": jp}
    return {"modo": "patron",
            "pregunta": it["meaning"] + (" — " + it["literal"] if it["literal"] else ""),
            "respuesta": jp, "patron": jp}


def _primera_unidad_gram():
    for u in CURRICULUM:
        nombre, items = _unidad_gram(u["id"])
        if len(items) >= 3:
            return u["id"], nombre, items
    raise AssertionError("sin unidad de gramática en CURRICULUM")


def _mini_practica_gram_app(jm):
    import random as _random
    from flask import redirect, request, url_for

    app = Flask("practica_gram_test",
                template_folder=os.path.join(_RAIZ, "templates"))

    @app.route("/japones/gramatica/practicar", methods=["GET", "POST"],
               endpoint="japones_gramatica_practicar")
    def vista():
        uid = (request.values.get("unidad") or "").strip()
        nombre, items = _unidad_gram(uid)
        if nombre is None:
            return "no unit", 302
        por_jp = {it["jp"]: it for it in items}

        if request.method == "POST":
            jp = (request.form.get("word") or "").strip()
            try:
                quality = int(request.form.get("quality", 3))
            except ValueError:
                quality = 3
            quality = max(0, min(5, quality))
            it = por_jp.get(jp)
            if it:
                item_id = jm.get_item_id(jp, "gramatica")
                if item_id is None:
                    jm.add_item("gramatica", jp, meaning=it["meaning"])
                    item_id = jm.get_item_id(jp, "gramatica")
                if item_id is not None:
                    jm.review(item_id, quality, "gramatica")
            return redirect(url_for("japones_gramatica_practicar", unidad=uid))

        due = [d for d in jm.get_due_items(limit=500, kind="gramatica")
               if d["jp"] in por_jp]
        rows = jm.gram_rows()
        nuevos = [jp for jp in por_jp
                  if jp not in rows or (rows[jp].get("reps") or 0) == 0]
        if due:
            jp = due[0]["jp"]
        elif nuevos:
            jp = _random.choice(nuevos)
        else:
            return render_template("japones_gram_practica.html", unidad=uid,
                                   unidad_nombre=nombre, pendientes=0,
                                   al_dia=True, v=None)
        it = por_jp[jp]
        ej = _gram_ejercicio(it)
        v = {"jp": jp, "meaning": it["meaning"], "literal": it["literal"],
             "uso": it["uso"], "ejemplo": it["ejemplo"], "modo": ej["modo"],
             "pregunta": ej["pregunta"], "respuesta": ej["respuesta"],
             "patron": ej["patron"]}
        return render_template("japones_gram_practica.html", unidad=uid,
                               unidad_nombre=nombre, pendientes=len(due),
                               al_dia=False, v=v)

    return app


def test_practica_gram():
    uid, _nombre, items = _primera_unidad_gram()
    jps = {it["jp"] for it in items}
    jm = _jm()
    cliente = _mini_practica_gram_app(jm).test_client()

    # 1) GET → 200 y el ítem servido pertenece a la unidad
    for _ in range(6):
        resp = cliente.get("/japones/gramatica/practicar?unidad=" + uid)
        assert resp.status_code == 200
        m = _RE_WORD.search(resp.get_data(as_text=True))
        assert m and m.group(1) in jps

    # unidad inexistente → no 200
    assert cliente.get("/japones/gramatica/practicar?unidad=__nope__").status_code == 302

    # 2) POST de 5 calificaciones sobre un ítem: SM-2 igual que kanji + mastery
    jp = sorted(jps)[0]
    it = next(i for i in items if i["jp"] == jp)
    jm.add_item("kanji", jp, reading="", meaning=it["meaning"], tipo="kanji")
    kid = jm.get_item_id(jp, "kanji")

    secuencia = [5, 5, 5, 1, 5]  # q5×3 → aprendida; luego q1 (vuelve pronto); q5
    masteries = []
    for i, q in enumerate(secuencia, 1):
        cliente.post("/japones/gramatica/practicar",
                     data={"unidad": uid, "word": jp, "quality": str(q)})
        jm.review(kid, q, "kanji")

        g = _fila(jm, "japanese_grammar", "grammar_point", jp)
        k = _fila(jm, "japanese_kanji", "kanji", jp)
        assert g[:4] == k[:4], f"paso {i} q={q}: gram {g[:4]} != kanji {k[:4]}"

        mastery = g[4]
        assert mastery is not None, f"paso {i}: mastery no calculado"
        masteries.append(mastery)

        if i <= 3:  # q5 ×3 → 'aprendida' = mastery >= 100
            assert mastery >= 100, (i, mastery)
        if i == 4:  # q1 = 'No' → mastery recalculado a la baja, vuelve pronto
            assert mastery < 100, mastery
            assert g[0] == 0 and g[2] == 1, g  # reps reseteado, interval 1 día
            from datetime import date, timedelta
            assert g[3] <= (date.today() + timedelta(days=1)).isoformat()

    # mastery se recalcula en cada review, no es estático: cae del paso 3 al 4
    assert masteries[3] < masteries[2], masteries


# ── Fase 14 — Circuito juego SRS → profesor ────────────────────────────────────
#
# Cierra el círculo del Bloque III: lo que la práctica web (Fases 12/13) lleva a
# 'learned' debe verse 'sabido' vía `estado_item()` — la fuente única que ya leen
# temario (Fase 07), boletín (Fase 11) y profesor (Fase 09/10). No hay lógica de
# `status`+`reps` duplicada que migrar; este test verifica el extremo a extremo.


def test_circuito():
    from unittest.mock import MagicMock

    from ai.sensei.profesor import ITEMS_CANDO_FOCO, ProfesorJapones

    # unidad N5 con can-dos y >= 2 vocab no-kanji entre los ítems que el FOCO lista
    elegida = None
    for u in CURRICULUM:
        if not u.get("can_dos"):
            continue
        vocab = [jp for e in u.get("items", [])[:ITEMS_CANDO_FOCO]
                 if e.get("kind") == "vocabulario" and e.get("tipo") != "kanji"
                 and (jp := str(e.get("jp") or "").strip())]
        if len(vocab) >= 2:
            elegida = (u, vocab[0], vocab[1])
            break
    assert elegida, "sin unidad con can-dos y vocab en CURRICULUM"
    unidad, jp, otro = elegida
    uid = unidad["id"]

    jm = _jm()
    cliente = _mini_practica_app(jm).test_client()

    # 1) la práctica web lleva el ítem a 'learned' (q5 ×3) ...
    for _ in range(3):
        cliente.post("/japones/vocabulario/practicar",
                     data={"unidad": uid, "word": jp, "quality": "5"})
    assert _fila(jm, "japanese_vocabulary", "word", jp)[4] == "learned"
    # ... y `estado_item()` -- la fuente única -- lo da 'sabido'
    assert jm.estado_item(jp, "vocabulario") == "sabido"

    # 2) ese 'sabido' llega al FOCO del profesor como [sabida]
    mem = MagicMock()
    mem.obtener_perfil.return_value = ""
    prof = ProfesorJapones(jm, MagicMock(), mem, MagicMock())
    prof._foco_unidad = unidad
    prof._foco_nuevos = []
    prof.session_id = 1
    _rec, foco = prof._montar_estado()
    linea = next((ln for ln in foco.splitlines()
                  if f"【{jp}】" in ln and "[sabida]" in ln), None)
    assert linea, "sin linea [sabida] para el item practicado en el FOCO:\n" + foco

    # 3) el boton "marcar como completa" deja OTRO item igual de 'sabido'
    jm.marcar_completo(otro, "vocabulario")
    assert jm.estado_item(otro, "vocabulario") == "sabido"


# ── Práctica de kanji por categoría ───────────────────────────────────────────
#
# Gemela de test_practica_vocab pero para /japones/kanjis/practicar?categoria=.
# Mismo motivo para no `import app` (deps de la Pi): app Flask mínima con el
# cuerpo real de app.py:japones_kanjis_practicar sobre un JapaneseMemory real
# (BD tmp) y el KANJI_N5 real.

from ai.sensei.kanji_n5 import KANJI_N5

_RE_KANJI = re.compile(r'name="kanji"\s+value="([^"]*)"')


def _mini_kanji_practica_app(jm):
    import random as _random
    from flask import redirect, render_template, request, url_for

    app = Flask("practica_kanji_test",
                template_folder=os.path.join(_RAIZ, "templates"))

    @app.route("/japones/kanjis/practicar", methods=["GET", "POST"],
               endpoint="japones_kanjis_practicar")
    def vista():
        cat = (request.values.get("categoria") or "").strip()
        pool = [k for k in KANJI_N5
                if cat in ("", "all") or k.get("categoria") == cat]
        if cat not in ("", "all") and not pool:
            return "no cat", 302
        jps_pool = {k.get("jp") for k in pool}
        cat_nombre = (pool[0].get("categoria_nombre", cat).split("—")[-1].strip()
                      if cat not in ("", "all") and pool else "")

        if request.method == "POST":
            kanji = (request.form.get("kanji") or "").strip()
            try:
                quality = int(request.form.get("quality", 2))
            except ValueError:
                quality = 2
            quality = max(0, min(5, quality))
            item = next((k for k in pool if k.get("jp") == kanji), None)
            if item:
                item_id = jm.get_item_id(kanji, "kanji")
                if item_id is None:
                    jm.add_item("kanji", kanji,
                                reading=(item.get("reading") or "").strip(),
                                meaning=(item.get("meaning") or "").strip(),
                                tipo="kanji")
                    item_id = jm.get_item_id(kanji, "kanji")
                if item_id is not None:
                    jm.review(item_id, quality, "kanji")
            return redirect(url_for("japones_kanjis_practicar",
                                    categoria=cat or None))

        due = [d["jp"] for d in jm.get_due_items(limit=500, kind="kanji")
               if d["jp"] in jps_pool]
        practicados = jm.get_practiced_set("kanji")
        nuevos = [k["jp"] for k in pool if k.get("jp") not in practicados]
        if due:
            jp = due[0]
        elif nuevos:
            jp = _random.choice(nuevos)
        else:
            return render_template("japones_kanji_practica.html", k=None,
                                   categoria=cat, categoria_nombre=cat_nombre,
                                   pendientes=0, al_dia=True)
        item = next(k for k in pool if k.get("jp") == jp)
        k = dict(item)
        k["mnemo"] = jm.get_mnemos().get(jp) or item.get("mnemo", "")
        return render_template("japones_kanji_practica.html", k=k,
                               categoria=cat, categoria_nombre=cat_nombre,
                               pendientes=len(due) + len(nuevos), al_dia=False)

    return app


def test_practica_kanji_por_categoria():
    cat = KANJI_N5[0]["categoria"]
    jps = {k["jp"] for k in KANJI_N5 if k["categoria"] == cat}
    assert len(jps) >= 2
    jm = _jm()
    cliente = _mini_kanji_practica_app(jm).test_client()

    # 1) GET con categoría → 200 y el kanji servido pertenece a la categoría
    for _ in range(6):
        resp = cliente.get("/japones/kanjis/practicar?categoria=" + cat)
        assert resp.status_code == 200
        m = _RE_KANJI.search(resp.get_data(as_text=True))
        assert m and m.group(1) in jps

    # categoría inexistente → 302 (no 200)
    assert cliente.get(
        "/japones/kanjis/practicar?categoria=__nope__").status_code == 302

    # sin categoría → practica todo el N5
    resp = cliente.get("/japones/kanjis/practicar")
    assert resp.status_code == 200
    m = _RE_KANJI.search(resp.get_data(as_text=True))
    assert m and m.group(1) in {k["jp"] for k in KANJI_N5}

    # 2) POST califica solo dentro de la categoría; el SM-2 avanza igual que kanji
    jp = sorted(jps)[0]
    it = next(k for k in KANJI_N5 if k["jp"] == jp)
    jm.add_item("kanji", jp + "_espejo", reading="", meaning="x", tipo="kanji")
    kid = jm.get_item_id(jp + "_espejo", "kanji")
    for q in (5, 5, 5):
        cliente.post("/japones/kanjis/practicar",
                     data={"categoria": cat, "kanji": jp, "quality": str(q)})
        jm.review(kid, q, "kanji")
    real = _fila(jm, "japanese_kanji", "kanji", jp)
    espejo = _fila(jm, "japanese_kanji", "kanji", jp + "_espejo")
    assert real[:4] == espejo[:4]

    # 3) toda la categoría dominada → estado "al día"
    for k in KANJI_N5:
        if k["categoria"] == cat:
            jm.marcar_completo(k["jp"], "kanji", reading="", meaning="x",
                               tipo="kanji")
    resp = cliente.get("/japones/kanjis/practicar?categoria=" + cat)
    assert resp.status_code == 200
    assert "Todo repasado" in resp.get_data(as_text=True)
