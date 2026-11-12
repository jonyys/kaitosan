"""Comprobaciones deterministas del sensei: ¿ha usado Laura lo de este can-do?
¿hay errores de conjugación? Y el texto de las fases. Sin LLM; lo usa
ai/sensei/profesor.py.
"""

import os
import re

from ai.sensei.conjugar import analizar
from ai.sensei.curriculum import ITEM_POR_JP

ACIERTOS_PRACTICA = 2
ACIERTOS_TAREA = 2
ACIERTOS_ANTIGUO = 1  # repaso de algo ya dominado: basta con ver que lo recuerda
LIBRE_TURNOS_TEMA = 3  # en charla libre, cada 3 turnos se guía hacia un can-do ya trabajado
NUEVOS_POR_ANTIGUO = 4 # 1 repaso de lo antiguo por cada 4 objetivos nuevos (~20 %)
FALLOS_MAX = 5  # intentos seguidos sin acierto → modelo de respuesta y a lo siguiente
_RE_JP_CHAR = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")


def _formas(cd):
    """Cómo puede sonar cada ingrediente del can-do en lo que dice Laura: el jp
    sin 〜 ni glosas entre paréntesis, partido por ';', y su lectura en kana."""
    out = set()
    for jp in cd.get("items", []):
        it = ITEM_POR_JP.get(jp, {})
        for s in [jp, it.get("reading") or ""]:
            s = re.sub(r"[（(].*?[)）]", "", s).replace("〜", "").replace("～", "")
            out |= {x.strip() for x in s.split(";") if len(x.strip()) >= 2}
    # 'claves': lo que hay que oír cuando la unidad no trae el ingrediente como
    # ítem (いただきます, いくら, うん…): ver candos_clase.json.
    return out | set(cd.get("claves", []))


_PROMPT_JUEZ = (
    "Clase de japonés N5 para una estudiante española hablando con su profesor.\n"
    "Objetivo: {texto}\nLo que se enseña: {explicacion}\n{tarea}\n{contexto}\n"
    "Laura ha dicho (viene de reconocimiento de voz: puede tener fallos de transcripción): «{msg}»\n\n"
    "¿Lo que dice demuestra que hace lo que pide el objetivo? Cumple si es una frase en japonés que "
    "{criterio} NO cumple si solo menciona una "
    "palabra del tema, habla de otra cosa o no hace lo que pide el objetivo. NO cumple tampoco si "
    "falla justo en lo que se enseña (la partícula, forma o expresión clave del objetivo). Fuera de "
    "eso, no exijas perfección gramatical ni un vocabulario concreto.{romaji} Responde solo JSON: {{\"cumple\": true}} o {{\"cumple\": false}}."
)
# Logs de la Pi (12-nov): «ohayō por la mañana, konbanwa por la noche…» → Whisper lo tomó
# por español y escribió «Ohio por la mañana, con Bangwa por la noche…». Era correcto.
_NOTA_ROMAJI = (
    "\nOJO: el reconocimiento lo ha tomado por español, así que las palabras japonesas llegan "
    "escritas como si fueran españolas (p. ej. «Ohio» u «o fallo» = おはよう, «con Bangwa» = "
    "こんばんは, «Yasumi» = おやすみ, «con un chihuahua» = こんにちは). Si se reconocen en ella las "
    "palabras japonesas que pide el objetivo, cumple aunque el resto esté en español.")
_juez_prov = None
_VEREDICTO = {"type": "json_schema", "json_schema": {"name": "veredicto", "strict": True, "schema": {
    "type": "object", "properties": {"cumple": {"type": "boolean"}},
    "required": ["cumple"], "additionalProperties": False}}}


def _contexto_juez(kaito):
    """Lo último que dijo Kaito: la situación a la que responde Laura. Logs (12-nov): sin
    ella, «おはようございます、こんばんは、おやすみなさい» no cumplía (3/3) porque el juez no
    sabía que en la situación Kaito «se va a dormir»; y Kaito suele inventar la situación."""
    if not kaito:
        return ""
    kaito = kaito.strip()[-500:]  # la pregunta va al final
    return (f"Lo que acaba de decirle Kaito (la situación o pregunta a la que responde, manda "
            f"sobre la tarea de arriba): «{kaito}»\n")


def juez_cumple(cd, mensaje, fase="tarea", romaji=False, contexto=None):
    """¿Cumple el mensaje lo que pide el objetivo? Un modelo pequeño responde sí/no
    (~1 s). Medido sobre 387 frases: 4 falsos negativos y 15 falsos positivos, frente
    a 75 y 122 con palabras clave. None si no hay clave o falla → vale la comprobación
    por palabras. JUEZ_MODELO (.env) cambia el modelo; JUEZ_MODELO=off lo apaga.
    `contexto`: lo último que dijo Kaito. 12-nov, 17 casos ×3 con situación de Kaito:
    haiku-5.5 50/51, gpt-6-luna 47, gemini-3.1-flash-lite 45 (rechazaba siempre
    «おはようございます、こんばんは、おやすみなさい»), deepseek-v4.1-flash 44."""
    global _juez_prov
    modelo = os.getenv("JUEZ_MODELO", "anthropic/claude-haiku-5.5")
    if modelo.lower() == "off" or not os.getenv("OPENROUTER_API_KEY"):
        return None
    try:
        if _juez_prov is None:
            from ai.openrouter_provider import OpenRouterProvider
            _juez_prov = OpenRouterProvider(modelos=[modelo])
        if fase == "tarea":
            # Solo lo que tiene que hacer: en los repasos la situación la inventa Kaito.
            tarea = "Laura tiene que: " + que_hacer(cd)
            criterio = "hace claramente lo que pide la tarea o usa lo que se enseña."
        else:  # práctica: basta con usar lo que se enseña en una frase suya
            tarea, criterio = "", "usa lo que se enseña en una frase suya, por sencilla que sea."
        p = _PROMPT_JUEZ.format(texto=cd["texto"], explicacion=cd.get("explicacion", ""),
                                tarea=tarea, criterio=criterio, msg=mensaje,
                                romaji=_NOTA_ROMAJI if romaji else "",
                                # Solo en tareas: en la práctica basta con usar lo que se enseña
                                # (con la frase de Kaito el juez se volvía estricto: 17:02 y 17:03).
                                contexto=_contexto_juez(contexto) if fase == "tarea" else "")
        # Esquema obligatorio: con solo «json_object», haiku a veces se ponía a analizar en
        # voz alta las letras españolas y no llegaba al veredicto (2 de cada 4).
        r = _juez_prov.completar([{"role": "user", "content": p}], max_tokens=30, temperature=0,
                                 response_format=_VEREDICTO, reasoning_effort="off")
        v = re.findall(r'"cumple"\s*:\s*(true|false)', r)
        if not v:
            raise ValueError(f"sin veredicto: {r[:80]!r}")
        return v[-1] == "true"
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Juez de objetivo no disponible ({type(e).__name__}) → palabras clave")
        return None


def usa_patron(cd, mensaje, juez=None):
    """¿Ha usado Laura lo de este can-do? Determinista: conjugación correcta para
    'te'/'ta'/'tekudasai'; para el resto, que salga alguno de sus ingredientes.
    ponytail: "sale el ingrediente" no es "lo usa bien"; el matiz lo pone el LLM."""
    patron = cd.get("patron")
    if patron in ("te", "ta"):
        return bool(analizar(mensaje, patron)["correctas"])
    if patron == "tekudasai":
        return any(re.search(re.escape(f) + r"\s*(ください|下さい)", mensaje)
                   for f in analizar(mensaje)["correctas"])
    if patron == "llano":  # hablar en forma llana: japonés sin です/ます
        return bool(_RE_JP_CHAR.search(mensaje)) and not re.search("です|ます|でし|まし", mensaje)
    if juez is not None:  # función (cd, mensaje) → bool|None; None = no sé
        v = juez(cd, mensaje)
        if v is not None:
            return v
    if cd.get("requiere"):  # el patrón manda: nombrar un ingrediente suelto no basta
        return any(r in mensaje for r in cd["requiere"])
    return any(f in mensaje for f in _formas(cd))


def errores(cd, mensaje):
    """Errores de conjugación comprobados: forma て siempre (es la base de
    casi todo) y forma た."""
    return analizar(mensaje)["errores"] + analizar(mensaje, "ta")["errores"]


def presentar(cd):
    return (
        f"Preséntale lo de hoy: {cd['texto']}. Explicación (elige solo lo imprescindible para "
        f"empezar y dilo natural, sin recitarla; el resto lo verá al corregirla): {cd['explicacion']} "
        "Como máximo 2 o 3 cosas japonesas nuevas en total (el ejemplo cuenta); el resto, en los "
        "siguientes turnos. Todo en unos 15 segundos hablado: explicación de 1-2 frases cortas. Pon un ejemplo con algo de su vida. "
        + PEDIR_FRASE
    )


# Laura no puede decir una frase con palabras que nunca ha visto: Kaito le pide algo
# concreto y le da antes lo que le falte (la lista está en «Palabras que Laura ya ha visto»).
PEDIR_FRASE = (
    "Termina pidiéndole UNA frase concreta que use lo de hoy: dile en español exactamente qué "
    "tiene que decir (algo corto de su vida, distinto de tu ejemplo), no solo un tema. Que pueda "
    "montarla con palabras que ya ha visto; si le falta alguna (como mucho 2), dásela antes en "
    "japonés y di qué significa con palabras (nada de signos como =). Los nombres propios no son palabras"
    " nuevas: se dicen tal cual, sin traducirlos.")


def tarea(cd):
    return (f"Plantéale esta tarea EN ESPAÑOL, empezando directamente por la situación (nada de «la tarea es»), haciendo tú tu parte, sin "
            f"darle la respuesta ni un ejemplo. {cd['tarea']} Si para contestar le falta alguna palabra "
            "que no ha visto (como mucho 2), dásela suelta en japonés y di qué significa. Todo en 2 frases cortas como máximo, "
            "y pídele lo que dice «Laura tiene que», sin añadir más cosas. Háblale a ella de tú (nunca "
            "digas «Laura tiene que»: eso es para ti). Ella contesta en japonés.")


def que_hacer(cd):
    """La parte «Laura tiene que: …» de la tarea, sin la situación."""
    t = cd.get("tarea", "")
    return t.split("Laura tiene que:", 1)[-1].strip()


def tarea_nueva(cd):
    """Tarea de repaso: Kaito no ve la situación original, así que la inventa."""
    return ("Plantéale EN ESPAÑOL una situación cotidiana nueva, inventada por ti, en la que "
            f"Laura tenga que: {que_hacer(cd)} Situación de UNA sola frase y UNA sola acción, que "
            "pueda contar con palabras que ya ha visto (nada de historias con varios pasos). Empieza "
            "directamente por ella, haz tú tu parte y no le des la respuesta ni un ejemplo; si le "
            "falta alguna palabra (como mucho 2), dásela suelta en japonés con su significado. "
            "Háblale a ella de tú. Ella contesta en japonés.")


def cortar_frases(texto, minimo=25, final=False):
    """Corta lo que llega del LLM en frases COMPLETAS para ir hablándolas ya: termina en
    . ? ! 。 o salto de línea, nunca dentro de un bloque 【…】 y con al menos `minimo`
    caracteres (una frase muy corta se une a la siguiente: cada trozo de voz cuesta ~1 s).
    Devuelve (frases, resto); con `final=True` el resto también sale como frase."""
    frases, ini, prof = [], 0, 0
    for i, ch in enumerate(texto):
        if ch == "【":
            prof += 1
        elif ch == "】":
            prof = max(0, prof - 1)
        elif prof == 0 and ch in ".?!。\n" and len(texto[ini:i + 1].strip()) >= minimo:
            frases.append(texto[ini:i + 1].strip())
            ini = i + 1
    resto = texto[ini:]
    if final and resto.strip():
        frases.append(resto.strip())
        resto = ""
    return frases, resto
