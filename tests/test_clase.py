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
    # cierra teforma_encadenar y empieza a enseñar el siguiente (guarda «empezado»)
    assert [c.args[:2] for c in p.jap_memory.set_can_do.call_args_list] == [
        ("teforma_encadenar", "empezado"), ("teforma_encadenar", "conseguido"),
        ("teforma_pedir", "empezado")]
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

    def juez(cd, m, fase, contexto=None):
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
    p.juez = lambda cd, m, fase="tarea", **k: llamadas.append(m) or True
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
    # Logs de la Pi (12-nov): la queja de que no se lo ha enseñado también es «no sé»
    p.clase = {"cd": "comida_gustos", "fase": "tarea", "tipo": "pendiente", "aciertos": 0, "fallos": 0}
    out = p._instruccion("Me estás pidiendo mucho sin habérmelo enseñado antes.")
    assert "no se acuerda" in out and p.clase["fase"] == "practicar"


def test_japones_que_whisper_tomo_por_español_cuenta():
    """Logs de la Pi (12-nov): «ohayō por la mañana, konbanwa por la noche y oyasumi antes
    de dormir» llegó como «Ohio por la mañana, con Bangwa…» y Kaito repetía la tarea."""
    p = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    p.activo = True
    vistos = []
    p.juez_romaji = lambda cd, m, fase, **k: vistos.append(m) or True
    p.clase = {"cd": "saludos_saludar", "fase": "tarea", "tipo": "nuevo", "aciertos": 0, "fallos": 0}
    p._instruccion("Ohio por la mañana, con Bangwa por la noche y Yasumi antes de dormir.")
    assert p.clase["aciertos"] == 1 and len(vistos) == 1
    p._instruccion("¿Y al mediodía qué se dice?")   # una pregunta no va al juez
    assert len(vistos) == 1 and p.clase["aciertos"] == 1
    # Logs (12-nov, 2.ª clase): «Ohio con Bang Bang, Hoy Azul». El STT lo vuelve a oír
    # forzando japonés y el juez valora primero esa versión, solo en ese turno.
    p.oir_japones("おはよう こんばんは おやすみ")
    p._instruccion("Ohio con Bang Bang, Hoy Azul.")
    assert vistos[-1] == "おはよう こんばんは おやすみ"
    p._instruccion("Ohio con Bang Bang, Hoy Azul.")
    assert vistos[-1] == "Ohio con Bang Bang, Hoy Azul."


def test_el_juez_ve_lo_ultimo_que_dijo_kaito():
    """Logs (12-nov): sin la situación de Kaito («…y al final me voy a dormir»), el juez
    rechazaba «おはようございます、こんばんは、おやすみなさい»."""
    p = ProfesorJapones(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    p.activo = True
    ctx = []
    p.juez = lambda cd, m, fase="tarea", contexto=None: ctx.append(contexto) or True
    p.mensajes = [{"role": "assistant", "content": "Son las nueve… y al final me voy a dormir."},
                  {"role": "user", "content": "vale"},
                  {"role": "assistant", "content": "Salúdame en cada momento."}]
    p.clase = {"cd": "saludos_saludar", "fase": "tarea", "tipo": "nuevo", "aciertos": 0, "fallos": 0}
    p._instruccion("おはようございます、こんばんは、おやすみなさい")
    assert ctx == ["Salúdame en cada momento."]


def test_stt_vuelve_a_oir_en_japones_lo_que_tomo_por_español():
    from ai.speech_to_text import _ruta_transcripcion

    class Stt:
        def __init__(self, crudo):
            self.crudo, self.llamadas = crudo, []

        def transcribir(self, a, idioma=None):
            self.llamadas.append(idioma)
            return self.crudo if idioma is None else "おはよう、こんばんは、おやすみ"

    oido = []
    kw = dict(sensei_activo=True, modo_conv=False, espera_japones=True, al_oir_ja=oido.append)
    assert _ruta_transcripcion(Stt("Ohio con Bang Bang, Hoy Azul."), "a.wav", **kw) == (
        "Ohio con Bang Bang, Hoy Azul.", None)
    assert oido == ["おはよう、こんばんは、おやすみ"]
    s = Stt("¿Cómo se dice tarde?")   # una pregunta: ni segunda pasada
    _ruta_transcripcion(s, "a.wav", **kw)
    assert s.llamadas == [None] and len(oido) == 1


def test_silencio_no_se_convierte_en_acierto():
    """Logs de la Pi: Laura callada → Whisper «.» → Azure silencio → Whisper-ja inventó
    «ご視聴ありがとうございました» y contó como acierto."""
    from ai.speech_to_text import _ruta_transcripcion, transcribir_para_turno

    class Stt:
        def __init__(self, crudo, azure):
            self.crudo, self.azure, self.llamadas = crudo, azure, []

        def transcribir(self, a, idioma=None):
            self.llamadas.append(("whisper", idioma))
            return self.crudo if idioma is None else "ご視聴ありがとうございました"

        def transcribir_con_pronunciacion(self, a, referencia=None):
            self.llamadas.append(("azure",))
            return self.azure

    kw = dict(sensei_activo=True, modo_conv=False, espera_japones=True)
    # Whisper devuelve solo «.»: ni Azure ni segundo Whisper
    s = Stt(".", None)
    assert _ruta_transcripcion(s, "a.wav", **kw) == ("", None) and s.llamadas == [("whisper", None)]
    # Azure oye silencio: turno vacío, sin caer a Whisper-ja
    s = Stt("あ", {"texto": "", "pron": None})
    assert _ruta_transcripcion(s, "a.wav", **kw) == ("", None)
    assert ("whisper", "ja") not in s.llamadas
    # y si aun así llega una frase fantasma, se descarta
    s = Stt("あ", None)
    assert transcribir_para_turno(s, "a.wav", **kw) == ("", None)


class _ProvStream:
    """Proveedor falso: completar_stream da trozos de texto; completar, la respuesta entera."""
    def __init__(self, trozos=None, falla_al_principio=False, corta_a_mitad=False):
        self.trozos, self.falla, self.corta, self.enteras = trozos or [], falla_al_principio, corta_a_mitad, 0

    def completar_stream(self, mensajes, **kw):
        if self.falla:
            raise RuntimeError("sin streaming")
        for i, t in enumerate(self.trozos):
            if self.corta and i == 2:
                raise ConnectionError("se cortó")
            yield t

    def completar(self, mensajes, **kw):
        self.enteras += 1
        return "".join(self.trozos) or "Respuesta entera de reserva, bastante larga."


def _profe(prov):
    p = ProfesorJapones(MagicMock(), prov, MagicMock(), MagicMock())
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "comida_bebida")
    p.activo = True
    p._recuerdas = lambda: ""
    p.clase = {"cd": "comida_gustos", "fase": "practicar", "aciertos": 0, "fallos": 0, "tipo": "nuevo"}
    return p


def test_streaming_da_frases_completas_y_la_respuesta_entera():
    trozos = ["¡Qué bien, Laura! Ahora cuéntame ", "algo con 【すきです", "。ね】 de tu día.", "\nOtra frase final sin punto"]
    prov, dichas = _ProvStream(trozos), []
    r = _profe(prov).responder_turno("hola", on_frase=dichas.append)
    assert dichas == ["¡Qué bien, Laura! Ahora cuéntame algo con 【すきです。ね】 de tu día.",
                      "Otra frase final sin punto"]       # sin cortar dentro de 【】
    assert r == "".join(trozos).strip() and prov.enteras == 0


def test_si_el_streaming_falla_antes_de_dar_nada_se_usa_el_camino_normal():
    prov, dichas = _ProvStream(falla_al_principio=True), []
    r = _profe(prov).responder_turno("hola", on_frase=dichas.append)
    assert dichas == [] and prov.enteras == 1 and "reserva" in r


def test_si_el_stream_se_corta_a_mitad_no_se_repite_lo_ya_dicho():
    prov, dichas = _ProvStream(["Primera frase bastante larga, de verdad. ", "Segunda ", "cortada"], corta_a_mitad=True), []
    r = _profe(prov).responder_turno("hola", on_frase=dichas.append)
    assert dichas[0].startswith("Primera frase") and prov.enteras == 0   # no se vuelve a pedir
    assert r.startswith("Primera frase")


def test_cortar_frases_une_las_cortas_y_respeta_los_bloques():
    from ai.sensei.clase import cortar_frases
    assert cortar_frases("¡Hola! Qué tal estás hoy, Laura? Bien") == (["¡Hola! Qué tal estás hoy, Laura?"], " Bien")
    assert cortar_frases("Di 【いち。に】 ahora mismo por favor.")[0] == ["Di 【いち。に】 ahora mismo por favor."]


def test_stream_de_openrouter_conserva_tildes_y_japones(monkeypatch):
    """Logs de la Pi: el SSE sin charset se leía como latin-1 («despuÃ©s») y la voz lo leía mal."""
    import json
    from ai import openrouter_provider as mod

    def sse(texto):
        return ("data: " + json.dumps({"choices": [{"delta": {"content": texto}}]}, ensure_ascii=False)).encode("utf-8")

    class Resp:
        status_code = 200
        text = ""
        def iter_lines(self, decode_unicode=False):
            if decode_unicode:   # lo que hacía el código malo: latin-1 si no hay charset
                for l in self.iter_lines():
                    yield l.decode("latin-1")
                return
            yield b": OPENROUTER PROCESSING"
            yield sse("Ayer, después del trabajo ")
            yield sse("jugaste 【あそびました】.")
            yield b"data: [DONE]"
        def close(self):
            pass

    monkeypatch.setattr(mod, "OPENROUTER_API_KEY", "x")
    monkeypatch.setattr(mod.requests, "post", lambda *a, **k: Resp())
    prov = mod.OpenRouterProvider(modelos=["m"])
    assert "".join(prov.completar_stream([{"role": "user", "content": "hola"}])) == \
        "Ayer, después del trabajo jugaste 【あそびました】."


def test_en_progreso_desde_que_se_empieza_a_ensenar(tmp_path):
    """Boletín (12-nov): tres sesiones sin cerrar el can-do y todo seguía en ○. Se marca ◐
    al empezar a enseñarlo, y el «conseguido» de esa misma sesión sigue sumando."""
    from core.japanese_memory import JapaneseMemory
    jm = JapaneseMemory(str(tmp_path / "j.db"))
    p = ProfesorJapones(jm, MagicMock(), MagicMock(), MagicMock())
    p.activo, p.session_id = True, 7
    p.clase = {"cd": "saludos_saludar", "fase": "presentar", "tipo": "nuevo", "aciertos": 0, "fallos": 0}
    p._instruccion("vamos allá")
    assert jm.can_dos_progreso()["saludos_saludar"]["estado"] == "en_progreso"
    jm.set_can_do("saludos_saludar", "conseguido", 7)
    assert jm.can_dos_progreso()["saludos_saludar"]["veces_ok"] == 1
    # un repaso (ya en progreso) o un dominado no se tocan al abrirlo
    p.clase = {"cd": "saludos_saludar", "fase": "repaso", "tipo": "pendiente", "aciertos": 0, "fallos": 0}
    p._instruccion("vamos allá")
    assert jm.can_dos_progreso()["saludos_saludar"]["veces_ok"] == 1


def test_pasa_a_lo_siguiente_cierra_como_parcial_y_abre_el_siguiente(tmp_path):
    """Logs (12-nov): «pasa a lo siguiente, que ya me lo sé» se trató como «no sé» y Kaito
    volvió a explicar. Ahora pasa al siguiente, sin darlo por conseguido."""
    from core.japanese_memory import JapaneseMemory
    jm = JapaneseMemory(str(tmp_path / "j.db"))
    p = ProfesorJapones(jm, MagicMock(), MagicMock(), MagicMock())
    p.activo, p.session_id = True, 7
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "saludos_basicos")
    p.clase = {"cd": "saludos_saludar", "fase": "tarea", "tipo": "nuevo", "aciertos": 0, "fallos": 0,
               "nuevos": 0, "hechos": []}
    out = p._instruccion("Pasa a lo siguiente, que ya me lo sé")
    assert "pasar a lo siguiente" in out and "Luego:" in out
    assert p.clase["cd"] != "saludos_saludar" and "saludos_saludar" in p.clase["hechos"]
    assert jm.can_dos_progreso()["saludos_saludar"]["estado"] == "en_progreso"
    # en la presentación no aplica (aún no se ha enseñado nada) y con japonés tampoco
    p.clase = {"cd": "saludos_gracias", "fase": "presentar", "tipo": "nuevo", "aciertos": 0, "fallos": 0}
    assert "pasar a lo siguiente" not in p._instruccion("ya me lo sé")


def test_el_juez_solo_ve_la_frase_de_kaito_en_las_tareas(monkeypatch):
    """12-nov: con la frase de Kaito el juez de la práctica rechazaba «おはよう、朝日» (1/3)
    cuando sin ella aprobaba (3/3)."""
    import ai.sensei.clase as clase

    class Prov:
        prompts = []

        def completar(self, mensajes, **kw):
            self.prompts.append(mensajes[0]["content"])
            return '{"cumple": true}'

    monkeypatch.setenv("JUEZ_MODELO", "x/y")
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setattr(clase, "_juez_prov", Prov())
    cd = {"texto": "t", "explicacion": "e", "tarea": "Laura tiene que: saludar"}
    assert clase.juez_cumple(cd, "おはよう", "practicar", contexto="PREGUNTA_DE_KAITO") is True
    assert clase.juez_cumple(cd, "おはよう", "tarea", contexto="PREGUNTA_DE_KAITO") is True
    assert "PREGUNTA_DE_KAITO" not in Prov.prompts[0] and "PREGUNTA_DE_KAITO" in Prov.prompts[1]


def test_vocabulario_solo_lo_que_kaito_dice_en_clase(tmp_path):
    """12-nov: la sesión registraba «los 2 siguientes del can-do» (さようなら, おやすみなさい…)
    aunque Kaito no los enseñara, y duplicaba お母さん / おかあさん."""
    from core.japanese_memory import JapaneseMemory
    jm = JapaneseMemory(str(tmp_path / "j.db"))
    p = ProfesorJapones(jm, MagicMock(), MagicMock(), MagicMock())
    p.session_id = 7
    p._extraer_resumen_basico = lambda t: "resumen"
    p._llamar_extractor = lambda h, **k: (_ for _ in ()).throw(RuntimeError("sin API"))
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "saludos_basicos")
    p._ejecutar_extraccion(7, [
        {"role": "assistant", "content": "Modo Sensei activado! 【やあ】, Laura. 【さようなら】"},  # apertura: no cuenta
        {"role": "user", "content": "vamos"},
        {"role": "assistant", "content": "【おはよう、おかあさん】 y de noche 【こんばんは】. 【きのう えいがを みました】"},
        {"role": "assistant", "content": "【おかあさん】 otra vez"},
    ])
    palabras = set(jm.vocab_rows())
    assert {"お母さん", "こんばんは", "昨日", "映画"} <= palabras
    assert "さようなら" not in palabras and "おかあさん" not in palabras and "今晩" not in palabras


def test_la_lista_de_palabras_vistas_tiene_tope_y_prioriza_las_usadas():
    jm = MagicMock()
    jm.resumen_perfil.return_value = {}
    filas = {f"w{i}": {"word": f"w{i}", "reading": f"w{i}", "meaning": f"m{i}", "reps": 0,
                       "sensei_usos": 5 if i == 3 else 0} for i in range(200)}
    jm.vocab_rows.return_value = filas
    mem = MagicMock()
    mem.obtener_perfil.return_value = ""
    p = ProfesorJapones(jm, MagicMock(), mem, MagicMock())
    r = p._recuerdas()
    linea = next(l for l in r.splitlines() if l.startswith("Palabras que Laura ya ha visto"))
    assert "las 60 más usadas; conoce 140 más" in linea
    assert linea.count("(m") == 60 and "w3 (m3)" in linea and "w199 (m199)" in linea  # usada y reciente
    assert "w0 (m0)" not in linea   # vieja y sin uso: fuera


def test_paso_a_lo_siguiente_lo_escribe_whisper_con_o():
    """Log 17:29 (12-nov): «Paso a lo siguiente, ya te he dicho 5 veces» no se reconoció."""
    from ai.sensei.profesor import _RE_SIGUIENTE
    for s in ["Paso a lo siguiente", "Pasa a lo siguiente, ya me lo sé", "pasemos a lo siguiente", "ya lo sé"]:
        assert _RE_SIGUIENTE.search(s), s
    for s in ["Paso por la oficina", "¿qué sigue?", "dime la frase siguiente"]:
        assert not _RE_SIGUIENTE.search(s), s


def test_los_nombres_propios_no_entran_al_vocabulario(tmp_path):
    """12-nov: el extractor registró ジョナサン como vocabulario."""
    import json
    from core.japanese_memory import JapaneseMemory
    jm = JapaneseMemory(str(tmp_path / "j.db"))
    p = ProfesorJapones(jm, MagicMock(), MagicMock(), MagicMock())
    p._extraer_resumen_basico = lambda t: "resumen"
    p._llamar_extractor = lambda h, **k: json.dumps({
        "summary": "s", "sin_corregir": [], "episodios": [], "kaito_dijo": [], "nota_profe": "",
        "new_items": [{"category": "vocabulario", "jp": jp, "es": es} for jp, es in
                      [("ジョナサン", "Jonathan"), ("マリサさん", "Marisa"), ("ラウラ", "Laura"),
                       ("Ana", "Ana"), ("ありがとう", "gracias")]]})
    p._foco_unidad = next(u for u in CURRICULUM if u["id"] == "saludos_basicos")
    p._ejecutar_extraccion(7, [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}])
    assert set(jm.vocab_rows()) == {"ありがとう"}
