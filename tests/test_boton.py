"""El botón de la caja: si el detector tiene el micro, hay que pedirle que lo suelte."""
import importlib
import sys
from unittest import mock

import pytest


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


def _listener(en_pausa):
    from core.listener import VoiceListener
    vl = VoiceListener.__new__(VoiceListener)
    vl._detector = mock.MagicMock()
    vl._detector.en_pausa.return_value = en_pausa
    vl._on_wakeword = mock.MagicMock()
    vl.state = mock.MagicMock()
    vl.state.get.return_value = "idle"
    vl.recorder = mock.MagicMock()
    return vl


def test_segundo_toque_mientras_escucha_cancela_la_grabacion():
    vl = _listener(en_pausa=False)
    vl.state.get.return_value = "listening"
    vl.on_boton()
    vl.recorder.cancelar.set.assert_called_once()
    vl._detector.disparar.assert_not_called()
    vl._on_wakeword.assert_not_called()


def test_cancelar_escucha_sin_escuchar_no_hace_nada():
    vl = _listener(en_pausa=False)
    assert vl.cancelar_escucha() is False
    vl.recorder.cancelar.set.assert_not_called()


def test_boton_con_el_detector_escuchando_le_pide_soltar_el_micro():
    vl = _listener(en_pausa=False)
    vl.on_boton()
    vl._detector.disparar.assert_called_once()
    vl._on_wakeword.assert_not_called()  # grabar ahora mismo fallaría: el micro lo tiene el detector


def test_boton_en_no_molestar_escucha_directamente():
    vl = _listener(en_pausa=True)
    vl.on_boton()
    vl._on_wakeword.assert_called_once()
    vl._detector.disparar.assert_not_called()


def _listener_sensei(sensei, estado="idle", en_pausa=False):
    vl = _listener(en_pausa)
    vl.brain = mock.MagicMock()
    vl.brain.profesor.esta_activo.return_value = sensei
    vl.state = mock.MagicMock()
    vl.state.get.return_value = estado
    vl._ciclo_voz = mock.MagicMock()
    return vl


def test_fuera_de_sensei_el_boton_no_es_de_hablar():
    vl = _listener_sensei(sensei=False)
    assert vl.boton_pulsado() is False
    vl._detector.disparar.assert_not_called()


def test_en_sensei_pulsar_suelta_el_micro_y_marca_pulsar_para_hablar():
    vl = _listener_sensei(sensei=True)
    assert vl.boton_pulsado() is True  # el botón sabe que no debe apagar la Pi
    vl._detector.disparar.assert_called_once_with(vl._turno_mantenido)


def test_en_sensei_con_la_cara_ocupada_no_hay_pulsar_para_hablar():
    vl = _listener_sensei(sensei=True, estado="speaking")
    assert vl.boton_pulsado() is False


def test_mantenido_graba_hasta_soltar():
    vl = _listener_sensei(sensei=True)
    vl.boton_pulsado()
    vl._boton_dur = 2.0
    vl._boton_suelto.set()
    vl._turno_mantenido()
    vl._ciclo_voz.assert_called_once_with(mantenido=vl._boton_suelto)


def test_toque_corto_en_sensei_es_escucha_normal():
    vl = _listener_sensei(sensei=True)
    vl.boton_pulsado()
    vl._boton_dur = 0.1
    vl._boton_suelto.set()
    vl._turno_mantenido()
    vl._on_wakeword.assert_called_once()
    vl._ciclo_voz.assert_not_called()


def test_el_boton_no_apaga_la_pi_si_se_habla():
    import core.button as b
    apagados = []
    with mock.patch.object(b.subprocess, "run", lambda *a, **k: apagados.append(a)):
        pb = b.PowerButton.__new__(b.PowerButton)
        pb._on_short, pb._on_press, pb._on_release = mock.MagicMock(), lambda: True, mock.MagicMock()
        pb._held = pb._hablando = False
        pb._on_pressed()
        pb._on_held()  # tres segundos pulsado en sensei
        assert not apagados and not pb._held
        pb._on_released()
        pb._on_release.assert_called_once()
        pb._on_short.assert_not_called()
        # fuera de sensei, el comportamiento de siempre
        pb._on_press = lambda: False
        pb._on_pressed()
        pb._on_held()
        assert apagados


def test_wakeword_espera_a_que_la_cara_este_lista_antes_de_escuchar():
    import threading, time
    vl = _listener(en_pausa=False)
    vl.socketio = mock.MagicMock()
    # sin pantalla: nadie contesta y no espera más de ~medio segundo
    t0 = time.monotonic()
    vl._esperar_pantalla()
    assert time.monotonic() - t0 < 1.5
    vl.socketio.emit.assert_called_with("despierta", {})
    # con el reloj: contesta «voy» y luego «lista»; hasta entonces no termina
    def pantalla():
        time.sleep(0.1)  # contesta tras el «despierta», no antes
        vl.pantalla_va()
        time.sleep(0.8)
        vl.pantalla_lista()
    threading.Thread(target=pantalla).start()
    t0 = time.monotonic()
    vl._esperar_pantalla()
    assert time.monotonic() - t0 >= 0.7
    assert not vl._despertando
