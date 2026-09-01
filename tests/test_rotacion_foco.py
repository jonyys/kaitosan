"""El FOCO de due items rotaba dentro de la sesión mientras el profesor
orquestaba por cola SRS.

Fase 09 eliminó esa cola: el FOCO se organiza alrededor del can-do activo y ya
no hay `_rotar_due` / `_foco_agotados` / `TURNOS_POR_ITEM_FOCO`. El plan
(`PLAN_CANDO_N5.md` §18) cita este test para reescribirlo en la Fase 18.
"""
import pytest

pytestmark = pytest.mark.skip(
    reason="cola due eliminada en Fase 09; test se reescribe en Fase 18 (PLAN_CANDO_N5.md §18)"
)


def test_rotacion_foco_pendiente_de_reescritura():
    pass
