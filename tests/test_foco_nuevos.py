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
    prof._llamar_extractor = lambda h, **k: (_ for _ in ()).throw(RuntimeError("sin API"))
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


def test_juez_vocab_reintenta_si_el_turno_pide_algo_no_enseñado():
    """_revisar_turno corta ANTES de hablar, no después: si el juez marca
    algún fallo, responder_turno reintenta con el proveedor principal en vez
    de dejar pasar una pregunta sin respuesta posible."""
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    jap = JapaneseMemory(db)
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""

    provider = MagicMock()
    provider.completar.side_effect = [
        "¿Cómo dirías 'programo'? @@OBJETIVO: わたしはプログラミングをします@@",
        "Vale, dime algo que ya sepas usando 【です】.",
    ]
    prof = ProfesorJapones(jap, provider, memoria, MagicMock())
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    prof._provider_juez = MagicMock()
    prof._provider_juez.completar.return_value = (
        '{"vocab_no_enseñado": true, "dicta_y_pide_repetir": false, '
        '"mas_de_una_cosa_nueva": false, "objetivo_no_coincide": false, '
        '"mas_de_una_correccion": false}'
    )

    respuesta = prof.responder_turno("vamos a practicar")

    assert provider.completar.call_count == 2, provider.completar.call_count
    assert "programo" not in respuesta.lower(), respuesta
    assert "です" in respuesta, respuesta


def test_juez_vocab_no_reintenta_si_dice_que_esta_bien():
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    jap = JapaneseMemory(db)
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""

    provider = MagicMock()
    provider.completar.return_value = "Repite conmigo: 【こんにちは】."
    prof = ProfesorJapones(jap, provider, memoria, MagicMock())
    prof.entrar()
    if prof.timer:
        prof.timer.cancel()
    prof._provider_juez = MagicMock()
    prof._provider_juez.completar.return_value = (
        '{"vocab_no_enseñado": false, "dicta_y_pide_repetir": false, '
        '"mas_de_una_cosa_nueva": false, "objetivo_no_coincide": false, '
        '"mas_de_una_correccion": false}'
    )

    prof.responder_turno("vamos a practicar")
    assert provider.completar.call_count == 1, provider.completar.call_count


def test_ya_dicho_esta_sesion_no_se_reintroduce_como_nuevo():
    """historial_sensei solo manda los últimos MAX_TURNOS pares al LLM — pasado
    ese punto, sin este listado el modelo "olvida" lo que enseñó al principio
    y lo reintroduce como si fuera nuevo (visto en sesión real: 【飲みます】
    explicado como novedad 3 veces en la misma conversación sin cortes). El
    FOCO se calcula sobre self.mensajes COMPLETO, así que el aviso sobrevive
    aunque el turno ya no esté en el contexto truncado."""
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    jap = JapaneseMemory(db)
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    prof = ProfesorJapones(jap, MagicMock(), memoria, MagicMock())
    prof.entrar()

    _, foco = prof._montar_estado()
    assert "Ya has dicho esto" not in foco, foco  # sesión recién empezada

    prof.mensajes = [{"role": "assistant", "content": "【飲みます】 significa bebo."}]
    _, foco = prof._montar_estado()
    assert "Ya has dicho esto" in foco and "【飲みます】" in foco, foco


def test_freno_de_ritmo_cuando_kaito_mete_muchas_palabras_seguidas():
    """El FOCO manda parar de introducir cosas nuevas si Kaito ya ha soltado
    UMBRAL_FRENO_NUEVOS bloques 【】 distintos esta sesión — no confía solo en
    el "una cosa nueva por turno" del prompt, que se salta con la racha."""
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    jap = JapaneseMemory(db)
    memoria = MagicMock()
    memoria.obtener_perfil.return_value = ""
    prof = ProfesorJapones(jap, MagicMock(), memoria, MagicMock())
    prof.entrar()

    _, foco = prof._montar_estado()
    assert "RITMO" not in foco, foco  # sesión recién empezada, nada que frenar

    # Simula que Kaito ya ha soltado 6 palabras/kana distintas esta sesión.
    prof.mensajes = [
        {"role": "assistant", "content": f"【{k}】 significa algo."}
        for k in "あいうえおか"
    ]
    _, foco = prof._montar_estado()
    assert "RITMO" in foco, foco
    assert "6" in foco, foco


if __name__ == "__main__":
    test_diez_turnos_dejan_dos_items()
    test_kanjis_tienen_srs_propio_y_duele_en_due_count()
    test_juez_vocab_reintenta_si_el_turno_pide_algo_no_enseñado()
    test_juez_vocab_no_reintenta_si_dice_que_esta_bien()
    test_ya_dicho_esta_sesion_no_se_reintroduce_como_nuevo()
    test_freno_de_ritmo_cuando_kaito_mete_muchas_palabras_seguidas()
    print("✅ Fase 01 OK: 10 turnos → 2 ítems, due_count = 2, juez de vocab, no reintroduce, freno de ritmo activo")
