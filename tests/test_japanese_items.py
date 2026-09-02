"""CRUD manual de vocab/kanji/gramática (core/japanese_items.py). Reemplaza las
15 rutas calcadas de app.py: aquí se prueba el SQL de las 5 operaciones sobre
las 3 tablas con un JapaneseMemory real en BD tmp.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core import japanese_items as ji
from core.japanese_memory import JapaneseMemory

_COL_ID = {"vocabulario": "word", "kanji": "kanji", "gramatica": "grammar_point"}
_TABLA = {"vocabulario": "japanese_vocabulary", "kanji": "japanese_kanji",
          "gramatica": "japanese_grammar"}


def _jm():
    return JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))


def _row(jm, kind, jp):
    with jm._conectar() as c:
        c.row_factory = __import__("sqlite3").Row
        r = c.execute(
            f"SELECT * FROM {_TABLA[kind]} WHERE {_COL_ID[kind]} = ?", (jp,)
        ).fetchone()
    return dict(r) if r else None


@pytest.mark.parametrize("kind", ji.KINDS)
def test_ciclo_completo(kind):
    jm = _jm()

    # añadir: sin campos -> False y no inserta
    assert ji.añadir(jm, kind, "", "algo") is False
    assert ji.añadir(jm, kind, "  ", "") is False

    assert ji.añadir(jm, kind, "テスト", "prueba") is True
    r = _row(jm, kind, "テスト")
    assert r is not None
    assert r["reps"] == 0 and r["next_review"]
    if kind == "gramatica":
        assert r["description"] == "prueba" and r["mastery"] == 0
    else:
        assert r["meaning"] == "prueba" and r["status"] == "learning"

    item_id = r["id"]

    # marcar_aprendido
    ji.marcar_aprendido(jm, kind, item_id)
    r = _row(jm, kind, "テスト")
    assert r["reps"] == 8 and r["interval_days"] == 36500
    if kind == "gramatica":
        assert r["mastery"] == 100
    else:
        assert r["status"] == "mastered"

    # resetear_srs
    ji.resetear_srs(jm, kind, item_id)
    r = _row(jm, kind, "テスト")
    assert r["reps"] == 0 and r["interval_days"] == 0
    if kind == "gramatica":
        assert r["mastery"] == 0
    else:
        assert r["status"] == "learning"

    # borrar
    ji.borrar(jm, kind, item_id)
    assert _row(jm, kind, "テスト") is None

    # borrar_todo
    ji.añadir(jm, kind, "A", "a")
    ji.añadir(jm, kind, "B", "b")
    ji.borrar_todo(jm, kind)
    with jm._conectar() as c:
        assert c.execute(f"SELECT COUNT(*) FROM {_TABLA[kind]}").fetchone()[0] == 0


# ── Wiring de las 15 rutas (mismo patrón que app.py:_wire_item_routes) ─────────
# `import app` no arranca aquí (deps de la Pi). Se replica el bucle de registro
# contra una app Flask mínima y se comprueba de punta a punta: form -> helper ->
# BD, y que las 15 URLs mantienen la ruta de siempre.
from flask import Flask, redirect, request


def _mini_app(jm):
    app = Flask("items_test")

    def wire(kind):
        def add():
            ji.añadir(jm, kind, request.form.get("jp", ""), request.form.get("es", ""))
            return redirect("/")

        def dele(item_id):
            ji.borrar(jm, kind, item_id); return redirect("/")

        def dele_all():
            ji.borrar_todo(jm, kind); return redirect("/")

        def reset(item_id):
            ji.resetear_srs(jm, kind, item_id); return redirect("/")

        def master(item_id):
            ji.marcar_aprendido(jm, kind, item_id); return redirect("/")

        b = f"/japones/{kind}"
        app.add_url_rule(f"{b}/añadir", f"{kind}_add", add, methods=["POST"])
        app.add_url_rule(f"{b}/borrar/<int:item_id>", f"{kind}_del", dele, methods=["POST"])
        app.add_url_rule(f"{b}/borrar-todo", f"{kind}_del_all", dele_all, methods=["POST"])
        app.add_url_rule(f"{b}/resetear-srs/<int:item_id>", f"{kind}_reset", reset, methods=["POST"])
        app.add_url_rule(f"{b}/marcar-aprendido/<int:item_id>", f"{kind}_master", master, methods=["POST"])

    for k in ji.KINDS:
        wire(k)
    return app


def test_rutas_registradas_y_ciclo_http():
    jm = _jm()
    cli = _mini_app(jm).test_client()

    for kind in ji.KINDS:
        b = f"/japones/{kind}"
        r = cli.post(f"{b}/añadir", data={"jp": "水", "es": "agua"})
        assert r.status_code == 302
        row = _row(jm, kind, "水")
        assert row is not None
        iid = row["id"]

        assert cli.post(f"{b}/marcar-aprendido/{iid}").status_code == 302
        assert _row(jm, kind, "水")["reps"] == 8
        assert cli.post(f"{b}/resetear-srs/{iid}").status_code == 302
        assert _row(jm, kind, "水")["reps"] == 0
        assert cli.post(f"{b}/borrar/{iid}").status_code == 302
        assert _row(jm, kind, "水") is None

        ji.añadir(jm, kind, "火", "fuego")
        assert cli.post(f"{b}/borrar-todo").status_code == 302
        assert _row(jm, kind, "火") is None

    # GET no está permitido (solo POST), la ruta existe
    assert cli.get("/japones/kanji/borrar-todo").status_code == 405
