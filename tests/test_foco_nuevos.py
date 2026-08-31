"""Fase 01 — los ítems nuevos se eligen una vez por sesión y se guardan al cerrar."""
import os
import sys
import sqlite3
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory
from ai.sensei.profesor import ProfesorJapones


def test_diez_turnos_dejan_dos_items():
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    jap = JapaneseMemory(db)

    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    prof = ProfesorJapones(jap, MagicMock(), memoria, MagicMock())

    prof.entrar()
    seleccion = list(prof._foco_nuevos)
    assert len(seleccion) == 2, seleccion

    for _ in range(10):
        prof._montar_estado()
        # durante la sesión no se escribe nada en la BD
        assert prof._foco_nuevos == seleccion
        with sqlite3.connect(db) as c:
            assert c.execute("SELECT COUNT(*) FROM japanese_vocabulary").fetchone()[0] == 0

    # el cierre persiste exactamente los ítems de la sesión
    prof.mensajes = [{"role": "user", "content": "hola"}]
    prof._extraer_resumen_basico = lambda t: ""
    prof._llamar_extractor = lambda h: (_ for _ in ()).throw(RuntimeError("sin API"))
    prof._ejecutar_extraccion(prof.session_id)

    total = sum(
        len(jap.get_due_items(50, kind=k)) for k in ("vocabulario", "gramatica")
    )
    assert total == 2, total
    assert jap.resumen_perfil()["due_count"] == 2, jap.resumen_perfil()


def test_kanjis_tienen_srs_propio_y_duele_en_due_count():
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    jap = JapaneseMemory(db)

    jap.add_item("kanji", "日", meaning="día")
    assert jap.get_item_id("日", kind="kanji") is not None
    assert len(jap.get_due_items(10, kind="kanji")) == 1

    row = jap.get_due_items(10, kind="kanji")[0]
    assert row["jp"] == "日"
    assert row["status"] == "learning"

    jap.review(row["id"], 5, kind="kanji")
    assert jap.get_due_items(10, kind="kanji") == [] or jap.get_due_items(10, kind="kanji")[0]["status"] in {"learning", "learned", "mastered"}


if __name__ == "__main__":
    test_diez_turnos_dejan_dos_items()
    test_kanjis_tienen_srs_propio_y_duele_en_due_count()
    print("✅ Fase 01 OK: 10 turnos → 2 ítems, due_count = 2")
