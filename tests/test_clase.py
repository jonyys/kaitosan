"""Modo clase: transiciones de fase y conjugación sin LLM."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.profesor import ProfesorJapones
from ai.sensei.curriculum import CURRICULUM


def test_fases_de_teforma():
    p = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "te_forma")
    p.clase = {"cd": "teforma_encadenar", "fase": "presentar", "aciertos": 0}

    assert not p.espera_japones  # activo=False (sin entrar())
    assert "Preséntale" in p._instruccion("hola")
    p.activo = True
    assert p.espera_japones       # tras presentar, practica en japonés
    assert "ha mezclado" in p._instruccion("けさ おきて, y luego desayuné")
    assert p.clase["aciertos"] == 0
    assert "いって" in p._instruccion("かいしゃに いきて ました")      # error → corrige
    assert p.clase["aciertos"] == 0
    p._instruccion("おきて、たべて、でかけます")
    assert "Plantéale" in p._instruccion("うちに かえって、ねます")   # 2 aciertos → tarea
    assert p.clase["fase"] == "tarea"
    p._instruccion("コーヒーを のんで、でかけました")
    out = p._instruccion("シャワーを あびて、ねました")
    assert "Felicítala" in out and p.clase["cd"] == "teforma_pedir"
    p.jap_memory.set_can_do.assert_called_once()
    assert "español" in p._instruccion("¿y eso por qué?")
    assert "se despide" in p._instruccion("me voy a cenar, じゃあね")


def test_comprobacion_por_ingredientes_y_japones_suelto():
    from ai.sensei.clase import usa_patron
    from ai.sensei.kana import frases_para_card, normalizar_bloques_jp
    saludar = next(cd for u in CURRICULUM for cd in u.get("can_dos", [])
                   if cd["id"] == "saludos_saludar")
    assert usa_patron(saludar, "あさは おはようございます")
    assert not usa_patron(saludar, "hola qué tal")
    llano = {"patron": "llano"}
    assert usa_patron(llano, "きのう すしを たべた") and not usa_patron(llano, "すしを たべました")
    assert usa_patron({"claves": ["いただきます"]}, "じゃあ、いただきます!")
    assert normalizar_bloques_jp("帰る es godan, 【いいね】") == "【帰る】 es godan, 【いいね】"
    # en pantalla, siempre hiragana (nunca kanji)
    assert frases_para_card("Bien: 【今朝起きて、会社に行きました】 y 帰る") == ["けさおきて、かいしゃにいきました", "かえる"]


def test_todos_los_candos_tienen_datos_de_clase():
    for u in CURRICULUM:
        for cd in u.get("can_dos", []):
            assert cd.get("explicacion") and cd.get("tarea"), cd["id"]


def test_voz_con_acento_y_falsos_positivos():
    from ai.sensei.kana import normalizar_japones, tiene_espanol
    from ai.sensei.clase import errores
    assert normalizar_japones("Hon o yomite") == "ほんおよみて"
    assert normalizar_japones("カエリテ") == "かえりて"
    assert errores({}, normalizar_japones("Kaerite"))          # romaji/katakana también se corrigen
    assert errores({}, normalizar_japones("うん、のみた"))       # た mal, sin ser del can-do 'ta'
    assert not tiene_espanol("Un kyou wa isogashii")            # «un» es うん
    p = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "saludos_basicos")
    p.clase = {"cd": "saludos_saludar", "fase": "practicar", "aciertos": 0}
    p.activo = True
    assert "se despide" not in p._instruccion("さようなら")      # despedirse en japonés es práctica


def test_gustos_exige_el_patron_no_solo_el_ingrediente():
    from ai.sensei.clase import usa_patron
    gustos = next(cd for u in CURRICULUM for cd in u.get("can_dos", []) if cd["id"] == "comida_gustos")
    assert not usa_patron(gustos, "お茶をください")
    assert usa_patron(gustos, "コーヒーが好きです") and usa_patron(gustos, "さかなが きらいです")


def test_juez_manda_si_responde_y_si_no_valen_las_palabras_clave():
    from ai.sensei.clase import usa_patron
    gustos = next(cd for u in CURRICULUM for cd in u.get("can_dos", []) if cd["id"] == "comida_gustos")
    assert usa_patron(gustos, "お茶をください", juez=lambda cd, m: True)         # el juez decide
    assert not usa_patron(gustos, "コーヒーが好きです", juez=lambda cd, m: False)
    assert usa_patron(gustos, "コーヒーが好きです", juez=lambda cd, m: None)     # sin juez → clave
    assert not usa_patron(gustos, "お茶をください", juez=lambda cd, m: None)


def test_juez_adelantado_se_aprovecha_si_azure_escribe_lo_mismo():
    """Whisper dice X, el juez ya empieza; si Azure escribe lo mismo (aunque con otra
    puntuación o en kanji), no se vuelve a preguntar."""
    llamadas = []

    def juez(cd, m, fase):
        llamadas.append(m)
        return True

    p = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "comida_bebida")
    p.activo = True
    p.clase = {"cd": "comida_gustos", "fase": "practicar", "aciertos": 0, "fallos": 0}
    p.juez = juez
    p.precalentar_juez("コーヒーが すきです")
    cd = p._cd()
    assert p._juzgar(cd, "コーヒーが好きです。", "practicar") is True   # Azure: otro texto, misma frase
    assert len(llamadas) == 1
    assert p._juzgar(cd, "さかなが すきです", "practicar") is True     # otra frase: pregunta de nuevo
    assert len(llamadas) == 2
    # los objetivos de conjugación no usan juez
    p.clase["cd"] = "teforma_encadenar"
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "te_forma")
    p.precalentar_juez("おきて、たべて")
    assert len(llamadas) == 2


def test_no_se_ayuda_en_vez_de_repetir_y_no_llama_al_juez_en_español():
    """Logs de la Pi: «no sé hacerlo, explícame» → Kaito repetía la tarea con otro escenario."""
    llamadas = []
    p = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "comida_bebida")
    p.activo = True
    p.juez = lambda cd, m, fase="tarea": llamadas.append(m) or True
    # repaso (pendiente) en tarea: no se acuerda → vuelve a presentar y a practicar
    p.clase = {"cd": "comida_gustos", "fase": "tarea", "tipo": "pendiente", "aciertos": 1, "fallos": 0}
    out = p._instruccion("No sé hacerlo, ¿me lo explicas?")
    assert "no se acuerda" in out and "Preséntale" in out
    assert p.clase["fase"] == "practicar" and p.clase["aciertos"] == 0 and p.clase["fallos"] == 1
    # tarea nueva: da la palabra y simplifica, sin cambiar de situación
    p.clase = {"cd": "comida_gustos", "fase": "tarea", "tipo": "nuevo", "aciertos": 0, "fallos": 0}
    out = p._instruccion("Es que no sé cómo se hace")
    assert "dale TÚ la palabra" in out and p.clase["fase"] == "tarea"
    # una duda de vocabulario NO cuenta como fallo
    p.clase["fallos"] = 0
    out = p._instruccion("¿Cómo se dice jugar?")
    assert "misma situación" in out and p.clase["fallos"] == 0
    assert llamadas == []   # ningún mensaje en español llegó al juez


def test_voz_parte_los_trozos_largos_en_español_por_frases():
    from ai import text_to_speech as mod
    t = mod.TextToSpeech.__new__(mod.TextToSpeech)
    t.voice_es, t.voice_ja = "es", "ja"
    largo = "Primera frase bastante larga para llenar. " * 2 + "Segunda frase de cierre, que sigue. ¿Y una pregunta más?"
    trozos = t._partir_largos([(largo, "es"), ("ください", "ja")], maximo=110)
    assert all(len(x) <= 110 for x, v in trozos if v == "es") and len(trozos) >= 3
    assert " ".join(x for x, v in trozos if v == "es") == largo.strip()   # no se pierde nada
    assert trozos[-1] == ("ください", "ja")
