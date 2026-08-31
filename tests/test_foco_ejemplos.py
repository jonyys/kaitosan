"""Fase 08 — cada ítem del FOCO llega al prompt con ejemplo, literal y uso."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM, ITEM_POR_JP
from ai.sensei.profesor import _lineas_foco

UNIDADES_CON_DETALLE = [
    "saludos_basicos", "particulas_basicas", "desu_masu", "verbos_n5",
    "adjetivos_n5", "conjugacion_adj", "grupos_verbales", "te_forma",
]


def test_unidades_0_a_5_completas():
    for unit in CURRICULUM:
        if unit["id"] not in UNIDADES_CON_DETALLE:
            continue
        for item in unit["items"]:
            for campo in ("ejemplo", "literal", "uso"):
                assert item.get(campo), (unit["id"], item["jp"], campo)


def test_verbs_se_dividen_en_dos_unidades():
    ids = [unit["id"] for unit in CURRICULUM]
    assert "verbos_n5" in ids
    assert "verbos_movimiento_objeto_n5" in ids
    assert ids.index("verbos_movimiento_objeto_n5") == ids.index("verbos_n5") + 1
    assert next(u for u in CURRICULUM if u["id"] == "grupos_verbales")["prerequisito"] == "verbos_movimiento_objeto_n5"


def test_item_nuevo_llega_con_ejemplo_y_uso():
    lineas = _lineas_foco("〜ている", "acción en progreso",
                          sufijo=" (unidad: Forma て)")
    assert len(lineas) == 3, lineas
    assert lineas[0] == "  - 【〜ている】 acción en progreso (unidad: Forma て)"
    assert "いま ごはんを たべています" in lineas[1]
    assert "(ahora / comida-OBJ / estoy-comiendo)" in lineas[1]
    assert "けっこんしています" in lineas[2]


def test_item_de_repaso_se_enriquece_desde_el_temario():
    # Los repasos vienen de la BD, sin ejemplo ni uso: se buscan por jp.
    item_bd = {"grammar_point": "〜てください", "description": "petición formal"}
    jp = item_bd.get("jp") or item_bd["grammar_point"]
    lineas = _lineas_foco(jp, item_bd["description"])
    assert len(lineas) == 3, lineas
    assert "まって ください" in lineas[1]


def test_item_fuera_del_temario_da_una_sola_linea():
    assert "たぬき" not in ITEM_POR_JP
    assert _lineas_foco("たぬき", "tejón") == ["  - 【たぬき】 tejón"]


if __name__ == "__main__":
    test_unidades_0_a_5_completas()
    test_item_nuevo_llega_con_ejemplo_y_uso()
    test_item_de_repaso_se_enriquece_desde_el_temario()
    test_item_fuera_del_temario_da_una_sola_linea()
    print("OK")
