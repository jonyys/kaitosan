"""Fase 08 — el extractor califica can-dos, no ítems SRS.

- Una transcripción donde Laura pide comida en japonés deja el can-do de la
  unidad de comida en `en_progreso` (1 sesión) con su `evidencia` guardada.
- Con el extractor caído (`data is None`) ningún can-do cambia y no hay excepción.
- No-regresión: `_ejecutar_extraccion` ya no llama a `review(` ni a
  `get_due_items(` (el SRS de vocab/gram deja de moverlo el profesor — plan 08).
"""
import inspect
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

from ai.sensei import profesor as profesor_mod
from ai.sensei.curriculum import CURRICULUM
from ai.sensei.profesor import ProfesorJapones
from core.japanese_memory import JapaneseMemory

UNIDAD_COMIDA = next(u for u in CURRICULUM if u["id"] == "comida_bebida")
CAN_DO_PEDIR = "comida_pedir"  # 'Puedo pedir un plato o una bebida en un restaurante'

TRANSCRIPT = [
    {"role": "assistant", "content": "Estamos en un restaurante. Pídeme algo de la carta."},
    {"role": "user", "content": "コーヒーをください"},
    {"role": "assistant", "content": "【いいね】! Perfecto, un café."},
]


def _profesor(jap):
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    return ProfesorJapones(jap, MagicMock(), memoria, MagicMock())


def _preparar(jap, extractor):
    prof = _profesor(jap)
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    prof._foco_unidad = UNIDAD_COMIDA          # unidad abierta → sus can-dos activos
    prof.mensajes = list(TRANSCRIPT)
    prof._extraer_resumen_basico = lambda t: "resumen"
    prof._llamar_extractor = extractor
    return prof


def test_can_do_conseguido_queda_en_progreso_con_evidencia():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))
    evidencia = "Laura dijo 「コーヒーをください」 sin que Kaito se lo diera"
    respuesta = json.dumps({
        "summary": "Laura pidió un café en japonés sin ayuda.",
        "can_dos": [
            {"id": CAN_DO_PEDIR, "resultado": "conseguido", "evidencia": evidencia}
        ],
        "new_items": [], "sin_corregir": [], "episodios": [], "kaito_dijo": [],
    })
    prof = _preparar(jap, lambda h: respuesta)

    prof._ejecutar_extraccion(prof.session_id)

    prog = jap.can_dos_progreso()
    assert CAN_DO_PEDIR in prog, prog
    fila = prog[CAN_DO_PEDIR]
    assert fila["estado"] == "en_progreso", fila
    assert fila["veces_ok"] == 1, fila
    assert fila["nota"] == evidencia, fila


def test_extractor_caido_no_toca_ningun_can_do():
    jap = JapaneseMemory(os.path.join(tempfile.mkdtemp(), "t.db"))

    def _cae(historial):
        raise RuntimeError("sin API")

    prof = _preparar(jap, _cae)

    prof._ejecutar_extraccion(prof.session_id)  # no debe lanzar

    assert jap.can_dos_progreso() == {}


def test_ejecutar_extraccion_no_llama_srs():
    src = inspect.getsource(ProfesorJapones._ejecutar_extraccion)
    codigo = "\n".join(
        l for l in src.splitlines() if not l.lstrip().startswith("#")
    )
    assert "review(" not in codigo, "el extractor ya no debe recalificar el SRS"
    assert "get_due_items(" not in codigo
    assert not hasattr(profesor_mod, "_QUALITY_MAP"), "_QUALITY_MAP quedó huérfano"


if __name__ == "__main__":
    test_can_do_conseguido_queda_en_progreso_con_evidencia()
    test_extractor_caido_no_toca_ningun_can_do()
    test_ejecutar_extraccion_no_llama_srs()
    print("OK")
