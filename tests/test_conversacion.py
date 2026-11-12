"""Cuándo sigue escuchando tras responder, y callarlo mientras habla."""
import importlib
import sys
import threading
import time
from unittest import mock

import pytest

from core.emociones import extraer_cierre, extraer_emocion


@pytest.fixture(autouse=True)
def audio_falso():
    """Fuera de la Pi no están las librerías de audio: se simulan solo si faltan."""
    faltan = {}
    for nombre in ("sounddevice", "pyaudio", "soundfile", "livekit", "livekit.wakeword"):
        try:
            importlib.import_module(nombre)
        except ImportError:
            faltan[nombre] = mock.MagicMock()
    with mock.patch.dict(sys.modules, faltan):
        yield


@pytest.mark.parametrize("entrada, cerrado, texto", [
    ("[neutral] [fin] Hecho.", True, "[neutral] Hecho."),
    ("[fin] [neutral] Hecho.", True, "[neutral] Hecho."),
    ("[FIN] Hecho.", True, "Hecho."),
    ("**[fin]** Hecho.", True, "Hecho."),
    ("Hecho. [fin]", True, "Hecho. "),
    ("[feliz] ¿Qué tal?", False, "[feliz] ¿Qué tal?"),
    ("El [final] de la peli.", False, "El [final] de la peli."),
    ("", False, ""),
])
def test_extraer_cierre(entrada, cerrado, texto):
    assert extraer_cierre(entrada) == (cerrado, texto)


def test_cierre_y_emocion_juntos_no_se_leen_en_voz_alta():
    cerrado, resto = extraer_cierre("[neutral] [fin] Hecho, alarma puesta.")
    assert cerrado
    assert extraer_emocion(resto) == (None, "Hecho, alarma puesta.")


class TtsFalso:
    def __init__(self, callado=False):
        self._c = callado

    def hablar(self, texto, lento_extra=False, on_start=None):
        on_start()

    def hablar_frases(self, frases, lento_extra=False, on_start=None):
        """Como la real: espera frases hasta None; suena con la primera."""
        dichas = []
        while True:
            f = frases.get(timeout=5)
            if f is None:
                break
            if not dichas:
                on_start()
            dichas.append(f)
        self.dichas = dichas

    def callado(self):
        return self._c

    def empezar_turno(self):
        pass


def ciclo(asunto_cerrado=False, callado=False, salir_de_sensei=False):
    """Un _ciclo_voz con todo falso. Devuelve si seguiría escuchando."""
    from core import listener as mod

    estado = {"v": "idle"}
    state = mock.Mock(get=lambda: estado["v"], cambiar=lambda v: estado.update(v=v))
    activo = [True, False] if salir_de_sensei else [False, False]
    profesor = mock.Mock(modo_conv=False, ultima_frase_objetivo=None)
    profesor.esta_activo.side_effect = lambda: activo[0] if len(activo) == 1 else activo.pop(0)
    brain = mock.Mock(profesor=profesor, ultimo_turno_ts=0.0, asunto_cerrado=asunto_cerrado,
                      _emitir_desactivar_sensei=False)
    brain.responder.return_value = ("Respuesta", False)

    v = mod.VoiceListener.__new__(mod.VoiceListener)
    v.recorder = mock.Mock(record_vad=lambda timeout_inicio_seg=0: "a.wav")
    v.stt = mock.Mock()
    v.brain, v.tts, v.state, v.socketio = brain, TtsFalso(callado), state, mock.Mock()
    with mock.patch.object(mod, "transcribir_para_turno", return_value=("hola", None)):
        return v._ciclo_voz()


def test_sigue_escuchando_por_defecto():
    assert ciclo() is True


def test_no_sigue_si_el_asunto_esta_cerrado():
    assert ciclo(asunto_cerrado=True) is False


def test_no_sigue_si_le_han_mandado_callar():
    assert ciclo(callado=True) is False


class SdFalso:
    """Como PortAudio en la Pi: parar el stream desde fuera es el fallo que se evita."""

    class CallbackStop(Exception):
        pass

    def __init__(self):
        self.sonado = []
        self.creados = 0

    def OutputStream(self, callback, finished_callback, **_):
        self.creados += 1
        sd = self

        class Stream:
            def start(self):
                threading.Thread(target=self._bucle, daemon=True).start()

            def _bucle(self):
                import numpy as np
                while True:
                    salida = np.full((480, 1), 9.0, dtype=np.float32)
                    try:
                        callback(salida, 480, None, None)
                    except sd.CallbackStop:
                        sd.sonado.append(salida.copy())
                        break
                    sd.sonado.append(salida.copy())
                    time.sleep(0.001)
                finished_callback()

            def stop(self):
                raise AssertionError("parar el stream desde fuera bloquea PortAudio")

            abort = stop

            def close(self):
                pass

        return Stream()

    def stop(self):
        raise AssertionError("sd.stop bloquea PortAudio en la Pi")


def _tts(mod):
    t = mod.TextToSpeech.__new__(mod.TextToSpeech)
    t.device, t.sample_rate_device = None, 48000
    t._callado = threading.Event()
    t.socketio = mock.Mock()
    return t


def test_suena_todo_el_audio_y_rellena_el_final_con_silencio():
    import numpy as np
    from ai import text_to_speech as mod

    t = _tts(mod)
    audio = np.arange(1, 1001, dtype=np.float32)
    sd = SdFalso()
    with mock.patch.object(mod, "sd", sd), mock.patch("core.system_settings.volumen_factor", return_value=1.0):
        t._reproducir_con_control_boca(audio, [])
    sonado = np.concatenate(sd.sonado)[:, 0]
    assert np.array_equal(sonado[:1000], audio)
    assert not sonado[1000:].any()
    assert not t.callado()


def test_callar_corta_la_voz_y_cierra_la_boca():
    import numpy as np
    from ai import text_to_speech as mod

    sd = SdFalso()
    t = _tts(mod)
    audio = np.zeros(48000 * 60, dtype=np.float32)  # un minuto de audio

    with mock.patch.object(mod, "sd", sd):
        hilo = threading.Thread(target=t._reproducir_con_control_boca, args=(audio, [(0.0, 60.0)]))
        hilo.start()
        time.sleep(0.15)
        t.callar()
        hilo.join(2)
        assert not hilo.is_alive(), "sigue reproduciendo tras callar"
        for _ in range(40):  # el hilo de la boca acaba por su cuenta
            if mock.call("boca", {"hablado": False}) in t.socketio.emit.call_args_list:
                break
            time.sleep(0.05)
    assert t.callado()
    assert mock.call("boca", {"hablado": False}) in t.socketio.emit.call_args_list


def test_callar_solo_vale_para_el_turno_en_curso():
    from ai import text_to_speech as mod

    t = _tts(mod)
    t.callar()
    assert t.callado()
    t.empezar_turno()
    assert not t.callado()


def test_callar_mientras_piensa_no_genera_audio_ni_empieza_a_hablar():
    from ai import text_to_speech as mod

    t = _tts(mod)
    t._generar_audio_completo = mock.Mock()
    empieza, para = mock.Mock(), mock.Mock()
    t.callar()
    t.hablar("Hola", on_start=empieza, on_stop=para)
    t._generar_audio_completo.assert_not_called()
    empieza.assert_not_called()
    para.assert_called_once()


def test_callar_mientras_genera_el_audio_no_llega_a_hablar(tmp_path):
    import numpy as np
    from ai import text_to_speech as mod

    t = _tts(mod)

    async def genera(_texto, ruta):
        with open(ruta, "wb") as f:
            f.write(b"x")
        t.callar()  # el toque llega justo ahora

    t._generar_audio_completo = genera
    empieza, para = mock.Mock(), mock.Mock()
    sd = SdFalso()
    sf = mock.Mock()
    sf.read.return_value = (np.zeros(48000, dtype=np.float32), 48000)
    with mock.patch.object(mod, "sd", sd), mock.patch.object(mod, "sf", sf):
        t.hablar("Hola", on_start=empieza, on_stop=para)
    empieza.assert_not_called()
    para.assert_called_once()
    assert sd.creados == 0


def test_callar_antes_de_empezar_no_reproduce():
    import numpy as np
    from ai import text_to_speech as mod

    t = _tts(mod)
    t._callado.set()
    sd = SdFalso()
    with mock.patch.object(mod, "sd", sd):
        t._reproducir_con_control_boca(np.zeros(10, dtype=np.float32), [])
    assert sd.creados == 0


# ── Voz por trozos: suena el primero mientras se generan los demás ───────────

def test_juntar_japones_une_solo_los_japoneses_seguidos():
    from ai import text_to_speech as mod
    t = _tts(mod)
    t.voice_es, t.voice_ja = "es", "ja"
    assert t._juntar_japones([("a", "es"), ("を", "ja"), ("ください", "ja"), ("b", "es"), ("うん", "ja")]) == [
        ("a", "es"), ("を、ください", "ja"), ("b", "es"), ("うん", "ja")]


def test_los_trozos_suenan_en_orden_y_la_voz_empieza_con_el_primero():
    import numpy as np
    from ai import text_to_speech as mod

    t = _tts(mod)
    a = np.full(4800, 0.5, dtype=np.float32)
    b = np.full(4800, -0.5, dtype=np.float32)
    cola = __import__("queue").Queue()
    sd = SdFalso()

    def llega_tarde():
        time.sleep(0.05)  # el 2.º trozo aún se está generando: suena silencio y luego sigue
        cola.put(b)
        cola.put(None)

    threading.Thread(target=llega_tarde, daemon=True).start()
    with mock.patch.object(mod, "sd", sd), mock.patch("core.system_settings.volumen_factor", return_value=1.0):
        t._sonar_por_trozos(a, cola)
    sonado = np.concatenate(sd.sonado)[:, 0]
    util = sonado[sonado != 0]
    assert np.array_equal(util, np.concatenate([a, b]))   # ni se pierde ni se repite nada
    assert sd.creados == 1                                  # un solo stream, sin cortes entre trozos


def test_hablar_por_trozos_avisa_al_empezar_y_al_acabar_y_callar_lo_corta():
    import numpy as np
    from ai import text_to_speech as mod

    async def trozos(self, texto, base, como_audio=False, corto=False):
        for i in range(3):
            yield np.full(4800, 0.3, dtype=np.float32)
    llamadas = []
    t = _tts(mod)
    t._generar_trozos = lambda texto, base, **kw: trozos(t, texto, base, **kw)
    sd = SdFalso()
    with mock.patch.object(mod, "sd", sd), mock.patch("core.system_settings.volumen_factor", return_value=1.0):
        t._hablar_por_trozos("hola", on_start=lambda: llamadas.append("start"), on_stop=lambda: llamadas.append("stop"))
    assert llamadas == ["start", "stop"]
    assert np.concatenate(sd.sonado)[:, 0].tolist().count(np.float32(0.3)) == 3 * 4800

    # sin audio (texto sin nada hablable): solo avisa de que ha parado
    async def nada(texto, base, **kw):
        return
        yield
    llamadas.clear()
    t._generar_trozos = nada
    t._hablar_por_trozos("...", on_start=lambda: llamadas.append("start"), on_stop=lambda: llamadas.append("stop"))
    assert llamadas == ["stop"]


def test_texto_y_tarjeta_salen_cuando_empieza_la_voz_no_antes():
    """Si la tarjeta de kana se ve mientras se genera el audio, Kaito parece colgado."""
    from core import listener as mod

    orden = []
    estado = {"v": "idle"}
    state = mock.Mock(get=lambda: estado["v"], cambiar=lambda v: estado.update(v=v))
    profesor = mock.Mock(modo_conv=False, ultima_frase_objetivo=None)
    profesor.esta_activo.return_value = True
    brain = mock.Mock(profesor=profesor, ultimo_turno_ts=0.0, asunto_cerrado=False,
                      _emitir_desactivar_sensei=False)
    brain.responder.return_value = ("【こんにちは】, Laura", False)

    class Tts(TtsFalso):
        def hablar(self, texto, lento_extra=False, on_start=None):
            orden.append("generando audio")
            on_start()
            orden.append("suena")

        def hablar_frases(self, frases, lento_extra=False, on_start=None):
            orden.append("generando audio")
            super().hablar_frases(frases, on_start=lambda: (on_start(), orden.append("suena")))

    socketio = mock.Mock()
    socketio.emit.side_effect = lambda ev, *a, **k: orden.append(ev)
    v = mod.VoiceListener.__new__(mod.VoiceListener)
    v.recorder = mock.Mock(record_vad=lambda timeout_inicio_seg=0: "a.wav")
    v.stt = mock.Mock()
    v.brain, v.tts, v.state, v.socketio = brain, Tts(), state, socketio
    with mock.patch.object(mod, "transcribir_para_turno", return_value=("hola", None)):
        v._ciclo_voz()
    for _ in range(100):  # la voz va en su hilo
        if "suena" in orden:
            break
        time.sleep(0.01)
    assert orden.index("generando audio") < orden.index("mensaje") < orden.index("suena")
    assert orden.index("generando audio") < orden.index("sensei_japones")


def test_voz_parte_los_trozos_largos_en_español_por_frases():
    from ai import text_to_speech as mod
    t = mod.TextToSpeech.__new__(mod.TextToSpeech)
    t.voice_es, t.voice_ja = "es", "ja"
    largo = "Primera frase bastante larga para llenar. " * 2 + "Segunda frase de cierre, que sigue. ¿Y una pregunta más?"
    trozos = t._partir_largos([(largo, "es"), ("ください", "ja")], maximo=110)
    assert all(len(x) <= 110 for x, v in trozos if v == "es") and len(trozos) >= 3
    assert " ".join(x for x, v in trozos if v == "es") == largo.strip()   # no se pierde nada
    assert trozos[-1] == ("ください", "ja")


def test_streaming_del_llm_la_voz_empieza_antes_que_el_final_y_la_tarjeta_espera_al_final():
    from core import listener as mod

    orden = []
    estado = {"v": "idle"}
    state = mock.Mock(get=lambda: estado["v"], cambiar=lambda v: estado.update(v=v))
    profesor = mock.Mock(modo_conv=False, ultima_frase_objetivo=None)
    profesor.esta_activo.return_value = True
    brain = mock.Mock(profesor=profesor, ultimo_turno_ts=0.0, asunto_cerrado=False,
                      _emitir_desactivar_sensei=False)

    def responder(texto, pron_contexto=None, on_frase=None):
        on_frase("【こんにちは】, Laura. Primera frase.", False)
        orden.append("llega la 1ª frase")
        time.sleep(0.15)        # el LLM sigue escribiendo mientras ya suena la primera
        on_frase("Segunda frase, la última.", False)
        orden.append("el LLM acaba")
        return "【こんにちは】, Laura. Primera frase. Segunda frase, la última.", False
    brain.responder.side_effect = responder

    class Tts(TtsFalso):
        def hablar_frases(self, frases, lento_extra=False, on_start=None):
            super().hablar_frases(frases, on_start=lambda: (orden.append("suena"), on_start()))
            orden.append("fin de la voz")
    tts = Tts()
    socketio = mock.Mock()
    socketio.emit.side_effect = lambda ev, *a, **k: orden.append(ev)
    v = mod.VoiceListener.__new__(mod.VoiceListener)
    v.recorder = mock.Mock(record_vad=lambda timeout_inicio_seg=0: "a.wav")
    v.stt = mock.Mock()
    v.brain, v.tts, v.state, v.socketio = brain, tts, state, socketio
    with mock.patch.object(mod, "transcribir_para_turno", return_value=("hola", None)):
        v._ciclo_voz()
    assert orden.index("llega la 1ª frase") < orden.index("suena")
    assert orden.index("el LLM acaba") < orden.index("sensei_japones")   # la tarjeta, con la respuesta entera
    assert orden.index("suena") < orden.index("sensei_japones")         # y nunca antes de que suene
    assert orden.count("sensei_japones") == 1 and orden.count("mensaje") == 1
    assert tts.dichas == ["【こんにちは】, Laura. Primera frase.", "Segunda frase, la última."]


def test_hablar_frases_suena_cada_frase_segun_llega_y_acaba_con_none():
    import numpy as np
    from ai import text_to_speech as mod

    t = _tts(mod)
    sintetizadas = []

    async def trozos(texto, base, **kw):
        sintetizadas.append(texto)
        yield np.full(4800, 0.1 if "uno" in texto else -0.1, dtype=np.float32)
    t._generar_trozos = trozos
    frases = __import__("queue").Queue()
    avisos = []
    sd = SdFalso()

    def llegan():
        frases.put("frase uno")
        time.sleep(0.05)               # el LLM aún escribe la siguiente
        frases.put("frase dos")
        frases.put(None)
    threading.Thread(target=llegan, daemon=True).start()
    with mock.patch.object(mod, "sd", sd), mock.patch("core.system_settings.volumen_factor", return_value=1.0):
        t.hablar_frases(frases, on_start=lambda: avisos.append("start"), on_stop=lambda: avisos.append("stop"))
    sonado = np.concatenate(sd.sonado)[:, 0]
    util = sonado[sonado != 0]
    assert sintetizadas == ["frase uno", "frase dos"] and avisos == ["start", "stop"]
    assert np.array_equal(util, np.concatenate([np.full(4800, 0.1, np.float32), np.full(4800, -0.1, np.float32)]))
    assert sd.creados == 1   # un solo stream para toda la respuesta


def test_primer_trozo_sin_ffmpeg_acortado_y_cache_de_trozos_repetidos(tmp_path):
    import asyncio
    import numpy as np
    from ai import text_to_speech as mod

    t = _tts(mod)
    t.voice_es, t.voice_ja = "es", "ja"
    t._cache_dir = str(tmp_path)

    # 1. ajustar en numpy: silencio inicial + recorte de bordes + pausa, sin ffmpeg
    sr = t.sample_rate_device
    audio = np.concatenate([np.zeros(sr), np.full(sr, 0.5, np.float32), np.zeros(sr)]).astype(np.float32)
    sal = t._ajustar_np(audio, trim_inicio=True, trim_fin=True, pausa=0.3, silencio_inicial=0.15)
    assert sal[: int(0.15 * sr)].max() == 0 and 0.5 in sal           # silencio delante, voz en medio
    esperado = int(0.15 * sr) + sr + 2 * int(0.06 * sr) + int(0.3 * sr)
    assert abs(len(sal) - esperado) <= 2                              # bordes recortados (dejando 0,06 s)
    assert len(t._ajustar_np(audio, trim_inicio=False, trim_fin=False, pausa=0, silencio_inicial=0)) == 3 * sr

    # 2. el primer trozo largo en español se corta en una pausa cercana
    largo = "Bueno, Laura, vamos a ver qué recuerdas de la clase de ayer, cuéntame todo."
    a, b = t._acortar_primero([(largo, "es"), ("ください", "ja")])[:2]
    assert len(a[0]) <= 56 and a[0].endswith(",") and (a[0] + " " + b[0]) == largo
    assert t._acortar_primero([("Corto.", "es")]) == [("Corto.", "es")]

    # 3. caché: la 2.ª vez que sale un trozo no se vuelve a descargar
    descargas = []

    async def fake_generar(txt, voz, ruta):
        descargas.append(txt)
        open(ruta, "wb").write(b"mp3")
    t._generar_audio_segmento = fake_generar
    t._cargar_trozo = lambda ruta: (os.unlink(ruta), np.full(sr, 0.5, np.float32))[1]

    async def una_vez():
        return [x async for x in t._generar_trozos("¡Qué bien, Laura!", str(tmp_path / "t"), como_audio=True)]
    import os
    asyncio.run(una_vez()); asyncio.run(una_vez())
    assert descargas == ["¡Qué bien, Laura!"]                         # la 2.ª salió de la caché
    assert len([f for f in os.listdir(tmp_path) if f.endswith(".mp3")]) == 1


def test_el_saludo_de_entrada_no_suena_hasta_que_acaba_la_animacion():
    """Al entrar en sensei la cara hace una animación de ~2 s: el saludo espera a que acabe."""
    import numpy as np
    from ai import text_to_speech as mod

    async def trozos(texto, base, **kw):
        yield np.full(4800, 0.3, dtype=np.float32)
    t = _tts(mod)
    t._generar_trozos = trozos
    sd = SdFalso()
    arranque = []
    objetivo = time.monotonic() + 0.4
    with mock.patch.object(mod, "sd", sd), mock.patch("core.system_settings.volumen_factor", return_value=1.0):
        t._hablar_por_trozos("hola", on_start=lambda: arranque.append(time.monotonic()), no_antes_de=objetivo)
    assert arranque and arranque[0] >= objetivo          # el audio ya estaba listo, pero espera
    assert not sd.sonado or len(sd.sonado) > 0
    # sin `no_antes_de` arranca sin espera
    arranque.clear()
    t0 = time.monotonic()
    with mock.patch.object(mod, "sd", SdFalso()), mock.patch("core.system_settings.volumen_factor", return_value=1.0):
        t._hablar_por_trozos("hola", on_start=lambda: arranque.append(time.monotonic()))
    assert arranque[0] - t0 < 0.3


def test_listener_pasa_la_espera_de_la_animacion_solo_al_saludo_de_entrada():
    from core import listener as mod

    def turno(estaba_activo, ahora_activo):
        estado = {"v": "idle"}
        state = mock.Mock(get=lambda: estado["v"], cambiar=lambda v: estado.update(v=v))
        profesor = mock.Mock(modo_conv=False, ultima_frase_objetivo=None, entrada_ts=1000.0)
        activo = {"v": estaba_activo}
        profesor.esta_activo.side_effect = lambda: activo["v"]   # cambia al responder, como en la realidad
        brain = mock.Mock(profesor=profesor, ultimo_turno_ts=0.0, asunto_cerrado=False,
                          _emitir_desactivar_sensei=False)
        brain.responder.side_effect = lambda *a, **k: (activo.update(v=ahora_activo), ("Modo Sensei activado!", False))[1]
        recibido = {}

        class Tts(TtsFalso):
            def hablar(self, texto, lento_extra=False, on_start=None, no_antes_de=None):
                recibido["no_antes_de"] = no_antes_de
                on_start()
        v = mod.VoiceListener.__new__(mod.VoiceListener)
        v.recorder = mock.Mock(record_vad=lambda timeout_inicio_seg=0: "a.wav")
        v.stt = mock.Mock()
        v.brain, v.tts, v.state, v.socketio = brain, Tts(), state, mock.Mock()
        with mock.patch.object(mod, "transcribir_para_turno", return_value=("activa el modo sensei", None)):
            v._ciclo_voz()
        time.sleep(0.2)
        return recibido.get("no_antes_de")

    assert turno(False, True) == 1000.0 + mod.SENSEI_ENTRADA_SEG    # acaba de entrar: espera
    assert turno(False, False) is None                              # no entró: sin espera
