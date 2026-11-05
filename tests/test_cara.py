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
