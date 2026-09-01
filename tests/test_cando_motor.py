"""Fase 06 — can-dos por unidad en `curriculum.py`.

- Toda unidad temática N5 de vocab/gramática tiene >= 2 can-dos.
- Las unidades de kanji (solo ítems `tipo == "kanji"`) NO llevan can-dos.
- Todos los `id` de can-do son únicos en todo el temario.
- Cada can-do tiene `texto` no vacío que empieza por "Puedo".
"""
import inspect
import os
import sys
import tempfile
from collections import Counter
from unittest.mock import MagicMock

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.prompts import cargar_prompt
from ai.sensei import profesor as profesor_mod
from ai.sensei.curriculum import CURRICULUM
from ai.sensei.profesor import ProfesorJapones
from core.japanese_memory import JapaneseMemory


def _es_tematica(unidad):
    return any(
        it["kind"] == "gramatica"
        or (it["kind"] == "vocabulario" and it.get("tipo") != "kanji")
        for it in unidad["items"]
    )


def test_candos():
    tematicas = [u for u in CURRICULUM if _es_tematica(u)]
    kanji = [u for u in CURRICULUM if not _es_tematica(u)]
    assert tematicas, "no hay unidades temáticas"

    sin_candos = [u["id"] for u in tematicas if len(u.get("can_dos", [])) < 2]
    assert not sin_candos, f"unidades temáticas con < 2 can-dos: {sin_candos}"

    kanji_con_candos = [u["id"] for u in kanji if u.get("can_dos")]
    assert not kanji_con_candos, f"unidades de kanji con can-dos: {kanji_con_candos}"

    ids = [cd["id"] for u in CURRICULUM for cd in u.get("can_dos", [])]
    dups = sorted({i for i, n in Counter(ids).items() if n > 1})
    assert not dups, f"can_do.id duplicados: {dups}"

    for u in CURRICULUM:
        for cd in u.get("can_dos", []):
            texto = (cd.get("texto") or "").strip()
            assert texto.startswith("Puedo"), (u["id"], cd.get("id"), texto)
            # id estable con prefijo de la unidad (o de un alias corto de ella)
            assert cd["id"] and cd["id"] == cd["id"].strip()


def _jm():
    return JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))


def test_set_can_do():
    jm = _jm()

    jm.set_can_do("x", "conseguido", 1)
    p = jm.can_dos_progreso()["x"]
    assert p["estado"] == "en_progreso" and p["veces_ok"] == 1

    jm.set_can_do("x", "conseguido", 2)
    assert jm.can_dos_progreso()["x"]["estado"] == "dominado"

    jm.set_can_do("x", "error", 3)
    p = jm.can_dos_progreso()["x"]
    assert p["estado"] == "en_progreso"
    assert p["ultima_sesion"] == 3

    # dos 'conseguido' en la MISMA sesión no bastan para dominar
    jm2 = _jm()
    jm2.set_can_do("y", "conseguido", 7)
    jm2.set_can_do("y", "conseguido", 7)
    p = jm2.can_dos_progreso()["y"]
    assert p["estado"] == "en_progreso" and p["veces_ok"] == 1


# Oráculo: transcripción textual de las clausuras `estado()` originales de
# `app.py:_temario_unidades()` (commit ae32cc8), con el renombrado 1:1 de la
# Fase 07. Se replican aquí en vez de importar app.py (que arrastra Flask+brain).
def _oraculo(kind, row):
    """row = (reps, status|mastery) o None."""
    if row is None:
        return "nueva"
    a, b = row
    if kind == "gramatica":
        aprendida = (a or 0) >= 2 or (b or 0) >= 100
    else:
        aprendida = (a or 0) >= 2 or b in ("learned", "mastered")
    return "aprendida" if aprendida else "en_curso"


_MAP = {"aprendida": "sabido", "en_curso": "en_progreso", "nueva": "nuevo"}


def test_estado_item_igual_que_pagina():
    jm = _jm()
    with jm._conectar() as c:
        # (reps, status) -> word
        vocab = {
            "v_learning": (0, "learning"),
            "v_reps2": (2, "learning"),
            "v_learned": (0, "learned"),
            "v_mastered": (0, "mastered"),
            "v_reps1": (1, "learning"),
        }
        for w, (reps, status) in vocab.items():
            c.execute(
                "INSERT INTO japanese_vocabulary (word, reps, status) VALUES (?, ?, ?)",
                (w, reps, status),
            )
        gram = {
            "g_cero": (0, 0),
            "g_reps2": (2, 0),
            "g_mastery100": (0, 100),
            "g_reps1": (1, 50),
        }
        for gp, (reps, mastery) in gram.items():
            c.execute(
                "INSERT INTO japanese_grammar (grammar_point, reps, mastery) VALUES (?, ?, ?)",
                (gp, reps, mastery),
            )

    for w, row in {**vocab, "v_ausente": None}.items():
        assert jm.estado_item(w, "vocabulario") == _MAP[_oraculo("vocabulario", row)], w
    for gp, row in {**gram, "g_ausente": None}.items():
        assert jm.estado_item(gp, "gramatica") == _MAP[_oraculo("gramatica", row)], gp


def test_fraccion_can_dos():
    unidad = next(u for u in CURRICULUM if len(u.get("can_dos", [])) == 4)
    ids = [cd["id"] for cd in unidad["can_dos"]]
    jm = _jm()

    assert jm.fraccion_can_dos(unidad["id"]) == 0.0
    assert jm.fraccion_can_dos("unidad_inexistente") == 0.0

    for cid in ids[:2]:
        jm.set_can_do(cid, "conseguido", 1)
        jm.set_can_do(cid, "conseguido", 2)
    assert jm.fraccion_can_dos(unidad["id"]) == 0.5


# ── Fase 09 — orquestación del profesor por can-do ───────────────────────────

def _profesor(jap):
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    prof = ProfesorJapones(jap, MagicMock(), memoria, MagicMock())
    return prof


def test_foco():
    """Unidad abierta, can-dos a 0: el FOCO nombra el primer can-do y lista sus
    ítems con marcador de estado, y no menciona la cola de repaso / due."""
    jm = _jm()
    prof = _profesor(jm)
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()

    _, foco = prof._montar_estado()
    unidad = CURRICULUM[0]  # BD limpia → primera unidad can-do
    primer_can_do = unidad["can_dos"][0]["texto"]

    assert f"Can-do de hoy: {primer_can_do}" in foco, foco
    # ítems del can-do con marcador de estado (BD limpia → todos nuevos)
    assert "[nueva]" in foco, foco
    primer_item = unidad["items"][0]["jp"]
    assert f"【{primer_item}】" in foco, foco

    bajo = foco.lower()
    for prohibida in ("cola de repaso", "srs hoy", "due"):
        assert prohibida not in bajo, (prohibida, foco)


def test_unidad_avanza_por_candos():
    """Con el 80 % de los can-dos de la unidad en 'dominado' (2 sesiones cada
    uno), unidad_actual() pasa a la unidad siguiente."""
    from ai.sensei.curriculum import unidad_actual

    jm = _jm()
    u0 = CURRICULUM[0]
    assert unidad_actual(jm)["id"] == u0["id"]

    # 4 can-dos → 80 % = los 4. 2 sesiones distintas 'conseguido' → 'dominado'.
    for cd in u0["can_dos"]:
        jm.set_can_do(cd["id"], "conseguido", 1)
        jm.set_can_do(cd["id"], "conseguido", 2)

    assert jm.fraccion_can_dos(u0["id"]) >= 0.8
    assert unidad_actual(jm)["id"] == CURRICULUM[1]["id"]


def test_sin_rotar_due():
    """El profesor ya no rota una cola due para vocab/gramática."""
    src = inspect.getsource(profesor_mod)
    assert "_rotar_due" not in src, "quedó rotación de cola due en profesor.py"
    assert "get_due_items(" not in src, "quedó get_due_items en el flujo del profesor"


def test_marcador_estado():
    """Fase 10 — cada ítem del FOCO lleva su marcador de estado. Un ítem sabido
    sale con [sabida]; uno nuevo, con [nueva]. Y el prompt trae la regla."""
    jm = _jm()
    unidad = CURRICULUM[0]  # BD limpia -> unidad can-do abierta
    sabido, nuevo = unidad["items"][0], unidad["items"][1]
    assert sabido["jp"] != nuevo["jp"]

    with jm._conectar() as c:
        if sabido["kind"] == "gramatica":
            c.execute(
                "INSERT INTO japanese_grammar (grammar_point, reps, mastery) VALUES (?, 2, 0)",
                (sabido["jp"],),
            )
        else:
            c.execute(
                "INSERT INTO japanese_vocabulary (word, reps, status) VALUES (?, 2, 'learned')",
                (sabido["jp"],),
            )
    assert jm.estado_item(sabido["jp"], sabido["kind"]) == "sabido"
    assert jm.estado_item(nuevo["jp"], nuevo["kind"]) == "nuevo"

    prof = _profesor(jm)
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    _, foco = prof._montar_estado()

    def _linea_foco_de(jp):
        pref = f"  - 【{jp}】"
        return next((ln for ln in foco.splitlines()
                     if ln.startswith(pref) and ("[sabida]" in ln or "[nueva]" in ln
                                                 or "[en progreso]" in ln)), None)

    ln_sabido = _linea_foco_de(sabido["jp"])
    ln_nuevo = _linea_foco_de(nuevo["jp"])
    assert ln_sabido and "[sabida]" in ln_sabido, foco
    assert ln_nuevo and "[nueva]" in ln_nuevo, foco

    prompt = cargar_prompt("profesor_japones")
    metodo = prompt.split("== MÉTODO DE ENSEÑANZA ==", 1)[1]
    assert "Cada palabra del FOCO lleva su estado" in metodo
    assert "[sabida]" in metodo and "[en progreso]" in metodo and "[nueva]" in metodo


def test_smoke_8_turnos_y_cierre():
    """Sustituto de `python simulate_sensei.py` (sin API key / sin
    google.generativeai en el entorno): 8 turnos + _montar_estado() y luego el
    cierre/extracción, todo con el LLM mockeado y sin excepción."""
    import json as _json

    jm = _jm()
    prof = _profesor(jm)
    prof.provider.completar.return_value = "Muy bien 【はい、そうです】"
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()

    for i in range(8):
        recuerdas, foco = prof._montar_estado()
        assert isinstance(recuerdas, str) and isinstance(foco, str)
        assert "Unidad actual:" in foco
        resp = prof.responder_turno(f"turno {i} 【こんにちは】")
        assert resp and resp.strip()

    assert len(prof.mensajes) == 16  # 8 pares user/assistant

    # Cierre + extracción: el extractor devuelve JSON mockeado, no debe lanzar.
    prof.provider.completar.return_value = _json.dumps({
        "summary": "Laura practicó saludos y presentaciones.",
        "can_dos": [], "new_items": [], "sin_corregir": [],
        "episodios": [], "kaito_dijo": [], "nota_profe": "Va soltándose.",
    })
    prof.cerrar_sesion_y_extraer()

    with jm._conectar() as conn:
        fila = conn.execute(
            "SELECT summary FROM japanese_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert fila and fila[0], fila


if __name__ == "__main__":
    test_candos()
    test_set_can_do()
    test_estado_item_igual_que_pagina()
    test_fraccion_can_dos()
    test_foco()
    test_unidad_avanza_por_candos()
    test_sin_rotar_due()
    test_marcador_estado()
    test_smoke_8_turnos_y_cierre()
    print("OK")
