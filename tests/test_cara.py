"""La cara: lo que el motor de animación da por hecho en el marcado."""
import re
from pathlib import Path

CARA = Path("templates/partials/face/_cara.html").read_text(encoding="utf-8")
MOTOR = Path("templates/partials/face/_scripts.html").read_text(encoding="utf-8")


def test_cada_ojo_tiene_las_piezas_que_anima_el_motor():
    assert len(re.findall(r'class="eye[ "]', CARA)) == 4
    for pieza in ('class="iris"', 'class="pupila"', 'class="parpado-sup"', 'class="parpado-inf"', "data-recorrido="):
        assert CARA.count(pieza) == 4, pieza


def test_las_formas_de_cada_boca_se_pueden_mezclar():
    # Se interpolan número a número: si difieren en cantidad, la boca se rompe.
    formas = re.findall(r'(cerrada|abierta): "([^"]+)"', MOTOR)
    assert len(formas) == 4
    for (_, cerrada), (_, abierta) in zip(formas[0::2], formas[1::2]):
        assert re.sub(r"-?[\d.]+", "#", cerrada) == re.sub(r"-?[\d.]+", "#", abierta)


def test_las_formas_de_los_gestos_se_pueden_mezclar_con_la_boca():
    # Los gestos suman sonrisa, O y boquita sobre la boca cerrada número a número.
    cerrada = re.search(r'cerrada: "([^"]+)"', MOTOR).group(1)
    bloque = re.search(r"FORMAS_BOCA = \{(.*?)\};", MOTOR, re.S).group(1)
    formas = re.findall(r'(\w+): "([^"]+)"', bloque)
    assert {n for n, _ in formas} == {"sonrisa", "o", "mini", "triste"}
    for nombre, d in formas:
        assert re.sub(r"-?[\d.]+", "#", d) == re.sub(r"-?[\d.]+", "#", cerrada), nombre


def test_la_cremallera_tiene_dibujo_y_no_sale_sola():
    assert 'class="cremallera"' in CARA
    assert re.search(r"cremallera: \{ dur: \d+, peso: 0,", MOTOR)
    assert 'hacerGesto("cremallera")' in MOTOR


def test_cada_ojo_tiene_pupila_de_corazon():
    assert CARA.count('class="pupila-corazon"') == 4


def test_cada_ojo_tiene_sus_brillitos():
    # Dos por ojo (uno grande y uno chiquito), dentro del iris para que sigan la mirada
    assert CARA.count('class="brillo-ojo"') == 4
    assert CARA.count('class="brillo-ojo brillo-ojo-2"') == 4
