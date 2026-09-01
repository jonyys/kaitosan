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
