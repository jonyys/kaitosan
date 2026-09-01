#!/usr/bin/env python
"""Fase 03 del plan can-do N5 — reconcilia la gramática de `ai/sensei/curriculum.py`
con la lista oficial `data/n5_grammar.csv` (tanos N5, 90 puntos).

Uso: `python scripts/reconciliar_gram.py [--check]`

Sin flags: reescribe el literal `CURRICULUM = [...]` de `ai/sensei/curriculum.py`
de forma determinista:

  1. CONSERVA con su contenido intacto (meaning/ejemplo/literal/uso carácter a
     carácter) los puntos de gramática cuyo `jp` esté en `data/n5_grammar.csv`,
     ya sea EXACTAMENTE o por FORMA CANÓNICA (mapa `CANON`: mismo punto escrito
     distinto — llano vs. cortés, etiqueta entre paréntesis, sufijo か). En los
     casos de forma canónica el `jp` adopta la grafía del CSV; el resto de
     campos no se toca.
  2. QUITA de sus unidades los puntos de gramática que no estén en la lista
     (sobre todo N4/N3, más planos/variantes que tanos no lista: この〜, contadores,
     grupos verbales, 〜かった…). No se tocan las unidades como unidades — eso es
     la Fase 04 —; solo se les quita el ítem de gramática.
  3. AÑADE los puntos N5 que faltan, con `jp` + `meaning` (español); deja
     `ejemplo` / `literal` / `uso` vacíos: los rellena la Fase 05.
  4. Cada punto (conservado, movido o nuevo) se coloca en la unidad de
     `ASIGNACION`. Los puntos N5 que hoy viven en unidades N4/N3 se mueven a
     una unidad N5 para que sobrevivan al borrado de la Fase 04.
  5. En cada unidad, los ítems que no son de gramática se quedan donde están; el
     bloque de gramática (en orden del CSV) se inserta en la posición del primer
     ítem de gramática original de esa unidad, o al final si no tenía ninguno.

Con `--check`: no escribe; sale != 0 si el resultado no cumpliría el invariante
(`set(jp de gramática) == set(jp del CSV)` y sin duplicados).

El literal se extrae y se reescribe con el mismo serializador determinista que
usó la Fase 02 (`reconciliar_vocab.extraer_literal_curriculum` / `formatear`),
de modo que el diff toca solo la gramática y el bloque de vocabulario sale byte
a byte igual.
"""
import sys
from pathlib import Path

# La consola de Windows por defecto (cp1252) revienta al imprimir japonés.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconciliar_vocab import extraer_literal_curriculum, formatear  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CURRICULUM_PY = RAIZ / "ai" / "sensei" / "curriculum.py"
CSV_GRAM = RAIZ / "data" / "n5_grammar.csv"

# --- Unidad destino de cada punto de gramática N5 (en orden del CSV) ----------
# Todas las unidades destino son N5, así ningún punto se pierde cuando la Fase 04
# borre las unidades N4/N3.
ASIGNACION = {
    "は": "particulas_basicas",
    "が": "particulas_basicas",
    "を": "particulas_basicas",
    "に": "particulas_basicas",
    "で": "particulas_basicas",
    "と": "particulas_basicas",
    "も": "particulas_basicas",
    "の": "particulas_basicas",
    "から": "particulas_basicas",
    "まで": "particulas_basicas",
    "や": "particulas_basicas",
    "へ": "particulas_basicas",
    "か": "particulas_basicas",
    "ね": "particulas_basicas",
    "よ": "particulas_basicas",
    "です": "desu_masu",
    "ではありません": "desu_masu",
    "じゃありません": "desu_masu",
    "でした": "desu_masu",
    "ではありませんでした": "desu_masu",
    "〜ます": "desu_masu",
    "〜ません": "desu_masu",
    "〜ました": "desu_masu",
    "〜ませんでした": "desu_masu",
    "〜ましょう": "desu_masu",
    "〜ましょうか": "desu_masu",
    "〜て（て形）": "te_forma",
    "〜てください": "te_forma",
    "〜てもいいです": "te_forma",
    "〜てはいけません": "te_forma",
    "〜ています": "te_forma",
    "〜てから": "te_forma",
    "〜てみます": "te_forma",
    "〜ておきます": "te_forma",
    "〜てしまいます": "te_forma",
    "〜てあげます": "te_forma",
    "〜てくれます": "te_forma",
    "〜てもらいます": "te_forma",
    "〜ないでください": "permiso_obligacion",
    "〜なくてもいいです": "permiso_obligacion",
    "〜なければなりません": "permiso_obligacion",
    "〜なくてはいけません": "permiso_obligacion",
    "〜ないほうがいいです": "permiso_obligacion",
    "〜たいです": "negacion_condicional",
    "〜たくないです": "negacion_condicional",
    "〜たがっています": "negacion_condicional",
    "〜つもりです": "comparaciones_deseos",
    "〜たことがあります": "negacion_condicional",
    "〜たり〜たりします": "negacion_condicional",
    "〜たあとで": "negacion_condicional",
    "〜たほうがいいです": "negacion_condicional",
    "〜まえに": "negacion_condicional",
    "〜ながら": "negacion_condicional",
    "〜ことができます": "negacion_condicional",
    "〜ことがあります": "negacion_condicional",
    "〜でしょう": "comparaciones_deseos",
    "〜かもしれません": "comparaciones_deseos",
    "〜と思います": "negacion_condicional",
    "〜そうです": "comparaciones_deseos",
    "〜んです": "cuerpo_salud",
    "という": "particulas_basicas",
    "〜すぎます": "comparaciones_deseos",
    "〜やすいです": "conjugacion_adj",
    "〜にくいです": "conjugacion_adj",
    "〜より": "comparaciones_deseos",
    "〜のほうが": "comparaciones_deseos",
    "〜ほど〜ない": "comparaciones_deseos",
    "〜くなります": "conjugacion_adj",
    "〜になります": "conjugacion_adj",
    "〜くします": "conjugacion_adj",
    "〜にします": "conjugacion_adj",
    "〜くて": "conjugacion_adj",
    "〜で（な形容詞）": "conjugacion_adj",
    "〜ば": "negacion_condicional",
    "〜たら": "negacion_condicional",
    "と（条件）": "negacion_condicional",
    "〜なら": "negacion_condicional",
    "〜が好きです": "comparaciones_deseos",
    "〜が嫌いです": "comparaciones_deseos",
    "〜がほしいです": "comparaciones_deseos",
    "〜が上手です": "comparaciones_deseos",
    "〜が下手です": "comparaciones_deseos",
    "〜がわかります": "comparaciones_deseos",
    "あげます": "te_forma",
    "もらいます": "te_forma",
    "くれます": "te_forma",
    "〜から（理由）": "negacion_condicional",
    "〜ので": "negacion_condicional",
    "疑問詞+か": "demostrativos",
    "疑問詞+も": "demostrativos",
}

# --- Forma canónica: jp actual en CURRICULUM -> jp del CSV (mismo punto) -------
# Solo casos inequívocos: mismo patrón gramatical, grafía distinta (llano vs.
# cortés, etiqueta entre paréntesis, sufijo か). El ítem conserva su contenido;
# solo cambia el `jp` a la grafía del CSV.
CANON = {
    "〜て": "〜て（て形）",
    "〜ている": "〜ています",
    "〜てもいいですか": "〜てもいいです",   # aparece 2x (te_forma / permiso): gana la 1ª
    "〜と思う": "〜と思います",
    "〜から": "〜から（理由）",            # el 〜から de negacion_condicional = motivo
    "〜ほしい": "〜がほしいです",
    "〜すぎる": "〜すぎます",
    "〜ことができる": "〜ことができます",
    "〜つもり": "〜つもりです",
    "〜まで": "まで",
    "〜と (condicional)": "と（条件）",
    "〜たことがある": "〜たことがあります",
    "〜てしまう": "〜てしまいます",
    "〜ておく": "〜ておきます",
    "〜そう": "〜そうです",
    "〜てもらう": "〜てもらいます",
    "〜てあげる": "〜てあげます",
    "〜てくれる": "〜てくれます",
}

# --- `meaning` en español para los puntos que se AÑADEN sin contenido previo ---
# Fase 05 lo afinará; aquí basta con algo usable. Los puntos conservados o
# movidos mantienen su `meaning` original intacto.
MEANINGS_NUEVOS = {
    "から": "partícula: desde / a partir de (lugar, tiempo o motivo)",
    "まで": "partícula: hasta (límite de lugar, tiempo o cantidad)",
    "や": "partícula 'y' para listas no exhaustivas: A や B (entre otras cosas)",
    "へ": "partícula de dirección: hacia ~ (se pronuncia 'e')",
    "じゃありません": "cópula negativa hablada: 'no es / no son' (más natural que ではありません)",
    "ではありませんでした": "cópula formal negativa en pasado: 'no era / no fueron'",
    "〜ましょうか": "ofrecimiento o propuesta: '¿hacemos ~?' / '¿te ayudo con ~?'",
    "〜て（て形）": "forma-て del verbo: conecta acciones y sirve de base para peticiones, permisos, etc.",
    "〜てもいいです": "permiso: 'puedes hacer ~ / está bien si haces ~'",
    "〜ています": "acción en curso o estado resultante: 'está haciendo ~' / 'está hecho'",
    "〜てみます": "probar a hacer ~: intentarlo a ver qué tal",
    "〜ておきます": "hacer ~ de antemano / dejarlo preparado para luego",
    "〜てしまいます": "terminar ~ del todo, o hacerlo sin querer y lamentarlo",
    "〜てあげます": "dar un favor: hacer ~ por otra persona",
    "〜てくれます": "recibir un favor: alguien hace ~ por mí (o por los míos)",
    "〜てもらいます": "pedir/recibir un favor: conseguir que alguien haga ~ por mí",
    "〜なくてはいけません": "obligación: hay que hacer ~ (variante de 〜なければなりません)",
    "〜ないほうがいいです": "consejo negativo: es mejor no hacer ~",
    "〜たくないです": "deseo negativo: no quiero hacer ~",
    "〜たがっています": "deseo de un tercero: se le nota que quiere hacer ~ (no se usa たい para otros)",
    "〜つもりです": "intención: tengo pensado / planeo hacer ~",
    "〜たことがあります": "experiencia: he hecho ~ alguna vez",
    "〜たり〜たりします": "enumeración parcial de acciones: hacer cosas como ~ y ~ (entre otras)",
    "〜たあとで": "secuencia: después de hacer ~",
    "〜たほうがいいです": "consejo: es mejor hacer ~",
    "〜まえに": "secuencia: antes de hacer ~",
    "〜ことができます": "capacidad: poder hacer ~ / saber hacer ~",
    "〜ことがあります": "frecuencia baja: a veces pasa que ~",
    "〜と思います": "opinión: creo que ~",
    "〜そうです": "apariencia: parece que ~ (por lo que se ve)",
    "という": "cita o definición: 'que se llama ~' / 'que dice que ~'",
    "〜すぎます": "exceso: hacer o ser ~ demasiado",
    "〜やすいです": "facilidad: fácil de hacer ~",
    "〜にくいです": "dificultad: difícil de hacer ~",
    "〜ほど〜ない": "comparación negativa: no es tan ~ como (otra cosa)",
    "〜くなります": "cambio de estado con adjetivo-い: volverse / ponerse ~",
    "〜になります": "cambio de estado con adjetivo-な o sustantivo: volverse / convertirse en ~",
    "〜くします": "provocar un cambio con adjetivo-い: hacer que algo quede ~",
    "〜にします": "provocar un cambio o elegir: hacer que algo sea ~ / decidirse por ~",
    "〜くて": "forma-て del adjetivo-い: enlaza cualidades o da un motivo",
    "〜で（な形容詞）": "forma-て del adjetivo-な (y de sustantivos): enlaza o da un motivo",
    "と（条件）": "condicional de consecuencia natural: 'si ~, (siempre) pasa ~'",
    "〜が好きです": "gusto: 'me gusta ~' (con が, no を)",
    "〜が嫌いです": "disgusto: 'no me gusta ~ / me disgusta ~'",
    "〜がほしいです": "deseo de un objeto: 'quiero (algo)' (no es un verbo)",
    "〜が上手です": "habilidad: 'se me da bien ~'",
    "〜が下手です": "habilidad: 'se me da mal ~'",
    "〜がわかります": "comprensión: 'entiendo ~' (con が)",
    "あげます": "dar algo a alguien (fuera del propio grupo, o de igual a igual)",
    "もらいます": "recibir algo de alguien",
    "くれます": "alguien me da algo a mí (o a mi grupo)",
    "〜から（理由）": "motivo: 'porque ~' (más directo y subjetivo que 〜ので)",
    "疑問詞+か": "interrogativo + か: algo / alguien / en algún sitio (indefinido afirmativo)",
    "疑問詞+も": "interrogativo + も + verbo negativo: nada / nadie / en ningún sitio",
}


def cargar_csv():
    """Lista de (jp, meaning) del CSV, en orden. `meaning` puede llevar comas
    (el CSV de la Fase 01 no las entrecomilla), así que se parte por la primera."""
    filas = []
    for linea in CSV_GRAM.read_text(encoding="utf-8").splitlines()[1:]:
        if not linea.strip():
            continue
        jp, meaning = linea.split(",", 1)
        filas.append((jp, meaning))
    return filas


def reconciliar(units, csv_filas):
    csv_orden = [jp for jp, _ in csv_filas]
    csv_set = set(csv_orden)

    # Pool de puntos de gramática ya existentes que se conservan (exacto o por
    # forma canónica). Si un jp/forma aparece 2x (bug preexistente), gana el 1º.
    pool = {}                 # csv_jp -> item conservado
    preservados_ids = set()   # id() de los dicts originales que se conservan (tal cual o renombrados)
    canon_renombrados = []    # (jp_viejo, csv_jp) para el informe
    for u in units:
        for it in u["items"]:
            if it["kind"] != "gramatica":
                continue
            if it["jp"] in csv_set:
                key = it["jp"]
            elif CANON.get(it["jp"]) in csv_set:
                key = CANON[it["jp"]]
            else:
                continue
            if key in pool:
                continue
            preservados_ids.add(id(it))          # el dict original ya no "se elimina"
            if key != it["jp"]:
                canon_renombrados.append((it["jp"], key))
                it = {**it, "jp": key}            # adopta la grafía del CSV
            pool[key] = it

    # Ítem final para cada jp del CSV: el conservado, o uno nuevo esqueleto.
    final_por_jp = {}
    conservados, nuevos = [], []
    for jp in csv_orden:
        if jp in pool:
            final_por_jp[jp] = pool[jp]
            conservados.append(jp)
        else:
            final_por_jp[jp] = {
                "kind": "gramatica",
                "jp": jp,
                "meaning": MEANINGS_NUEVOS[jp],
                "ejemplo": "",
                "literal": "",
                "uso": "",
            }
            nuevos.append(jp)

    # Puntos de gramática que se van (no se han conservado).
    eliminados = []
    for u in units:
        for it in u["items"]:
            if it["kind"] == "gramatica" and id(it) not in preservados_ids:
                eliminados.append((u["id"], it["jp"]))

    # Bloque de gramática por unidad, en orden del CSV.
    gram_por_unidad = {}
    for jp in csv_orden:
        gram_por_unidad.setdefault(ASIGNACION[jp], []).append(final_por_jp[jp])

    ids_validos = {u["id"] for u in units}
    faltan = sorted(set(ASIGNACION.values()) - ids_validos)
    if faltan:
        raise SystemExit(f"ASIGNACION apunta a unidades inexistentes: {faltan}")

    # Puntos N5 que hoy viven en unidades N4/N3 y se rescatan a una unidad N5.
    # 'forma_potencial' es la primera unidad N4 del literal (la inyección de
    # kanji y el borrado de la Fase 04 arrancan ahí).
    ids_lista = [u["id"] for u in units]
    corte_n4 = ids_lista.index("forma_potencial") if "forma_potencial" in ids_lista else len(ids_lista)
    n5_ids = set(ids_lista[:corte_n4])
    movidos = []
    for jp in csv_orden:
        for u in units:
            if any(it["kind"] == "gramatica" and (it["jp"] == jp or CANON.get(it["jp"]) == jp)
                   for it in u["items"]):
                if u["id"] not in n5_ids and ASIGNACION[jp] in n5_ids:
                    movidos.append((u["id"], ASIGNACION[jp], jp))
                break

    # Reconstruir items de cada unidad: lo no-gramática se queda en su sitio;
    # el bloque de gramática entra donde estaba el primer punto original.
    for u in units:
        nuevo_items = []
        bloque = gram_por_unidad.get(u["id"], [])
        insertado = False
        for it in u["items"]:
            if it["kind"] == "gramatica":
                if not insertado:
                    nuevo_items.extend(bloque)
                    insertado = True
                # los puntos de gramática viejos no se copian
            else:
                nuevo_items.append(it)
        if not insertado:
            nuevo_items.extend(bloque)
        u["items"] = nuevo_items

    return conservados, nuevos, eliminados, canon_renombrados, movidos


def verificar(units, csv_filas):
    csv_set = {jp for jp, _ in csv_filas}
    gram = [it["jp"] for u in units for it in u["items"] if it["kind"] == "gramatica"]
    problemas = []
    if set(gram) != csv_set:
        sobra = sorted(set(gram) - csv_set)
        falta = sorted(csv_set - set(gram))
        problemas.append(f"set(jp) != CSV. sobra={sobra} falta={falta}")
    dups = sorted({jp for jp in gram if gram.count(jp) > 1})
    if dups:
        problemas.append(f"gramática duplicada: {dups}")
    return problemas


def main():
    check = "--check" in sys.argv[1:]
    src = CURRICULUM_PY.read_text(encoding="utf-8")
    ini, fin, units = extraer_literal_curriculum(src)
    csv_filas = cargar_csv()

    conservados, nuevos, eliminados, canon, movidos = reconciliar(units, csv_filas)
    problemas = verificar(units, csv_filas)

    print(f"CSV: {len(csv_filas)} puntos de gramática N5")
    print(f"conservados con contenido intacto: {len(conservados)} "
          f"({len(conservados) - len(canon)} exactos + {len(canon)} por forma canónica)")
    for viejo, nuevo in canon:
        print(f"  · {viejo}  ->  {nuevo}")
    print(f"añadidos (jp+meaning, resto vacío para Fase 05): {len(nuevos)}")
    print(f"eliminados de sus unidades (no están en la lista): {len(eliminados)}")
    por_unidad = {}
    for uid, jp in eliminados:
        por_unidad[uid] = por_unidad.get(uid, 0) + 1
    for uid, n in sorted(por_unidad.items()):
        print(f"  - {uid}: {n}")
    print(f"puntos N5 movidos de una unidad N4/N3 a una N5: {len(movidos)}")
    for origen, destino, jp in movidos:
        print(f"  · {jp}: {origen} -> {destino}")

    if problemas:
        for p in problemas:
            print(f"ERROR: {p}")
        return 1

    if check:
        print("\nOK (--check): el resultado cumpliría el invariante. No se ha escrito nada.")
        return 0

    nuevo_src = src[:ini] + formatear(units, 0) + src[fin:]
    if nuevo_src == src:
        print("\nSin cambios: curriculum.py ya está reconciliado.")
        return 0
    CURRICULUM_PY.write_text(nuevo_src, encoding="utf-8")
    print(f"\nOK: {CURRICULUM_PY} reescrito.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
