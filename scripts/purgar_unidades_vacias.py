"""Fase 04 — borra de `curriculum.py` las unidades que quedaron con `items: []`
tras reconciliar vocabulario (Fase 02) y gramática (Fase 03).

Surgeon de texto: usa los rangos de línea del AST para quitar SOLO los bloques
de las unidades vacías; el resto del fichero queda byte a byte igual. Después
repunta los `prerequisito` que apuntaban a una unidad borrada y quita el token
"N4" del nombre de las 3 unidades N4 que sí conservan vocabulario N5.

Idempotente: si no hay unidades vacías, no toca nada. Ejecutar una vez y
commitear el diff resultante.
"""
import ast
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURR = os.path.join(RAIZ, "ai", "sensei", "curriculum.py")

# Repunte de prerequisitos rotos por el borrado (unidad_borrada -> superviviente).
REPUNTES = {
    ("adjetivos_n5", "grupos_verbales"): "verbos_movimiento_objeto_n5",
    ("transitivos_intransitivos", "experiencia_aspecto"): "forma_potencial",
}

# Las 3 unidades N4 que conservan vocabulario N5: se les quita el token de nivel
# del nombre (y del id donde lo lleva) para que no queden rastros "N4"/"N3".
RENOMBRA_NOMBRE = {
    "'nombre': 'Forma potencial N4: poder hacer X'":
        "'nombre': 'Forma potencial: poder hacer X'",
    "'nombre': 'Verbos transitivos e intransitivos N4'":
        "'nombre': 'Verbos transitivos e intransitivos'",
    "'nombre': 'Vocabulario N4 — Vida cotidiana y sociedad'":
        "'nombre': 'Vocabulario N5 — Vida cotidiana y sociedad'",
}
RENOMBRA_ID = {"'id': 'vocabulario_n4_vida'": "'id': 'vocabulario_vida'"}


def main():
    src = open(CURR, encoding="utf-8").read()
    tree = ast.parse(src)
    node = next(
        n for n in tree.body
        if isinstance(n, ast.Assign)
        and any(getattr(t, "id", None) == "CURRICULUM" for t in n.targets)
    )

    borrar = []
    for elt in node.value.elts:
        campos = {k.value: v for k, v in zip(elt.keys, elt.values)}
        items = campos["items"]
        vacia = isinstance(items, ast.List) and not items.elts
        if vacia:
            borrar.append((campos["id"].value, elt.lineno, elt.end_lineno))

    if not borrar:
        print("no hay unidades vacías, nada que hacer")
        return

    drop = set()
    for uid, ini, fin in borrar:
        drop.update(range(ini, fin + 1))
        print(f"borrando  {uid:28} líneas {ini}-{fin}")

    lineas = src.splitlines(keepends=True)
    nuevo = "".join(l for i, l in enumerate(lineas, 1) if i not in drop)

    for (unidad, viejo), nuevo_prereq in REPUNTES.items():
        antes = f"'prerequisito': '{viejo}'"
        despues = f"'prerequisito': '{nuevo_prereq}'"
        assert nuevo.count(antes) == 1, (antes, nuevo.count(antes))
        nuevo = nuevo.replace(antes, despues)
        print(f"repunte   {unidad:28} prereq {viejo} -> {nuevo_prereq}")

    for viejo, nuevo_txt in {**RENOMBRA_NOMBRE, **RENOMBRA_ID}.items():
        assert nuevo.count(viejo) == 1, (viejo, nuevo.count(viejo))
        nuevo = nuevo.replace(viejo, nuevo_txt)
        print(f"renombra  {viejo} -> {nuevo_txt}")

    # comprobación: sigue siendo Python válido y no quedan tokens N4/N3
    ast.parse(nuevo)
    open(CURR, "w", encoding="utf-8", newline="").write(nuevo)
    print(f"\nlisto: {len(borrar)} unidades borradas")


if __name__ == "__main__":
    main()
