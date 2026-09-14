"""Clase ProfesorJapones: orquestador del modo sensei.

Estado propio, historial independiente del de Brain, integración
de SRS (Fase 1) y currículo (Fase 2).
"""

import json
import random
import re
import threading
import time
from datetime import datetime

from ai.openrouter_provider import OpenRouterProvider
from ai.prompts import cargar_prompt
from ai.sensei.curriculum import (
    CURRICULUM,
    ITEM_POR_JP,
    siguiente_items_nuevos,
    unidad_actual,
)
from core.config import (
    CHEQUEO_OXIDO_CADA,
    EXTRACCION_PAUSA_LLAMADAS_SEG,
    EXTRACCION_RETRASO_SEG,
    MAX_ITEMS_NUEVOS,
    NIVEL_INMERSION_FORZADO,
    NIVEL_INMERSION_UMBRALES,
    MAX_TOKENS_SENSEI,
    MAX_TOKENS_EXPLICACION,
    REASONING_EFFORT_SENSEI,
    TEMPERATURE_SENSEI,
    THROTTLE_DUE,
)

# ── Constantes ────────────────────────────────────────────────────────────────

MAX_TURNOS = 10  # pares user/assistant conservados en el contexto del LLM
# ponytail: naive "unidad entera, recortada" como ítems del can-do activo — no hay
# mapa can-do→ítem para N5. Sube esto o mete el mapa si el FOCO se queda corto.
ITEMS_CANDO_FOCO = 12  # ítems del can-do activo que se listan en el FOCO
MUESTRA_OXIDO = 3      # ítems 'sabido' de unidades pasadas en el chequeo de óxido
# "Introduce como máximo UNA cosa nueva por turno" del prompt no frena una
# racha: en cuanto Laura encadena varios BIEN seguidos, el modelo se envalentona
# y mete verbo tras verbo (visto en sesión real: 15+ palabras nuevas en 14 min).
# Por encima de esto, el FOCO manda parar en vez de confiar solo en el prompt.
UMBRAL_FRENO_NUEVOS = 6

# Juez de turno (ver _revisar_turno): mismo modelo que el profesor, mismo
# proveedor (OpenRouter), esfuerzo bajo — barato en tokens (5 booleanos, casi
# nada de salida) y sin el riesgo de "high" (ver commit que lo bajó a medium:
# gpt-oss-120b devolvía vacío y caía al modelo de reserva lento en cada turno).
MODELO_JUEZ = "openai/gpt-oss-120b"
EFFORT_JUEZ = "low"
_JUEZ_SISTEMA = (
    "Eres un revisor automático de un profesor de japonés. Te paso el FOCO "
    "(lo que la alumna ya sabe o ya se le ha explicado hoy), el MENSAJE que "
    "se le va a HABLAR de verdad, y la FRASE OBJETIVO interna (Laura no la "
    "oye — solo puntúa su pronunciación del turno siguiente; puede venir "
    "vacía si el turno no pide repetir nada). Responde SOLO con un JSON de "
    "estas seis claves, cada una true o false:\n"
    '  "vocab_no_enseñado": true si el MENSAJE le PIDE decir, repetir o '
    "traducir una palabra o frase japonesa que NO esté marcada "
    "[sabida]/[en progreso]/[trabajándose hoy] en el FOCO, NI en la lista de "
    "'ya has dicho esto', NI se explique dentro del propio MENSAJE antes de "
    "pedírsela.\n"
    '  "dicta_y_pide_repetir": true si el MENSAJE ENSEÑA una palabra o '
    "frase nueva Y en el MISMO mensaje le pide que la repita o produzca — "
    "tiene que ser una cosa u otra, nunca las dos en el mismo turno.\n"
    '  "mas_de_una_cosa_nueva": true si el MENSAJE introduce 2 o más '
    "palabras o expresiones japonesas distintas que no estaban ya sabidas.\n"
    '  "objetivo_no_coincide": true si la FRASE OBJETIVO no está vacía Y usa '
    "palabras que NO aparecen en ningún sitio del MENSAJE.\n"
    '  "mas_de_una_correccion": true si el MENSAJE señala o corrige más de '
    "un fallo de Laura a la vez.\n"
    '  "frase_incompleta": true si el MENSAJE tiene un hueco donde debería '
    "haber una palabra o frase y no la hay — asteriscos sueltos ('****'), "
    "comillas o paréntesis vacíos, o una frase que anuncia algo ('se dice', "
    "'es', 'sería', 'significa') y no queda nada legible después. Ejemplo "
    "que SÍ es true: \"'Yo estudié' se dice ****. Ahora repite.\" (el hueco "
    "después de 'se dice' está vacío). Ejemplo que es false: \"'Yo estudié' "
    "se dice 【べんきょうしました】.\" (hay contenido real después).\n"
    "Si el mensaje no pide producir nada ni corrige nada, todas deben ser "
    "false. Responde SOLO el JSON, sin texto adicional ni markdown."
)
# Clave del JSON del juez → explicación en español para el aviso de reintento.
_EXPLICACION_FALLO_JUEZ = {
    "vocab_no_enseñado": "pedías algo que nunca le has enseñado",
    "dicta_y_pide_repetir": "enseñabas una palabra y le pedías repetirla en "
        "el mismo turno — o la enseñas, o se lo pides, nunca las dos cosas a la vez",
    "mas_de_una_cosa_nueva": "metías más de una palabra/expresión nueva de "
        "golpe — solo una por turno",
    "objetivo_no_coincide": "el @@OBJETIVO@@ usaba palabras que no dijiste "
        "en el mensaje visible",
    "mas_de_una_correccion": "corregías más de un fallo a la vez — como "
        "mucho uno por turno",
    "frase_incompleta": "la frase se quedaba a medias o sin sentido al "
        "leerla en voz alta — probablemente porque el recorte de japonés se "
        "comió un bloque entero del que dependía el resto de la frase",
}

_MARCA_ESTADO = {"sabido": "[sabida]", "en_progreso": "[en progreso]", "nuevo": "[nueva]"}

# can_do_id → texto legible, plano sobre todas las unidades del temario.
_CANDO_TEXTO = {
    cd["id"]: cd["texto"]
    for u in CURRICULUM for cd in (u.get("can_dos") or [])
}

# Saludo/despedida de apertura: expresión japonesa CORTA + el resto en español,
# para que se entienda sea cual sea el nivel (una frase japonesa entera aquí es
# justo lo que el alumno principiante no pilla).
SALUDOS = [
    "Modo Sensei activado! 【こんにちは】, Laura. ¿Qué tal estás?",
    "Modo Sensei activado! 【おはよう】, Laura. ¿Lista para practicar japonés?",
    "Modo Sensei activado! 【こんばんは】, Laura. ¿Cómo va el día?",
    "Modo Sensei activado! 【やあ】, Laura. ¿Empezamos?",
    "Modo Sensei activado! 【こんにちは】, Laura. Vamos a repasar un poco de japonés.",
]

DESPEDIDAS = [
    "【またね】, Laura.",
    "【じゃあね】, Laura. Nos vemos pronto.",
    "【おつかれさま】. Hasta la próxima.",
    "【さようなら】, Laura. Hasta otro día.",
    "【バイバイ】, Laura. Cuídate.",
]

# Resultados que el extractor puede devolver por can-do (Fase 08).
_RESULTADOS_CAN_DO = {"conseguido", "parcial", "no_intentado", "error"}

# Bloques 【...】 que contienen al menos un kana/kanji (con o sin puntuación dentro).
_RE_BLOQUE_JP = re.compile(r'【([^【】]*[぀-ゟ゠-ヿ一-鿿][^【】]*)】')
# Cualquier carácter japonés.
_RE_JP_CHAR = re.compile(r'[぀-ゟ゠-ヿ一-鿿]')
# Kanji (incl. extensión A). Un candidato a frase objetivo DENSO en kanji suele
# ser el nombre de la unidad ("挨拶と基本表現") o una descripción ("今日は挨拶の練習")
# colada, no algo que Laura deba pronunciar. Pero las frases-función N5 llevan
# 1-3 kanji sobre kana ("もう一度お願いします") y SÍ son objetivo: por eso se permite
# lo que esté en _EXPR_OK_NIVEL_BAJO o tenga poca proporción de kanji.
# ponytail: heurística por proporción de kanji + lista blanca. Si algún día se
# enseña producción de frases con kanji denso, pasar el candidato por kana.
_RE_KANJI = re.compile(r'[㐀-䶿一-鿿]')
_KANJI_RATIO_MAX_OBJETIVO = 0.4  # más kanji que esto → descripción, no objetivo


_LARGO_MIN_RATIO_KANJI = 3  # a esta longitud o menos, la proporción no dice nada
# (un verbo diccionario como 【飲む】/【見る】 es kanji+kana 1:1 y NO es descripción)


def _kanji_bloquea_objetivo(b: str) -> bool:
    """True si el bloque tiene demasiado kanji para ser una frase objetivo real
    (y no está en la lista blanca de expresiones fijas N5).

    Bloqueaba también verbos en diccionario de un solo kanji ('飲む', '見る':
    1 kanji en 2 caracteres = 50%, por encima del umbral) y entonces
    _extraer_frase_objetivo se quedaba sin ese bloque como candidato y caía a
    uno anterior de la MISMA respuesta — Azure puntuaba el siguiente turno
    contra una frase objetivo distinta a la que el profesor acababa de pedir."""
    if not _RE_KANJI.search(b):
        return False
    if b in _EXPR_OK_NIVEL_BAJO:
        return False
    if len(b) <= _LARGO_MIN_RATIO_KANJI:
        return False
    kanji = len(_RE_KANJI.findall(b))
    return kanji / max(len(b), 1) > _KANJI_RATIO_MAX_OBJETIVO
# Texto entre comillas japonesas 「…」 / 『…』.
_RE_ENTRECOMILLADO = re.compile(r'[「『]([^「」『』]*)[」『』]')

# Frases de ánimo/muletillas: NO son algo que Laura deba repetir.
_FRASES_ANIMO = {
    "よくできました", "いいね", "すごい", "じょうず", "じょうずです", "がんばって",
    "がんばろう", "もういちど", "もういちどおねがいします", "おねがいします",
    "そうです", "せいかい", "だいじょうぶ", "オーケー", "はい", "ええ",
}
# Señales de que el turno pide PRODUCIR una frase japonesa concreta —
# es decir, que hay un objetivo LITERAL que Laura debe repetir tal cual.
# "cómo dirías" NO va aquí a propósito: es una pregunta ABIERTA ("¿cómo
# dirías X usando 【ます】?") en la que Laura tiene que construir la frase
# ella misma — 【ます】 ahí es una pista gramatical, no el objetivo a
# repetir. Colarlo hacía que _extraer_frase_objetivo cogiera esa partícula
# suelta como frase objetivo y Azure puntuara la pronunciación de Laura
# contra "ます" en vez de contra lo que de verdad intentó decir. Una
# dictado real siempre trae además "repite"/"di conmigo"/etc., así que
# quitarlo no pierde ningún caso legítimo.
_PISTAS_PRODUCCION = (
    "repit", "repít", "repet",  # repite, repítela, repíteme, repetir, repetirme…
    "di conmigo", "dilo", "dila", "di la frase",
    "cómo se dice", "como se dice",
    "inténtalo", "intentalo", "prueba a decir", "practica diciendo",
    "completa la frase", "puedes decir", "puedes decirla", "vuelve a decir",
    "pronuncia", "a ver cómo suena", "dímelo",
)


# Fase 17 — arco de sesión. Palabras con que Laura suele despedirse; heurística
# a propósito simple (el gate real es calentamiento vs foco por turno).
_DESPEDIDAS_LAURA = (
    "adiós", "adios", "hasta luego", "hasta la próxima", "hasta la proxima",
    "hasta mañana", "hasta manana", "hasta la semana", "me voy", "nos vemos",
    "lo dejamos", "lo dejo aquí", "lo dejo aqui", "lo dejo por hoy",
    "ya es suficiente", "suficiente por hoy", "ya está bien por hoy",
    "じゃあね", "またね", "さようなら", "バイバイ",
)


def _fase_sesion(turno: int, ultimo_de_laura: str) -> str:
    """Pista de arco de sesión para la cabecera del FOCO (Fase 17).

    turno 1 → entrada (saluda de vuelta, pregunta qué tal, y engancha ya con el
    can-do; el saludo de apertura ya cuenta como calentamiento). Laura se
    despide → cierre (el prompt ya trae el ritual). Resto → foco."""
    if ultimo_de_laura and any(
        p in ultimo_de_laura.lower() for p in _DESPEDIDAS_LAURA
    ):
        return "FASE DE LA SESIÓN: cierre"
    if turno <= 1:
        return (
            "FASE DE LA SESIÓN: entrada — salúdala de vuelta y pregúntale qué tal "
            "le va. En cuanto haya un hueco natural, engancha YA "
            "con el can-do de hoy: no te quedes en saludos ni alargues la charla, "
            "y no montes un drill de pronunciación del saludo."
        )
    return "FASE DE LA SESIÓN: foco"


def _nivel_inmersion(perfil_jap: dict) -> int:
    """Nivel de inmersión 1→4 a partir del vocabulario que Laura ya domina.

    Sube solo según avanza; NIVEL_INMERSION_FORZADO lo fija a mano para probar."""
    if NIVEL_INMERSION_FORZADO:
        return max(1, min(4, NIVEL_INMERSION_FORZADO))
    estados = perfil_jap.get("vocab_by_status") or {}
    dominado = estados.get("learned", 0) + estados.get("mastered", 0)
    return 1 + sum(dominado >= umbral for umbral in NIVEL_INMERSION_UMBRALES)


def _limpiar_objetivo(s: str) -> str:
    return (s or "").strip("　 \t\n、。・…！？!?「」『』()（）").replace("【", "").replace("】", "")


def _extraer_frase_objetivo(texto: str):
    """La frase que el profesor pide REPETIR a Laura, para comparar contra ella en
    la evaluación de pronunciación del turno siguiente.

    Devuelve None salvo que el turno pida producción explícita ('repite',
    'cómo dirías'…). Manda la petición de producción: las muletillas de cierre
    ("¿vale?", "¿de acuerdo?") ya no vetan el objetivo, y sin petición no hay
    nada que puntuar aunque el turno pregunte por el significado."""
    if not texto:
        return None

    bajo = texto.lower()
    if not any(p in bajo for p in _PISTAS_PRODUCCION):
        return None

    entrecomillados = [
        _limpiar_objetivo(m) for m in _RE_ENTRECOMILLADO.findall(texto)
    ]
    entrecomillados = [
        e for e in entrecomillados
        if _RE_JP_CHAR.search(e) and len(e) >= 3 and not _kanji_bloquea_objetivo(e)
    ]
    if entrecomillados:
        return entrecomillados[-1]

    # Bloques 【…】 con japonés, con su posición para poder juntar los adyacentes.
    marcados = []
    for m in _RE_BLOQUE_LLANO.finditer(texto):
        b = _limpiar_objetivo(m.group(1))
        if (b and _RE_JP_CHAR.search(b) and b not in _FRASES_ANIMO
                and not _kanji_bloquea_objetivo(b)):
            marcados.append((m.start(), m.end(), b))
    if not marcados:
        return None

    # El prompt pone la frase objetivo al final del turno, a veces partida en
    # varios bloques seguidos ("Repite: 【ちょっと】…【もう一度お願いします】"). Se junta
    # la ÚLTIMA tanda de bloques separados solo por puntos suspensivos, espacios
    # o comas; así el objetivo es la frase entera, no su último trozo.
    grupo = [marcados[-1][2]]
    for i in range(len(marcados) - 1, 0, -1):
        hueco = texto[marcados[i - 1][1]:marcados[i][0]]
        if re.fullmatch(r'[\s…。、・.,\-–—]*', hueco or ""):
            grupo.insert(0, marcados[i - 1][2])
        else:
            break
    return " ".join(grupo) if len(grupo) > 1 else grupo[0]


# Línea centinela con la que el modelo declara la frase objetivo:
# "@@OBJETIVO: ちょっと、もう一度お願いします@@". No se habla ni se guarda.
# Tolerante: el modelo a veces se deja el "@@" de cierre o lo manda vacío; se
# captura hasta el "@@" de cierre, el fin de línea o el fin del texto, y SIEMPRE
# se recorta del mensaje hablado (aunque el objetivo salga vacío).
_RE_OBJETIVO_CENTINELA = re.compile(
    r'@@\s*OBJETIVO\s*:[ \t]*(.*?)[ \t]*(?:@@|$)',
    re.IGNORECASE | re.MULTILINE,
)


def _partir_objetivo_centinela(respuesta: str):
    """Separa la línea centinela del resto de la respuesta.

    Devuelve `(respuesta_sin_centinela, objetivo|None)`. Sin centinela devuelve
    `(respuesta, None)` y el llamante cae a `_extraer_frase_objetivo`.
    """
    if not respuesta:
        return respuesta, None
    m = _RE_OBJETIVO_CENTINELA.search(respuesta)
    if not m:
        return respuesta, None
    objetivo = _limpiar_objetivo(m.group(1).strip())
    limpia = (respuesta[:m.start()] + respuesta[m.end():]).strip()
    return limpia, (objetivo or None)


_RE_BLOQUE_LLANO = re.compile(r'【([^【】]+)】')
_RE_FIN_FRASE_JP = re.compile(r'[。！？]')
# Marcas de que un 【】 es una FRASE, no una palabra/expresión suelta: colas de
# cortesía o verbales pegadas a más texto. Solo se aplica a bloques que NO estén
# en la lista blanca de expresiones fijas de abajo.
_RE_JP_FRASE = re.compile(r'(でした|ました|でしょう|ましょう|ですか|ますか|んです|してくださ|といます|に入り)')
_LARGO_MAX_NIVEL_BAJO = 12  # caracteres dentro de 【】 tolerados en nivel 1-2
# Un bloque corto que termina en ました/でした SUELE ser justo la conjugación que
# se está enseñando ("見ました", "でした"), no una frase tema+comentario a medias:
# solo se descarta por _RE_JP_FRASE si además es más largo que esto (p.ej.
# "何か食べましたか" sí es una frase completa aunque quepa en pocos caracteres).
_LARGO_MAX_COLA_VERBAL = 6
# La longitud sola no distingue "verbo suelto con adverbio" (【早く起きました】,
# 7) de "tema + comentario" (【きのうは休みでした】, 9) — pueden pesar casi igual.
# Lo que de verdad los separa es si hay una partícula que engancha un
# argumento (tema は/が, objeto を, lugar/hora に・で) o una marca de pregunta
# か al final: sin eso, es un adverbio+verbo suelto (adjetivo con caso real:
# 【早く起きました】, 【べんきょうしました】) y se deja aunque pase de
# _LARGO_MAX_COLA_VERBAL — es justo la conjugación que tocaba enseñar. Con
# eso, sigue siendo frase y se descarta. Comprobado con un bug real: sin este
# distintivo, "la frase queda 【早く起きました】" se comía el bloque entero y
# dejaba "la frase queda ****" — ni el reintento del juez lo arreglaba,
# porque _acotar_japones se lo volvía a comer igual la segunda vez.
_RE_ARGUMENTO_O_PREGUNTA = re.compile(r'[はがをにで]|か$')
# Expresiones fijas N5 (saludos, cortesía y las frases-función de la unidad 0:
# pedir que repitan, decir que no entiendes). En nivel bajo se dejan enteras
# aunque lleven ます/ください/una coma: son justo lo que Laura tiene que aprender.
_EXPR_OK_NIVEL_BAJO = {
    "おはよう", "おはようございます", "こんにちは", "こんばんは",
    "おやすみ", "おやすみなさい", "さようなら", "じゃあね", "またね",
    "ありがとう", "ありがとうございます", "どうもありがとうございます",
    "すみません", "ごめんなさい", "はじめまして", "おげんきですか",
    "げんきです", "はい", "いいえ", "ください", "おつかれさま",
    "おつかれさまでした", "いただきます", "ごちそうさま", "ごちそうさまでした",
    "いってきます", "いってらっしゃい", "ただいま", "おかえり", "おかえりなさい",
    "どうぞ", "どういたしまして", "おねがいします", "よろしくおねがいします",
    "よくできました", "そうです", "ちがいます", "だいじょうぶ", "だいじょうぶです",
    "どうも", "けっこうです",
    # Unidad 0 — can-do "no he entendido / que lo repitan"
    "もういちど", "もう一度", "わかりません", "わかりました",
    "もういちどおねがいします", "もう一度おねがいします", "もう一度お願いします",
    "ゆっくりおねがいします", "ゆっくりお願いします",
    "ちょっとまってください", "ちょっと待ってください",
}


def _acotar_japones(respuesta: str, nivel: int) -> str:
    """Aplana el marcado 【】 y, en nivel 1-2, recorta las frases japonesas.

    En nivel 1-2 el profesor debe hablar español con palabras/expresiones
    japonesas SUELTAS. Si aun así suelta frases enteras en 【】 (tema + comentario,
    てください, formas de cortesía largas…), aquí se recortan a la primera
    expresión corta, o se quitan si no queda nada útil. Las expresiones fijas de
    saludo (lista blanca) se dejan enteras. Determinista: no depende de que el
    modelo obedezca el prompt."""
    from ai.sensei.kana import normalizar_bloques_jp
    respuesta = normalizar_bloques_jp(respuesta or "")
    if nivel > 2:
        return respuesta

    def _recorta(m):
        cont = m.group(1).strip("　 ・…「」『』（）()〜~。！？、").strip()
        if cont in _EXPR_OK_NIVEL_BAJO:
            return f"【{cont}】"
        # Combo de expresiones fijas separadas por 、 (「すみません、わかりません」,
        # 「すみません、もういちどおねがいします」): se deja entero.
        partes = [p.strip() for p in cont.split("、") if p.strip()]
        if len(partes) >= 2 and all(p in _EXPR_OK_NIVEL_BAJO for p in partes):
            return f"【{cont}】"
        cabeza = _RE_FIN_FRASE_JP.split(cont)[0].split("、")[0]
        cabeza = cabeza.strip("　 ・…「」『』（）()〜~").strip()
        if not cabeza:
            return ""
        if cabeza in _EXPR_OK_NIVEL_BAJO:
            return f"【{cabeza}】"
        # Sigue pareciendo una frase (larga, o con cola verbal/cortés PEGADA A
        # MÁS TEXTO) → fuera: un fragmento a medias confunde más que quitarlo.
        # Pero si es corto Y la cola verbal/cortés es prácticamente todo el
        # bloque, es la conjugación suelta que tocaba enseñar (ver
        # _LARGO_MAX_COLA_VERBAL) — esa SÍ se deja. Y si es más largo pero NO
        # tiene ninguna partícula que enganche un argumento (ver
        # _RE_ARGUMENTO_O_PREGUNTA), sigue siendo solo un verbo con adverbio,
        # no una frase tema+comentario — también se deja.
        if len(cabeza) > _LARGO_MAX_NIVEL_BAJO:
            return ""
        if (len(cabeza) > _LARGO_MAX_COLA_VERBAL and _RE_JP_FRASE.search(cabeza)
                and _RE_ARGUMENTO_O_PREGUNTA.search(cabeza)):
            return ""
        return f"【{cabeza}】"

    fuera = _RE_BLOQUE_LLANO.sub(_recorta, respuesta)
    # Limpia dobles espacios / signos huérfanos que deja el recorte.
    fuera = re.sub(r'\s{2,}', ' ', fuera)
    fuera = re.sub(r'[ \t]+([.,;:)])', r'\1', fuera)
    return fuera.strip()


def _lineas_foco(jp, meaning, sufijo=""):
    """Líneas del FOCO para un ítem: glosa + ejemplo, literal y uso del temario.

    Los ítems de repaso vienen de la BD sin esos campos; se buscan por jp en el
    temario. Sin ellos Kaito solo tiene la glosa y se inventa el resto."""
    info = ITEM_POR_JP.get(jp, {})
    lineas = [f"  - 【{jp}】 {meaning}{sufijo}"]
    if info.get("ejemplo"):
        literal = f"  ({info['literal']})" if info.get("literal") else ""
        lineas.append(f"      ejemplo: {info['ejemplo']}{literal}")
    if info.get("uso"):
        lineas.append(f"      uso: {info['uso']}")
    return lineas


_EXTRACCION_PROMPT = cargar_prompt("extraccion_sesion")


class ProfesorJapones:

    def __init__(self, jap_memory, provider, memory, socketio):
        """
        jap_memory — JapaneseMemory (capa de datos japonés + SRS)
        provider   — proveedor LLM principal (openai/gpt-oss-120b)
        memory     — core.memory.Memory (perfil general de Laura)
        socketio   — instancia Flask-SocketIO para emitir eventos
        """
        self.jap_memory = jap_memory
        self.provider = provider
        self.memory = memory
        self.socketio = socketio
        # Juez rápido que revisa cada respuesta ANTES de hablar — ver
        # _revisar_turno. Si OpenRouter no está disponible (sin API key, sin
        # red) se desactiva solo: el turno sigue igual, solo que sin chequeo.
        try:
            self._provider_juez = OpenRouterProvider(modelos=[MODELO_JUEZ])
        except Exception as e:
            print(f"⚠️ Juez de turno no disponible: {e}")
            self._provider_juez = None

        self.activo = False
        self.nivel_inmersion = 1    # lo recalcula _montar_estado() cada turno
        self.timer = None
        self.session_id = None
        self.mensajes = []          # historial propio de la sesión sensei (solo user/assistant)
        # Frase que el profesor pidió repetir en su último turno (ReferenceText de Azure).
        self.ultima_frase_objetivo = None

        # Estado del último FOCO (para cierre resiliente): ítems nuevos y unidad
        # abierta, ambos resueltos una vez por sesión en entrar().
        self._foco_nuevos = []
        self._foco_unidad = None

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    # Un solo modo (profe particular medio colega). Se mantiene el nombre por los
    # call sites de STT (transcribir_para_turno): False = evalúa pronunciación
    # cuando hay frase objetivo, igual que hacía el viejo registro "mixto".
    modo_conv = False

    def entrar(self):
        """Activa el modo sensei y abre una sesión en la BD."""
        self.activo = True
        self.mensajes = []
        self.ultima_frase_objetivo = None

        # La unidad abierta y los ítems nuevos del can-do activo se resuelven UNA
        # vez por sesión (no una por turno). Los nuevos se persisten al cerrar
        # (_ejecutar_extraccion), no aquí. MAX_ITEMS_NUEVOS limita cuántos.
        self._foco_unidad = unidad_actual(self.jap_memory)
        self._foco_nuevos = siguiente_items_nuevos(self.jap_memory, MAX_ITEMS_NUEVOS)

        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.jap_memory._conectar() as conn:
            cursor = conn.execute(
                "INSERT INTO japanese_sessions (started_at) VALUES (?)", (now,)
            )
            self.session_id = cursor.lastrowid

        if self.timer:
            self.timer.cancel()
        self._renovar_timer()
        self.socketio.emit("modo_sensei", {"activo": True})
        print("🎌 Modo Sensei activado")

    def saludo_inicial(self) -> str:
        """Saludo de apertura y lo registra en el historial de la sesión.

        Sin esto el modelo no sabe que ya ha saludado: vuelve a saludar en su
        primer turno y se queda en un bucle de saludos / repetir el saludo en
        vez de entrar en materia. En el historial va sin el prefijo de UI."""
        saludo = random.choice(SALUDOS)
        limpio = saludo.split("! ", 1)[-1] if "! " in saludo else saludo
        self.mensajes.append({"role": "assistant", "content": limpio})
        return saludo

    def salir(self):
        """Desactiva el modo sensei, cancela el timer y cierra la sesión.

        El evento modo_sensei activo:False lo emite app.py después de que el
        TTS termine, para que la despedida se pronuncie con la cara sensei.
        """
        if self.timer:
            self.timer.cancel()
            self.timer = None
        self.activo = False
        # La extracción tarda entre 5 y 15 s; que no bloquee la despedida.
        self.socketio.start_background_task(self.cerrar_sesion_y_extraer)
        print("🎌 Modo Sensei desactivado")

    def esta_activo(self) -> bool:
        return self.activo

    def _renovar_timer(self):
        """Reinicia el contador de inactividad de 20 minutos."""
        if self.timer:
            self.timer.cancel()
        def _timeout():
            self.activo = False
            self.timer = None
            # ponytail: DB/LLM writes via managed socketio task, not daemon timer thread
            self.socketio.start_background_task(self.cerrar_sesion_y_extraer)
        self.timer = threading.Timer(20 * 60, _timeout)
        self.timer.daemon = True
        self.timer.start()

    def _revisar_turno(self, respuesta_final: str, objetivo: str, foco: str) -> dict:
        """Juez rápido (mismo modelo del profesor, esfuerzo bajo) antes de
        hablar: repasa la respuesta YA RECORTADA (lo que de verdad se va a
        decir, ver _procesar en responder_turno) contra las 6 reglas de
        _JUEZ_SISTEMA. Ataja el problema en el origen — antes de que llegue
        a hablarse — en vez de corregirlo después. `objetivo` va aparte (no
        va dentro de `respuesta_final`: _partir_objetivo_centinela ya lo
        separó) para poder revisar "objetivo_no_coincide".

        Devuelve {} (nada marcado) si el juez no está disponible o falla:
        nunca bloquea el turno por su cuenta. reasoning_effort="low" es
        obligatorio: gpt-oss-120b sin él (ni con "off") razona igual por
        dentro y se come el presupuesto de tokens sin dejar nada para la
        respuesta. Y con varias claves en JSON necesita bastante más margen
        que un SI/NO suelto: con 150 salía vacío, con 400 iba justo (~3s la
        primera vez), con 800 iba fino — 600 de margen — comprobado en vivo."""
        if not self._provider_juez:
            return {}
        try:
            crudo = self._provider_juez.completar(
                [
                    {"role": "system", "content": _JUEZ_SISTEMA},
                    {"role": "user", "content": (
                        f"FOCO:\n{foco}\n\n"
                        f"MENSAJE que se le va a hablar:\n{respuesta_final}\n\n"
                        f"FRASE OBJETIVO interna: {objetivo or '(ninguna)'}"
                    )},
                ],
                max_tokens=600,
                temperature=0,
                reasoning_effort=EFFORT_JUEZ,
                response_format={"type": "json_object"},
            )
            data = json.loads(crudo)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"⚠️ Juez de turno falló, dejo pasar el turno: {e}")
            return {}

    # ── Turno de conversación ─────────────────────────────────────────────────

    def responder_turno(self, mensaje: str, lento_extra: bool = False, pron_contexto: str = None) -> str:
        """Genera la respuesta del sensei para un turno.

        Construye el historial desde cero usando el estado actual (SRS +
        currículo) sin tocar el historial de Brain. No lanza excepciones al
        exterior — ante fallos del proveedor devuelve mensaje de error amable.

        `pron_contexto` — resumen de la evaluación de pronunciación de Azure
        para este audio (o None). Se inyecta en el turno del usuario para que el
        profesor dé feedback específico; NO se guarda en el historial limpio.
        """
        self._renovar_timer()

        # Construir historial del sensei desde cero (sin mutar el de Brain)
        try:
            prompt_base = cargar_prompt("profesor_japones")
        except Exception as e:
            print(f"⚠️ No se pudo cargar prompt profesor_japones: {e}")
            prompt_base = "Eres un profesor de japonés amable. Habla en japonés con 【】."

        recuerdas, foco = self._montar_estado()
        # Cuánto japonés puede hablar: lo fija el progreso de Laura, no el prompt.
        prompt_base = prompt_base.replace(
            "{NIVEL_INMERSION}", str(self.nivel_inmersion)
        )

        # Inyección de slots (Phase 4) o bloque extra de contexto (compatibilidad)
        if "{RECUERDAS_DE_LAURA}" in prompt_base and "{FOCO_DE_HOY}" in prompt_base:
            sistema = prompt_base.replace("{RECUERDAS_DE_LAURA}", recuerdas).replace(
                "{FOCO_DE_HOY}", foco
            )
            historial_sensei = [{"role": "system", "content": sistema}]
        else:
            bloque_estado = f"RECUERDAS DE LAURA:\n{recuerdas}\n\nFOCO DE HOY:\n{foco}"
            historial_sensei = [
                {"role": "system", "content": prompt_base},
                {"role": "system", "content": bloque_estado},
            ]

        # Últimos MAX_TURNOS pares de la sesión actual
        historial_sensei.extend(self.mensajes[-(MAX_TURNOS * 2):])

        contenido_usuario = mensaje
        if pron_contexto:
            contenido_usuario += (
                "\n\n[EVALUACIÓN DE PRONUNCIACIÓN del audio de Laura (no la leas en voz "
                "alta ni menciones que hay un sistema que puntúa):\n"
                f"{pron_contexto}\n"
                "Haz caso al 'Veredicto':\n"
                "- Si es BIEN: felicítala en una frase y sigue.\n"
                "- Si es REGULAR o MAL: NO digas que lo ha dicho bien. Nombra la palabra "
                "fallida entre 【】 y di cómo suena la correcta, de forma breve y amable.\n"
                "- Si dice que ha dicho algo distinto a lo pedido: dile qué has oído y cuál "
                "era la frase, y pídele que la repita.]"
            )
        historial_sensei.append({"role": "user", "content": contenido_usuario})

        def _procesar(cruda: str):
            """Centinela + recorte de japonés en un solo paso, para poder
            aplicarlo igual a la respuesta original y a la del reintento.
            Devuelve (respuesta_final, objetivo_centinela); respuesta_final
            es None si queda vacía en cualquiera de los dos pasos (el modelo
            no dejó nada, o el recorte de nivel bajo se comió un bloque
            entero sin dejar apoyo alrededor)."""
            limpia, objetivo = _partir_objetivo_centinela(cruda)
            if not limpia or not limpia.strip():
                return None, None
            acotada = _acotar_japones(limpia, self.nivel_inmersion)
            if acotada != limpia:
                print(f"✂️  Japonés acotado a nivel {self.nivel_inmersion}")
            if not acotada or not acotada.strip():
                return None, None
            return acotada, objetivo

        # Llamar al LLM
        try:
            respuesta_cruda = self.provider.completar(
                historial_sensei,
                # Techo alto para todos los turnos: el desglose gramatical es
                # justo lo que se quedaba a medias. No se afina el límite por
                # tipo de turno (MAX_TOKENS_SENSEI existe pero no se usa aquí).
                max_tokens=MAX_TOKENS_EXPLICACION,
                temperature=TEMPERATURE_SENSEI,
                reasoning_effort=REASONING_EFFORT_SENSEI,
            )
        except Exception as e:
            print(f"❌ Error LLM en modo sensei: {e}")
            return "【ちょっとまってください。】 Un momento, hubo un problema técnico."

        respuesta, objetivo_centinela = _procesar(respuesta_cruda)
        if respuesta is None:
            # Vacía del modelo, o el recorte de nivel bajo se comió el único
            # bloque que había (turno que era UN SOLO 【frase larga】 sin apoyo
            # alrededor) — sin este chequeo Kaito se queda mudo o suelta una
            # frase a medias ("se dice ...") con TTS con texto vacío.
            print("⚠️ Respuesta vacía (del modelo o tras el recorte) en modo sensei")
            return "Perdona, se me ha cruzado un cable. ¿Me lo repites? 【もういちど おねがいします】"

        # Juez de turno: revisa el texto YA RECORTADO — el que de verdad se va
        # a hablar — no el crudo. Si viola alguna de las 6 reglas, un
        # reintento con el aviso puesto, antes de que llegue a hablarse.
        veredicto_juez = self._revisar_turno(respuesta, objetivo_centinela, foco)
        fallos = [k for k, v in veredicto_juez.items() if v and k in _EXPLICACION_FALLO_JUEZ]
        if fallos:
            explicacion = "; ".join(_EXPLICACION_FALLO_JUEZ[k] for k in fallos)
            print(f"⚠️ Juez: {', '.join(fallos)} — reintentando…")
            historial_reintento = historial_sensei + [
                {"role": "assistant", "content": respuesta_cruda},
                {"role": "user", "content": (
                    f"[SISTEMA] Esa respuesta no vale: {explicacion}. Respóndele de nuevo "
                    "evitando eso — usa solo lo que ya sabe (ver FOCO) y sigue las reglas "
                    "del prompt."
                )},
            ]
            try:
                reintento_cruda = self.provider.completar(
                    historial_reintento,
                    max_tokens=MAX_TOKENS_EXPLICACION,
                    temperature=TEMPERATURE_SENSEI,
                    reasoning_effort=REASONING_EFFORT_SENSEI,
                )
                reintento, objetivo_reintento = _procesar(reintento_cruda)
                if reintento is not None:
                    respuesta, objetivo_centinela = reintento, objetivo_reintento
                    # Solo aviso, sin volver a reintentar: un segundo fallo
                    # casi siempre es la MISMA causa de fondo (p.ej. el
                    # recorte comiéndose otra vez el mismo tipo de bloque),
                    # así que un tercer intento no arreglaría nada — solo
                    # gastaría otra llamada. Queda constancia para depurar.
                    veredicto_2 = self._revisar_turno(respuesta, objetivo_centinela, foco)
                    fallos_2 = [k for k, v in veredicto_2.items() if v and k in _EXPLICACION_FALLO_JUEZ]
                    if fallos_2:
                        print(f"⚠️ Juez: el reintento SIGUE con {', '.join(fallos_2)} — se deja pasar igual")
                # Si el reintento sale vacío, nos quedamos con la respuesta
                # original ya validada — el juez la marcó, pero es mejor eso
                # que arriesgarse a un turno mudo.
            except Exception as e:
                print(f"⚠️ Reintento del juez falló, sigo con la respuesta original: {e}")

        # Guardar turno limpio en el historial propio
        self.mensajes.append({"role": "user", "content": mensaje})
        self.mensajes.append({"role": "assistant", "content": respuesta})

        # Frase objetivo para la evaluación de pronunciación del PRÓXIMO turno:
        # manda el centinela; si el modelo no lo puso, heurística sobre 【】.
        self.ultima_frase_objetivo = (
            objetivo_centinela or _extraer_frase_objetivo(respuesta)
        )
        if self.ultima_frase_objetivo:
            origen = "centinela" if objetivo_centinela else "heurística"
            print(f"🎯 Frase objetivo ({origen}): {self.ultima_frase_objetivo}")

        return respuesta

    # ── Estado / orquestador ──────────────────────────────────────────────────

    def _muestra_oxido(self, unidad_abierta) -> list:
        """Chequeo de óxido: hasta MUESTRA_OXIDO ítems ya 'sabido' de unidades
        anteriores a la abierta, para que no se enmohezcan. Solo se llama cada
        CHEQUEO_OXIDO_CADA sesiones. Devuelve [(jp, meaning), ...]."""
        if not unidad_abierta:
            return []
        uid = unidad_abierta.get("id")
        out = []
        for u in CURRICULUM:
            if u.get("id") == uid:
                break
            if not u.get("can_dos"):
                continue  # unidad de kanji: su SRS es aparte
            for it in u["items"]:
                kind = "gramatica" if it["kind"] == "gramatica" else "vocabulario"
                if self.jap_memory.estado_item(it["jp"], kind) == "sabido":
                    out.append((it["jp"], it.get("meaning", "")))
                    if len(out) >= MUESTRA_OXIDO:
                        return out
        return out

    def _montar_estado(self) -> tuple:
        """Devuelve (recuerdas_de_laura, foco_de_hoy) como par de strings."""
        # ── RECUERDAS_DE_LAURA ─────────────────────────────────────────────
        try:
            perfil_general = self.memory.obtener_perfil()
        except Exception:
            perfil_general = ""

        perfil_jap = self.jap_memory.resumen_perfil()
        self.nivel_inmersion = _nivel_inmersion(perfil_jap)
        lineas_r = [perfil_general] if perfil_general else []

        if perfil_jap.get("vocab_by_status"):
            estados = ", ".join(
                f"{k}: {v}" for k, v in perfil_jap["vocab_by_status"].items()
            )
            lineas_r.append(f"Vocabulario por estado: {estados}")

        if perfil_jap.get("last_sessions"):
            lineas_r.append("Últimas sesiones:")
            lineas_r += [f"  - {s}" for s in perfil_jap["last_sessions"]]

        if perfil_jap.get("episodios_laura"):
            lineas_r.append("Lo que Laura ha contado de su vida:")
            lineas_r += [f"  - {e}" for e in perfil_jap["episodios_laura"]]

        if perfil_jap.get("anecdotas_kaito"):
            lineas_r.append("Lo que TÚ (Kaito) ya has contado de ti mismo — no te contradigas:")
            lineas_r += [f"  - {a}" for a in perfil_jap["anecdotas_kaito"]]

        if perfil_jap.get("sin_corregir"):
            lineas_r.append(f"Quedó sin corregir: {perfil_jap['sin_corregir']}")

        if perfil_jap.get("notas_profe"):
            lineas_r.append("Cómo va Laura (notas de sesiones anteriores):")
            lineas_r += [f"  - {n}" for n in perfil_jap["notas_profe"]]

        # THROTTLE_DUE (Fase 09): tamaño máximo de la lista de puntos débiles.
        if perfil_jap.get("weak_points"):
            puntos = ", ".join(
                f"{w['word']} ({w['errors']} errores)"
                for w in perfil_jap["weak_points"][:THROTTLE_DUE]
            )
            lineas_r.append(f"Puntos débiles (vocabulario): {puntos}")

        if perfil_jap.get("weak_grammar"):
            puntos_g = ", ".join(
                f"{g['punto']} ({g['errors']} errores)"
                for g in perfil_jap["weak_grammar"][:THROTTLE_DUE]
            )
            lineas_r.append(f"Puntos débiles (gramática): {puntos_g}")

        recuerdas_de_laura = "\n".join(lineas_r)

        # ── FOCO_DE_HOY ────────────────────────────────────────────────────
        # El FOCO se organiza alrededor del CAN-DO ACTIVO de la unidad abierta,
        # no de una cola de repaso SRS. (Fase 09.)
        unidad = self._foco_unidad or {}
        can_dos = unidad.get("can_dos", []) if isinstance(unidad, dict) else []
        prog = self.jap_memory.can_dos_progreso()

        lineas_f = []

        # Fase 17: arco de sesión. Nº de turno = pares user/assistant ya cerrados
        # + 1 (el actual aún no está en self.mensajes). La despedida se mira sobre
        # el último mensaje de Laura ya registrado, así que en el flujo real va un
        # turno por detrás; basta para dar la entrada al cierre.
        turno = len(self.mensajes) // 2 + 1
        ultimo_de_laura = next(
            (m["content"] for m in reversed(self.mensajes) if m["role"] == "user"),
            "",
        )
        lineas_f.append(_fase_sesion(turno, ultimo_de_laura))

        # Bloques 【】 DISTINTOS que Kaito ya ha soltado esta sesión, sin filtrar
        # por si ya eran sabidos — a propósito grosero, solo mide qué se ha
        # dicho ya. Se calcula sobre self.mensajes COMPLETO (nunca se recorta),
        # a diferencia de historial_sensei que solo manda los últimos
        # MAX_TURNOS pares al LLM: sin esto, pasados ~10 turnos el modelo deja
        # de "ver" lo que enseñó al principio y lo reintroduce como si fuera
        # nuevo (visto en sesión real: 【飲みます】 explicado como novedad 3
        # veces, 【起きます】 2 veces, en la misma conversación sin cortes).
        dicho_por_kaito = "\n".join(
            m["content"] for m in self.mensajes if m["role"] == "assistant"
        )
        bloques_dichos = {
            b for b in _RE_BLOQUE_LLANO.findall(dicho_por_kaito)
            if _RE_JP_CHAR.search(b) and b not in _EXPR_OK_NIVEL_BAJO and b not in _FRASES_ANIMO
        }
        if bloques_dichos:
            lineas_f.append(
                "Ya has dicho esto en 【】 esta sesión — NO lo vuelvas a presentar "
                "como si fuera nuevo, aunque ya no lo veas en los últimos turnos: "
                + ", ".join(f"【{b}】" for b in sorted(bloques_dichos))
            )
        if len(bloques_dichos) >= UMBRAL_FRENO_NUEVOS:
            lineas_f.append(
                f"⚠️ RITMO: ya has soltado {len(bloques_dichos)} palabras/expresiones "
                "distintas en 【】 esta sesión. PARA de introducir nada nuevo — ni "
                "aunque Laura pregunte por otra palabra o vaya encadenando aciertos — "
                "y dedica el resto de la sesión a que combine y repita SOLO lo que ya "
                "ha salido hoy."
            )

        if unidad:
            lineas_f.append(f"Unidad actual: {unidad['nombre']}")
            if unidad.get("funcion"):
                lineas_f.append(f"  para qué sirve: {unidad['funcion']}")
            if unidad.get("frases_hechas"):
                lineas_f.append("  expresiones naturales de esta unidad:")
                lineas_f += [
                    f"    - 【{f['jp']}】 {f['uso']}" for f in unidad["frases_hechas"]
                ]

        if can_dos:
            grupos = {"dominado": [], "en_progreso": [], "pendiente": []}
            for cd in can_dos:
                est = prog.get(cd["id"], {}).get("estado", "no_intentado")
                clave = est if est in ("dominado", "en_progreso") else "pendiente"
                grupos[clave].append(cd["texto"])
            lineas_f.append("Can-dos de esta unidad:")
            lineas_f.append(f"  dominados: {', '.join(grupos['dominado']) or '—'}")
            lineas_f.append(f"  en progreso: {', '.join(grupos['en_progreso']) or '—'}")
            lineas_f.append(f"  pendientes: {', '.join(grupos['pendiente']) or '—'}")

        # Can-do activo = primer can-do de la unidad que no está dominado.
        idx_activo = next(
            (i for i, cd in enumerate(can_dos)
             if prog.get(cd["id"], {}).get("estado") != "dominado"),
            None,
        )
        activo = can_dos[idx_activo] if idx_activo is not None else None
        siguiente = (
            can_dos[idx_activo + 1]
            if idx_activo is not None and idx_activo + 1 < len(can_dos)
            and prog.get(can_dos[idx_activo + 1]["id"], {}).get("estado") != "dominado"
            else None
        )
        # ¿Se dominó algún can-do hace nada (esta sesión o un par atrás), aunque
        # fuera de otra unidad? El más reciente se lo reconoce Kaito en la
        # entrada y presenta el nuevo. ponytail: ventana de 5 ids de sesión para
        # tragarnos sesiones abandonadas en medio.
        recien_dominado = None
        if turno <= 1:
            cand = [
                (v["ultima_sesion"], cid) for cid, v in prog.items()
                if v.get("estado") == "dominado" and v.get("ultima_sesion")
                and v["ultima_sesion"] >= (self.session_id or 0) - 5
                and cid != (activo["id"] if activo else None)
            ]
            if cand:
                recien_dominado = _CANDO_TEXTO.get(max(cand)[1])
        # Ítems a introducir hoy (elegidos en entrar()): casi siempre ya salen en
        # la lista del can-do de abajo, así que se marcan ahí en vez de repetir
        # el bloque entero. `nuevos_restantes` recoge los que no aparezcan.
        nuevos = self._foco_nuevos
        nuevos_jp = {n["jp"] for n in nuevos}
        nuevos_vistos = set()

        if activo:
            if recien_dominado:
                lineas_f.append(
                    f"ACABA DE DOMINAR (última sesión): «{recien_dominado}». "
                    "SOLO en este primer turno: reconóceselo de pasada a Laura "
                    "(«lo de … ya lo tienes») y engancha con el can-do de hoy. "
                    "Luego no lo vuelvas a mencionar ni a trabajar."
                )
            lineas_f.append(f"Can-do de hoy: {activo['texto']}")
            if siguiente:
                lineas_f.append(
                    f"Siguiente can-do (para encadenar): «{siguiente['texto']}». "
                    "Si HOY Laura ya ha producido el can-do de hoy ELLA SOLA (sin "
                    "que se lo dictes) dos veces o más, no sigas machacándolo: "
                    "empieza a colar el siguiente en la conversación. Puedes "
                    "trabajar los dos en la misma sesión."
                )
            items = unidad.get("items", [])[:ITEMS_CANDO_FOCO]
            if items:
                lineas_f.append(
                    "  lo que necesita (las [sabida] úsalas en japonés directamente):"
                )
                estados_it = self.jap_memory.estado_items_bulk(
                    (it["jp"], it["kind"]) for it in items
                )
                # Marca intra-sesión: si Kaito ya citó 【jp】 en un turno suyo de
                # esta sesión (dicho_por_kaito, calculado arriba para el freno de
                # ritmo), un ítem que aún sería [nueva] pasa a [trabajándose hoy]
                # (no repitas la glosa, pero sigue en el FOCO). Se busca el bloque
                # 【jp】 con corchetes, no el jp suelto, para no dar falsos
                # positivos con ítems de una sola kana (「て」, 「に」).
                for it in items:
                    kind = "gramatica" if it["kind"] == "gramatica" else "vocabulario"
                    estado = estados_it.get((it["jp"], kind), "nuevo")
                    if estado == "nuevo" and f"【{it['jp']}】" in dicho_por_kaito:
                        marca = "[trabajándose hoy]"
                    elif it["jp"] in nuevos_jp:
                        marca = "[introdúcelo hoy]"
                        nuevos_vistos.add(it["jp"])
                    else:
                        marca = _MARCA_ESTADO.get(estado, "[nueva]")
                    lineas_f += _lineas_foco(
                        it["jp"], it.get("meaning", ""), sufijo=f"  {marca}"
                    )
        elif can_dos:
            lineas_f.append(
                "Todos los can-dos de esta unidad están dominados. Repasa lo flojo "
                "o conversa libremente en japonés."
            )

        # Fallback: nuevos que no salieron en la lista del can-do (raro con
        # ITEMS_CANDO_FOCO=12). Se listan aparte para no perderlos.
        nuevos_restantes = [n for n in nuevos if n["jp"] not in nuevos_vistos]
        if nuevos_restantes:
            lineas_f.append(f"Ítems nuevos a introducir ({len(nuevos_restantes)}):")
            for nuevo in nuevos_restantes:
                lineas_f += _lineas_foco(
                    nuevo["jp"], nuevo["meaning"],
                    sufijo=f" (unidad: {nuevo['unidad']})",
                )

        # Chequeo de óxido: cada CHEQUEO_OXIDO_CADA sesiones, vocabulario viejo.
        if self.session_id and self.session_id % CHEQUEO_OXIDO_CADA == 0:
            oxido = self._muestra_oxido(unidad)
            if oxido:
                lineas_f.append(
                    "Repaso de mantenimiento (que no se oxide lo ya sabido):"
                )
                for jp, meaning in oxido:
                    lineas_f += _lineas_foco(jp, meaning, sufijo="  [sabida]")

        # (la línea de FASE DE LA SESIÓN no cuenta como contenido)
        if not [ln for ln in lineas_f
                if not ln.startswith("FASE DE LA SESIÓN")]:
            lineas_f.append(
                "Sin unidad abierta. Conversa libremente en japonés sobre cualquier tema."
            )

        foco_de_hoy = "\n".join(lineas_f)
        return recuerdas_de_laura, foco_de_hoy

    # ── Cierre de sesión y extracción (Fase 5) ───────────────────────────────

    def cerrar_sesion_y_extraer(self):
        """Extrae el aprendizaje de la sesión con LLM ligero y actualiza el SRS.

        Corre en segundo plano. Espera EXTRACCION_RETRASO_SEG antes de llamar al
        extractor para no compartir ventana de tokens/min con la despedida.
        Se lleva una copia de mensajes/foco: una sesión nueva puede empezar
        durante la espera y pisar self.*."""
        if not self.session_id:
            return
        session_id = self.session_id
        mensajes = list(self.mensajes)
        foco_nuevos = list(self._foco_nuevos)
        foco_unidad = self._foco_unidad
        self.session_id = None  # liberar ya: la sesión siguiente puede abrir mientras esperamos

        self._dormir(EXTRACCION_RETRASO_SEG)

        try:
            self._ejecutar_extraccion(session_id, mensajes, foco_nuevos, foco_unidad)
        except Exception as e:
            print(f"⚠️ Error inesperado en extracción de sesión {session_id}: {e}")
            try:
                self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
            except Exception:
                pass

    def _dormir(self, segundos: int):
        """Pausa cooperativa: usa socketio.sleep si existe (en la simulación es
        un no-op), si no time.sleep. Nunca propaga excepciones."""
        if not segundos or segundos <= 0:
            return
        dormir = getattr(self.socketio, "sleep", None) or time.sleep
        try:
            dormir(segundos)
        except Exception:
            pass

    def _ejecutar_extraccion(self, session_id: int, mensajes=None,
                             foco_nuevos=None, foco_unidad=None):
        # Sin argumentos → usa el estado vivo (call sites de tests). Con ellos →
        # la instantánea que tomó cerrar_sesion_y_extraer antes de esperar.
        mensajes = self.mensajes if mensajes is None else mensajes
        if not any(m["role"] == "user" for m in mensajes):
            # Solo el saludo de apertura: no hay nada que extraer.
            self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
            return

        foco_nuevos = list(self._foco_nuevos if foco_nuevos is None else foco_nuevos)
        unidad = (self._foco_unidad if foco_unidad is None else foco_unidad) or {}
        can_dos_activos = unidad.get("can_dos", []) if isinstance(unidad, dict) else []

        # Persistir aquí los ítems nuevos de la sesión.
        for nuevo in foco_nuevos:
            try:
                self.jap_memory.add_item(
                    nuevo["kind"], nuevo["jp"],
                    reading=nuevo.get("reading"),
                    meaning=nuevo.get("meaning"),
                    tipo=nuevo.get("tipo"),
                    session_id=session_id,
                )
            except Exception as e:
                print(f"⚠️ Error persistiendo ítem nuevo '{nuevo['jp']}': {e}")

        transcript = self._construir_transcript(mensajes)

        # Determinista, no depende de ningún LLM: cuenta como "usado en sensei"
        # cualquier palabra/gramática de la BD que aparezca en el transcript.
        try:
            self.jap_memory.marcar_usos_en_sensei(transcript)
        except Exception as e:
            print(f"⚠️ Error marcando usos en sensei: {e}")

        # Nivel 1: resumen en texto libre con cualquier modelo disponible.
        # Se guarda siempre para que la próxima sesión tenga continuidad aunque
        # la extracción completa no sea posible.
        summary_basico = self._extraer_resumen_basico(transcript)

        # Nivel 2: extracción completa. El extractor califica los CAN-DOS ACTIVOS
        # de la unidad abierta (se los pasamos con id + texto), no ítems SRS.
        # Solo con el modelo principal (strict=True): los alternativos producen
        # JSON con japonés corrupto y notas de can-do inventadas que contaminan la
        # BD. Si el modelo fuerte no está disponible, NO se toca ningún can-do
        # (guardrail más abajo): mejor perder la calificación de una sesión que
        # corromper el progreso con un modelo flojo.
        self._dormir(EXTRACCION_PAUSA_LLAMADAS_SEG)  # separa esta llamada del resumen

        if can_dos_activos:
            bloque_can_dos = "CAN-DOS ACTIVOS:\n" + "\n".join(
                f"  - {cd['id']}: {cd['texto']}" for cd in can_dos_activos
            ) + "\n\n"
        else:
            bloque_can_dos = ""
        historial = [
            {"role": "system", "content": _EXTRACCION_PROMPT},
            {"role": "user", "content": f"{bloque_can_dos}Conversación:\n{transcript}"},
        ]

        data = None
        try:
            texto = self._llamar_extractor(historial)
            data = self._parsear_json_sesion(texto)
        except Exception as e:
            print(f"⚠️ Error en extractor (intento 1): {e}")

        if data is None:
            print("⚠️ JSON inválido / modelo no disponible (intento 1). Reintentando…")
            self._dormir(EXTRACCION_PAUSA_LLAMADAS_SEG)  # deja que la ventana tokens/min se vacíe
            historial_retry = historial + [
                {"role": "user", "content": "Devuelve SOLO el JSON válido, sin ningún texto adicional."},
            ]
            try:
                texto = self._llamar_extractor(historial_retry)
                data = self._parsear_json_sesion(texto)
            except Exception as e:
                print(f"⚠️ Error en extractor (intento 2): {e}")

        if data is None:
            # Guardrail: el modelo fuerte no respondió (rate limit o JSON inválido
            # dos veces). NO se cae a modelos de reserva para calificar can-dos —
            # producen japonés sucio y calificaciones inventadas que corrompen la
            # BD. Solo se guarda el resumen básico para dar continuidad; los
            # can-dos se quedan como estaban y se recalifican la próxima sesión.
            print(f"⚠️ Extracción completa no disponible (sesión {session_id}). "
                  f"No se toca can_do_progreso.")
            self.jap_memory.guardar_resumen_sesion(session_id, summary=summary_basico)
            return

        # Qué devolvió el extractor de verdad para cada can-do — sin esto, un
        # can-do que se queda sin fila en can_do_progreso (omitido, o
        # "no_intentado") es indistinguible en el log de uno que sí se calificó;
        # hay que adivinarlo mirando la BD a mano.
        print(f"🧾 Extractor (sesión {session_id}) can_dos: "
              f"{[(cd.get('id'), cd.get('resultado')) for cd in data.get('can_dos', [])]}")

        # Ítems nuevos que introdujo la sesión: se registran en la BD de vocab/gram
        # (su progreso SRS ya no lo mueve el profesor — lo hará el juego web).
        for item in data.get("new_items", []):
            jp = (item.get("jp") or "").strip()
            es = (item.get("es") or "").strip()
            category = (item.get("category") or "vocabulario").lower()
            if not jp:
                continue
            kind = "gramatica" if "gram" in category else "vocabulario"
            try:
                self.jap_memory.add_item(kind, jp, meaning=es, session_id=session_id)
            except Exception as e:
                print(f"⚠️ Error añadiendo ítem '{jp}': {e}")

        # Calificar can-dos: el extractor solo devuelve los de la unidad abierta.
        # 'no_intentado' no cambia estado (lo decide set_can_do). La evidencia
        # (cita textual) se guarda como nota del can-do.
        ids_validos = {cd["id"] for cd in can_dos_activos}
        ids_calificados = set()
        for cd in data.get("can_dos", []):
            cid = (cd.get("id") or "").strip()
            resultado = (cd.get("resultado") or "").strip().lower()
            if not cid or resultado not in _RESULTADOS_CAN_DO:
                continue
            if ids_validos and cid not in ids_validos:
                print(f"⚠️ Can-do '{cid}' no está entre los activos de la sesión; ignorado.")
                continue
            ids_calificados.add(cid)
            evidencia = (cd.get("evidencia") or "").strip() or None
            try:
                self.jap_memory.set_can_do(cid, resultado, session_id, nota=evidencia)
            except Exception as e:
                print(f"⚠️ Error registrando can-do '{cid}': {e}")
        # El extractor puede devolver JSON válido pero incompleto (se le acaban
        # los tokens a media lista): esto deja constancia en vez de fallar en
        # silencio, para no tener que adivinarlo mirando la BD a mano otra vez.
        sin_calificar = ids_validos - ids_calificados
        if sin_calificar:
            print(f"⚠️ El extractor no calificó estos can-dos activos "
                  f"(sesión {session_id}): {', '.join(sorted(sin_calificar))}")

        self.jap_memory.guardar_resumen_sesion(
            session_id,
            summary=data.get("summary") or summary_basico or None,
            # Lo que Kaito decidió no corregir en el momento: lo recupera
            # la próxima sesión desde RECUERDAS_DE_LAURA.
            errors_noted="; ".join(
                e.strip() for e in data.get("sin_corregir", []) if e and e.strip()
            ),
            # Fase 15: cómo va Laura como alumna. Si no viene, se guarda vacía.
            nota_profe=(data.get("nota_profe") or "").strip(),
        )
        # Memoria episódica: lo que Laura contó de su vida, y lo que Kaito
        # afirmó de sí mismo (para que no se contradiga entre sesiones).
        self.jap_memory.guardar_episodios(session_id, data.get("episodios", []))
        self.jap_memory.guardar_anecdotas_kaito(session_id, data.get("kaito_dijo", []))

    def _construir_transcript(self, mensajes=None) -> str:
        lines = []
        for m in (self.mensajes if mensajes is None else mensajes):
            rol = "Profesor" if m["role"] == "assistant" else "Laura"
            lines.append(f"{rol}: {m['content']}")
        return "\n".join(lines)

    def _extraer_resumen_basico(self, transcript: str) -> str:
        """Resumen en texto libre usando cualquier modelo disponible.

        No requiere JSON ni japonés correcto — sirve de continuidad mínima
        para la próxima sesión cuando la extracción completa no está disponible.
        """
        historial = [
            {"role": "system", "content": (
                "Resume en 2-3 frases qué vocabulario y estructuras japonesas "
                "se trabajaron en esta clase. Menciona las palabras o expresiones "
                "en japonés que aparecieron. Responde solo en español."
            )},
            {"role": "user", "content": f"Conversación:\n{transcript}"},
        ]
        try:
            return self.provider.completar(historial, max_tokens=150)
        except Exception as e:
            print(f"⚠️ No se pudo generar resumen básico: {e}")
            return None

    def _llamar_extractor(self, historial: list, strict: bool = True) -> str:
        # strict=True: solo el modelo del sensei — es el que da japonés limpio en
        # el JSON. Si está en rate limit se reintenta con strict=False (cadena de
        # reserva): un new_item con japonés algo sucio se puede corregir; perder
        # la calificación de can-dos de toda la sesión, no.
        # max_tokens=2000: una unidad con 5 can-dos + ítems nuevos + episodios en
        # el mismo JSON no cabía en 1000 y el modelo se dejaba can-dos sin
        # calificar sin que saltara ningún error (JSON válido, solo incompleto).
        return self.provider.completar(
            historial,
            max_tokens=2000,
            response_format={"type": "json_object"},
            strict=strict,
            reasoning_effort="low",
        )

    def _parsear_json_sesion(self, texto: str):
        texto = re.sub(r"```(?:json)?\s*", "", texto).replace("```", "").strip()
        try:
            data = json.loads(texto)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", texto, re.DOTALL)
            if not m:
                return None
            try:
                data = json.loads(m.group())
            except json.JSONDecodeError:
                return None
        if not isinstance(data, dict):
            return None
        data.setdefault("summary", "")
        data.setdefault("can_dos", [])
        data.setdefault("new_items", [])
        data.setdefault("sin_corregir", [])
        data.setdefault("episodios", [])
        data.setdefault("kaito_dijo", [])
        return data


if __name__ == "__main__":
    # _acotar_japones a nivel bajo: una cola de conjugación CORTA y SOLA
    # (【見ました】, 【でした】) es la gramática que se está enseñando y se deja;
    # una frase tema+comentario, aunque quepa en pocos caracteres
    # (【何か食べましたか】), se sigue recortando.
    assert _acotar_japones("【見ました】", 1) == "【見ました】"
    assert _acotar_japones("【のみました】", 1) == "【のみました】"
    assert _acotar_japones("【でした】", 1) == "【でした】"
    assert _acotar_japones("【何か食べましたか】", 1) == ""
    assert _acotar_japones("【きのうは休みでした】", 1) == ""
    # Expresión fija de la lista blanca: se deja aunque lleve ます/ください.
    assert _acotar_japones("【もう一度お願いします】", 1) == "【もう一度お願いします】"

    # Bug real (sesión de prueba de 20 turnos): un verbo con adverbio, sin
    # ninguna partícula que enganche un argumento, se comía entero por pasar
    # de _LARGO_MAX_COLA_VERBAL aunque NO fuera tema+comentario — dejaba
    # "la frase queda ****" hablado, y ni el reintento del juez lo arreglaba
    # (_acotar_japones se lo volvía a comer igual). Ahora se deja: no hay
    # は/が/を/に/で ni una か final, así que no es una frase, es solo el
    # verbo que tocaba enseñar.
    assert _acotar_japones("【早く起きました】", 1) == "【早く起きました】"
    assert _acotar_japones("【べんきょうしました】", 1) == "【べんきょうしました】"
    # En cambio, con partícula de argumento SÍ se sigue recortando aunque
    # pese lo mismo que el caso de arriba.
    assert _acotar_japones("【コーヒーを飲みました】", 1) == ""
    print("✅ _acotar_japones OK")

    # _extraer_frase_objetivo: un verbo diccionario corto y kanji-denso por
    # proporción (【飲む】 = 1 kanji en 2 caracteres) es un candidato válido a
    # objetivo, no "descripción colada" — si se descarta, el heurístico cae a
    # una frase objetivo ANTERIOR de la misma respuesta y Azure puntúa el
    # turno siguiente contra la frase equivocada.
    texto = (
        "Así que cuando decimos 【きのうは】 【やすみでした】 estamos diciendo eso. "
        "Ahora, combina lo que ya sabes y di \"ayer bebí café\" usando la forma "
        "pasada del verbo 【飲む】. Repite la frase completa, por favor."
    )
    assert _extraer_frase_objetivo(texto) == "飲む", _extraer_frase_objetivo(texto)

    # "¿Cómo dirías X usando 【partícula】?" es pregunta ABIERTA: Laura tiene
    # que construir la frase, 【ます】 es solo la pista. No hay objetivo
    # literal que puntuar — si lo hubiera, Azure evaluaría su intento contra
    # la partícula suelta en vez de contra lo que ella dijo de verdad.
    texto_abierto = (
        "¡Genial, suena muy natural! Ahora, vamos a practicar una acción "
        "cotidiana. ¿Cómo dirías \"Cada mañana bebo café\" usando la forma "
        "【ます】? Intenta armar la frase en japonés."
    )
    assert _extraer_frase_objetivo(texto_abierto) is None, _extraer_frase_objetivo(texto_abierto)
    print("✅ _extraer_frase_objetivo OK")
