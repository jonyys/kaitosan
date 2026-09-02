"""CRUD manual de vocabulario / kanji / gramática desde el panel (app.py).

Antes eran 15 rutas casi calcadas (5 operaciones × 3 tipos) con el SQL repetido
en cada una. Aquí vive una vez, en `_CFG` por tipo; app.py registra las 15 URLs
en un bucle y cada vista solo hace flash + redirect.

`kind` ∈ {"vocabulario", "kanji", "gramatica"}. Cada función abre su conexión
con `jm._conectar()` (context manager: commitea al salir sin error).
"""
from datetime import date

_CFG = {
    "vocabulario": {
        "tabla": "japanese_vocabulary",
        "col": "word",
        "insert": (
            "INSERT INTO japanese_vocabulary "
            "(word, meaning, status, confidence, errors, times_reviewed, "
            " reps, ease_factor, interval_days, next_review, times_correct) "
            "VALUES (?, ?, 'learning', 0, 0, 0, 0, 2.5, 0, ?, 0)"
        ),
        "reset": (
            "UPDATE japanese_vocabulary SET "
            "reps=0, ease_factor=2.5, interval_days=0, next_review=date('now'), "
            "status='learning', times_reviewed=0, times_correct=0, errors=0 "
            "WHERE id=?"
        ),
        "master": (
            "UPDATE japanese_vocabulary SET "
            "status='mastered', reps=8, ease_factor=2.5, interval_days=36500, "
            "next_review=date('now','+36500 days'), errors=0 WHERE id=?"
        ),
    },
    "kanji": {
        "tabla": "japanese_kanji",
        "col": "kanji",
        "insert": (
            "INSERT INTO japanese_kanji "
            "(kanji, meaning, status, confidence, errors, times_reviewed, "
            " reps, ease_factor, interval_days, next_review, times_correct) "
            "VALUES (?, ?, 'learning', 0, 0, 0, 0, 2.5, 0, ?, 0)"
        ),
        "reset": (
            "UPDATE japanese_kanji SET "
            "reps=0, ease_factor=2.5, interval_days=0, next_review=date('now'), "
            "status='learning', times_reviewed=0, times_correct=0, errors=0 "
            "WHERE id=?"
        ),
        "master": (
            "UPDATE japanese_kanji SET "
            "status='mastered', reps=8, ease_factor=2.5, interval_days=36500, "
            "next_review=date('now','+36500 days'), errors=0 WHERE id=?"
        ),
    },
    "gramatica": {
        "tabla": "japanese_grammar",
        "col": "grammar_point",
        "insert": (
            "INSERT INTO japanese_grammar "
            "(grammar_point, description, mastery, errors, "
            " reps, ease_factor, interval_days, next_review, times_seen, times_correct) "
            "VALUES (?, ?, 0, 0, 0, 2.5, 0, ?, 0, 0)"
        ),
        "reset": (
            "UPDATE japanese_grammar SET "
            "reps=0, ease_factor=2.5, interval_days=0, next_review=date('now'), "
            "mastery=0, times_seen=0, times_correct=0, errors=0 WHERE id=?"
        ),
        "master": (
            "UPDATE japanese_grammar SET "
            "mastery=100, reps=8, ease_factor=2.5, interval_days=36500, "
            "next_review=date('now','+36500 days'), errors=0 WHERE id=?"
        ),
    },
}

KINDS = tuple(_CFG)


def añadir(jm, kind, jp, es):
    """Inserta un ítem manual. Devuelve True si se insertó, False si faltaban
    campos (jp o es vacíos)."""
    jp, es = (jp or "").strip(), (es or "").strip()
    if not (jp and es):
        return False
    with jm._conectar() as c:
        c.execute(_CFG[kind]["insert"], (jp, es, date.today().isoformat()))
    return True


def borrar(jm, kind, item_id):
    with jm._conectar() as c:
        c.execute(f"DELETE FROM {_CFG[kind]['tabla']} WHERE id = ?", (item_id,))


def borrar_todo(jm, kind):
    with jm._conectar() as c:
        c.execute(f"DELETE FROM {_CFG[kind]['tabla']}")


def resetear_srs(jm, kind, item_id):
    with jm._conectar() as c:
        c.execute(_CFG[kind]["reset"], (item_id,))


def marcar_aprendido(jm, kind, item_id):
    with jm._conectar() as c:
        c.execute(_CFG[kind]["master"], (item_id,))
