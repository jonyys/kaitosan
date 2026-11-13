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
    return vl


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
