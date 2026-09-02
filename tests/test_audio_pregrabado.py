"""El botón "escuchar" de las fichas sirve un mp3 pregrabado por
scripts/generar_audio.py. La clave del archivo = md5(texto), y el texto lo
eligen DOS sitios que tienen que coincidir:
  - la plantilla: audio_url(it.reading or it.jp)  (it.reading ya viene vacío
    si == jp, ver app.py:_temario_unidades)
  - el script:    rd if rd and rd != jp else jp

Este test bloquea que esas dos reglas se separen, y que la clave del script
sea la misma que la de app.py:_audio_clave (ambas md5 hex de texto.strip()).
`import app` no arranca aquí (deps de la Pi), así que se replica _audio_clave.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM
from ai.sensei.kanji_n5 import KANJI_N5
from scripts.generar_audio import clave, textos


def _audio_clave_app(texto):  # copia 1:1 de app.py:_audio_clave
    return hashlib.md5((texto or "").strip().encode("utf-8")).hexdigest()


def _texto_plantilla_vocab(e):
    """Lo que la plantilla pasaría a audio_url() para un ítem de vocabulario:
    it.reading (vacío si == jp) or it.jp."""
    jp = str(e.get("jp") or "").strip()
    reading = str(e.get("reading") or "").strip()
    it_reading = reading if reading and reading != jp else ""
    return it_reading or jp


def test_clave_coincide_app_y_script():
    for t in list(textos())[:20]:
        assert clave(t) == _audio_clave_app(t)


def test_regla_de_texto_plantilla_vs_script():
    generados = set(textos())
    for u in CURRICULUM:
        for e in u.get("items", []):
            if e.get("kind") != "vocabulario" or e.get("tipo") == "kanji":
                continue
            if not str(e.get("jp") or "").strip():
                continue
            # el texto que elegiría la plantilla tiene que ser uno de los que
            # el script pregraba
            assert _texto_plantilla_vocab(e) in generados


def test_kanji_reading_card_cubierto():
    generados = set(textos())
    for k in KANJI_N5:
        t = str(k.get("reading_card") or k.get("reading") or "").strip()
        if t:
            assert t in generados


def test_sin_textos_vacios_ni_duplicados():
    ts = list(textos())
    assert all(t and t.strip() for t in ts)
    assert len(ts) == len(set(ts))
