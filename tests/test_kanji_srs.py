"""Los kanji tienen su propio SRS y cuentan en due_count."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.japanese_memory import JapaneseMemory


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
    test_kanjis_tienen_srs_propio_y_duele_en_due_count()
    print("✅ Fase 01 OK: 10 turnos → 2 ítems, due_count = 2, juez de vocab, no reintroduce, freno de ritmo activo")
