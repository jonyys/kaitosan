"""Alarmas con días de la semana: cuándo es la próxima vez que suenan."""
import sys
import types
from datetime import datetime

sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))  # el audio no hace falta aquí

from ai.skills.alarm import AlarmSkill, segundos_hasta, texto_dias

LUNES_10H = datetime(2026, 11, 9, 10, 0, 0)  # 2026-11-09 es lunes


def horas(h, m, dias=None):
    return segundos_hasta(h, m, dias, LUNES_10H) / 3600


def test_sin_dias_es_la_proxima_vez_que_dan_esa_hora():
    assert horas(11, 0) == 1
    assert horas(9, 0) == 23


def test_con_dias_espera_al_primero_que_toque():
    assert horas(11, 0, [2]) == 49           # el miércoles
    assert horas(9, 0, [0]) == 7 * 24 - 1    # hoy ya pasó: el lunes que viene
    assert horas(11, 0, [0, 1]) == 1         # hoy mismo


def test_texto_de_los_dias():
    assert texto_dias([]) == ""
    assert texto_dias([0, 1, 2, 3, 4]) == "de lunes a viernes"
    assert texto_dias(list(range(7))) == "todos los días"
    assert texto_dias([0, 2]) == "lunes, miércoles"


def test_el_interruptor_apaga_y_enciende_sin_borrar():
    skill = AlarmSkill()
    skill.poner_alarma("07:00", dias=[0])
    alarma = skill.alarmas[0]
    skill.activar_alarma(alarma["id"], False)
    alarma["timer"].join(1)  # cancelar avisa al hilo, que tarda un instante en salir
    assert alarma["activa"] is False and not alarma["timer"].is_alive()
    skill.activar_alarma(alarma["id"], True)
    assert alarma["activa"] is True and alarma["timer"].is_alive()
    alarma["timer"].cancel()


def test_temporizador_pausa_reanuda_y_se_detiene():
    skill = AlarmSkill()
    skill.poner_temporizador(0, 10)
    t = skill.temporizadores[0]
    skill.estado_temporizador(t["id"], "pausar")
    assert t["pausado"] and 9 < t["restante"] <= 10
    skill.estado_temporizador(t["id"], "reanudar")
    assert not t["pausado"] and t["timer"].is_alive()
    skill.estado_temporizador(t["id"], "detener")
    assert t["pausado"] and t["restante"] == 10  # parado y con la duración entera
    t["timer"].cancel()
