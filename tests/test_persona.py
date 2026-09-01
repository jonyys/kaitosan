"""Fase 15 — Notas del profe: cómo va Laura como alumna, de una sesión a otra."""
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory
from ai.sensei.profesor import ProfesorJapones


def _profesor(jap):
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    return ProfesorJapones(jap, MagicMock(), memoria, MagicMock())


def _sembrar_sesion(jap, nota):
    with jap._conectar() as conn:
        sid = conn.execute(
            "INSERT INTO japanese_sessions (started_at) VALUES (datetime('now'))"
        ).lastrowid
    jap.guardar_resumen_sesion(sid, summary="s", nota_profe=nota)
    return sid


def test_nota_profe():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    prof = _profesor(jap)
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    prof.mensajes = [{"role": "user", "content": "わたし は のんだ… ¿o va が?"}]
    nota = "Duda mucho con は/が y se frustra, pero no se rinde: vuelve a intentarlo."
    prof.provider.completar.return_value = json.dumps({
        "summary": "Laura practicó el pasado casual.",
        "can_dos": [], "new_items": [], "sin_corregir": [],
        "episodios": [], "kaito_dijo": [],
        "nota_profe": nota,
    })
    prof._ejecutar_extraccion(prof.session_id)

    with jap._conectar() as conn:
        fila = conn.execute(
            "SELECT nota_profe FROM japanese_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert fila[0] == nota, fila


def test_montar_estado_incluye_notas_bajo_como_va_laura():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    _sembrar_sesion(jap, "Viene con energía y arranca ella los temas.")
    _sembrar_sesion(jap, "Hoy cansada, cuesta que suelte frases largas.")

    prof = _profesor(jap)
    recuerdas = prof._montar_estado()[0]
    assert "Cómo va Laura" in recuerdas
    assert "Viene con energía y arranca ella los temas." in recuerdas
    assert "Hoy cansada, cuesta que suelte frases largas." in recuerdas


def test_extractor_sin_nota_profe_no_rompe_y_guarda_vacia():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    prof = _profesor(jap)
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    prof.mensajes = [{"role": "user", "content": "hola"}]
    prof.provider.completar.return_value = json.dumps({
        "summary": "Charla corta.",
        "can_dos": [], "new_items": [], "sin_corregir": [],
        "episodios": [], "kaito_dijo": [],
    })
    prof._ejecutar_extraccion(prof.session_id)  # no debe lanzar

    with jap._conectar() as conn:
        fila = conn.execute(
            "SELECT nota_profe FROM japanese_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert (fila[0] or "") == "", fila
    assert jap.resumen_perfil()["notas_profe"] == []


# ── Fase 16 — Deberes entre sesiones ────────────────────────────────────────

def test_deberes():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    prof = _profesor(jap)

    # Sesión 1: Kaito propuso una tarea al despedirse; el extractor la captura.
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    prof.mensajes = [{"role": "user", "content": "じゃあね, hasta la semana que viene"}]
    deberes = "Apúntate en japonés tres cosas que tengas en tu mesa."
    prof.provider.completar.return_value = json.dumps({
        "summary": "Repaso y despedida.",
        "can_dos": [], "new_items": [], "sin_corregir": [],
        "episodios": [], "kaito_dijo": [], "nota_profe": "",
        "deberes": deberes,
    })
    prof._ejecutar_extraccion(prof.session_id)

    with jap._conectar() as conn:
        fila = conn.execute(
            "SELECT deberes FROM japanese_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert fila[0] == deberes, fila
    assert jap.resumen_perfil()["deberes_ultima_sesion"] == deberes

    # Sesión 2: los deberes entran PRIMEROS en el FOCO, antes de la unidad.
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    foco = prof._montar_estado()[1]
    assert foco.startswith("DEBERES DE LA SEMANA PASADA"), foco
    assert deberes in foco.splitlines()[0]
    for marca in ("Unidad actual", "Can-do de hoy", "Can-dos de esta unidad"):
        if marca in foco:
            assert foco.index("DEBERES DE LA SEMANA") < foco.index(marca), foco


def test_deberes_sin_campo_no_rompe():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    prof = _profesor(jap)
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    prof.mensajes = [{"role": "user", "content": "hola"}]
    prof.provider.completar.return_value = json.dumps({
        "summary": "Charla corta.",
        "can_dos": [], "new_items": [], "sin_corregir": [],
        "episodios": [], "kaito_dijo": [],
    })
    prof._ejecutar_extraccion(prof.session_id)  # no debe lanzar

    assert jap.resumen_perfil()["deberes_ultima_sesion"] == ""
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    foco = prof._montar_estado()[1]
    assert "DEBERES DE LA SEMANA" not in foco, foco


# ── Fase 17 — Arco de sesión ────────────────────────────────────────────────

def _par(u, a="ok"):
    return [{"role": "user", "content": u}, {"role": "assistant", "content": a}]


def test_arco():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    prof = _profesor(jap)
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()

    # Turnos 1 y 2 → calentamiento, con la nota de "aún no metas ejercicio".
    for pares in (0, 1):
        prof.mensajes = _par("hola") * pares
        foco = prof._montar_estado()[1]
        assert "FASE DE LA SESIÓN: calentamiento" in foco
        assert "aún no metas ejercicio de temario" in foco

    # Turno 4 (primero del cuerpo) → foco.
    prof.mensajes = _par("sigo") * 3
    foco = prof._montar_estado()[1]
    assert "FASE DE LA SESIÓN: foco" in foco

    # Laura se despide → cierre (gana a la cuenta de turno).
    prof.mensajes = _par("vale, lo dejamos por hoy, hasta la semana")
    foco = prof._montar_estado()[1]
    assert "FASE DE LA SESIÓN: cierre" in foco


if __name__ == "__main__":
    test_nota_profe()
    test_montar_estado_incluye_notas_bajo_como_va_laura()
    test_extractor_sin_nota_profe_no_rompe_y_guarda_vacia()
    test_deberes()
    test_deberes_sin_campo_no_rompe()
    test_arco()
    print("OK")
