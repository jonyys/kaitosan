"""Fase 08 — las unidades base traen ejemplo, literal y uso en sus ítems."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sensei.curriculum import CURRICULUM, ITEM_POR_JP

UNIDADES_CON_DETALLE = [
    "saludos_basicos", "particulas_basicas", "desu_masu", "verbos_n5",
    "adjetivos_n5", "conjugacion_adj", "grupos_verbales", "te_forma",
]


def test_unidades_0_a_5_completas():
    # Desde la Fase 02, el vocabulario N5 se reconcilia con la lista oficial y
    # los ítems nuevos entran sin ejemplo/literal (los improvisa el profesor en
    # vivo) y sin uso (lo rellena la Fase 05 solo donde el matiz lo pide).
    # Desde la Fase 03, la gramática también se reconcilia con la lista tanos N5:
    # los puntos nuevos o rescatados de unidades N4/N3 entran solo con jp+meaning
    # y la Fase 05 les genera ejemplo/literal/uso. Aquí se exige el contrato de
    # "los 4 campos" únicamente a los puntos que ya traían contenido (ejemplo no
    # vacío); en cuanto uno lo tiene, literal y uso deben acompañarlo.
    for unit in CURRICULUM:
        if unit["id"] not in UNIDADES_CON_DETALLE:
            continue
        for item in unit["items"]:
            if item["kind"] != "gramatica":
                continue
            if not item.get("ejemplo"):
                continue  # punto reconciliado en Fase 03; lo completa la Fase 05
            for campo in ("ejemplo", "literal", "uso"):
                assert item.get(campo), (unit["id"], item["jp"], campo)


def test_verbs_se_dividen_en_dos_unidades():
    ids = [unit["id"] for unit in CURRICULUM]
    assert "verbos_n5" in ids
    assert "verbos_movimiento_objeto_n5" in ids
    assert ids.index("verbos_movimiento_objeto_n5") == ids.index("verbos_n5") + 1


if __name__ == "__main__":
    test_unidades_0_a_5_completas()
    print("OK")
