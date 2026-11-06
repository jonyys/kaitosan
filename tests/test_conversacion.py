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

    def callado(self):
        return self._c


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


def test_callar_corta_la_voz_y_cierra_la_boca():
    import numpy as np
    from ai import text_to_speech as mod

    cortado = threading.Event()
    sd = mock.Mock()
    sd.stop.side_effect = cortado.set
    sd.wait.side_effect = lambda: cortado.wait(5)

    t = mod.TextToSpeech.__new__(mod.TextToSpeech)
    t.device, t.sample_rate_device = None, 48000
    t._callado = threading.Event()
    t.socketio = mock.Mock()
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


def test_callar_antes_de_empezar_no_reproduce():
    import numpy as np
    from ai import text_to_speech as mod

    t = mod.TextToSpeech.__new__(mod.TextToSpeech)
    t.device, t.sample_rate_device = None, 48000
    t._callado = threading.Event()
    t._callado.set()
    sd = mock.Mock()
    with mock.patch.object(mod, "sd", sd):
        t._reproducir_con_control_boca(np.zeros(10, dtype=np.float32), [])
    sd.play.assert_not_called()
