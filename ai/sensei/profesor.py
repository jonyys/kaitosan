"""Clase ProfesorJapones: orquestador del modo sensei.

Estado propio, historial independiente del de Brain, integración
de SRS (Fase 1) y currículo (Fase 2).
"""

import json
import re
import threading
from datetime import datetime

from ai.prompts import cargar_prompt
from ai.sensei.curriculum import (
    CURRICULUM,
    ITEM_POR_JP,
    siguiente_items_nuevos,
    unidad_actual,
)
from core.config import (
    CHEQUEO_OXIDO_CADA,
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

_MARCA_ESTADO = {"sabido": "[sabida]", "en_progreso": "[en progreso]", "nuevo": "[nueva]"}

SALUDOS = [
    "Modo Sensei activado! 【こんにちは、ラウラさん。おげんきですか。】",
    "Modo Sensei activado! 【おはようございます、ラウラさん。きょうはなにをしたいですか。】",
    "Modo Sensei activado! 【こんばんは、ラウラさん。げんきですか。】",
    "Modo Sensei activado! 【やあ、ラウラさん。ちょうしはどうですか。】",
    "Modo Sensei activado! 【ラウラさん、こんにちは。にほんごをべんきょうしましょう。】",
]

DESPEDIDAS = [
    "【またね、ラウラさん】",
    "【じゃあね、ラウラさん。また会いましょう】",
    "【おつかれさまでした。またね】",
    "【さようなら、ラウラさん。また今度】",
    "【バイバイ、ラウラさん。気をつけてね】",
]

# Resultados que el extractor puede devolver por can-do (Fase 08).
_RESULTADOS_CAN_DO = {"conseguido", "parcial", "no_intentado", "error"}

# Bloques 【...】 que contienen al menos un kana/kanji (con o sin puntuación dentro).
_RE_BLOQUE_JP = re.compile(r'【([^【】]*[぀-ゟ゠-ヿ一-鿿][^【】]*)】')
# Cualquier carácter japonés.
_RE_JP_CHAR = re.compile(r'[぀-ゟ゠-ヿ一-鿿]')
# Texto entre comillas japonesas 「…」 / 『…』.
_RE_ENTRECOMILLADO = re.compile(r'[「『]([^「」『』]*)[」『』]')

# Frases de ánimo/muletillas: NO son algo que Laura deba repetir.
_FRASES_ANIMO = {
    "よくできました", "いいね", "すごい", "じょうず", "じょうずです", "がんばって",
    "がんばろう", "もういちど", "もういちどおねがいします", "おねがいします",
    "そうです", "せいかい", "だいじょうぶ", "オーケー", "はい", "ええ",
}
# Señales de que el turno pide PRODUCIR una frase japonesa concreta.
_PISTAS_PRODUCCION = (
    "repit", "repít", "repet",  # repite, repítela, repíteme, repetir, repetirme…
    "di conmigo", "dilo", "dila", "di la frase",
    "cómo dirías", "como dirias", "cómo se dice", "como se dice",
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

    turnos 1-2 → calentamiento (charla, deberes, cómo está Laura; temario aún no).
    Laura se despide → cierre (el prompt ya trae el ritual). Resto → foco."""
    if ultimo_de_laura and any(
        p in ultimo_de_laura.lower() for p in _DESPEDIDAS_LAURA
    ):
        return "FASE DE LA SESIÓN: cierre"
    if turno <= 2:
        return (
            "FASE DE LA SESIÓN: calentamiento — (turnos 1-2: charla, deberes, "
            "cómo está Laura; aún no metas ejercicio de temario)"
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
    entrecomillados = [e for e in entrecomillados if _RE_JP_CHAR.search(e) and len(e) >= 3]
    if entrecomillados:
        return entrecomillados[-1]

    bloques = [_limpiar_objetivo(b) for b in _RE_BLOQUE_JP.findall(texto)]
    bloques = [b for b in bloques if b and b not in _FRASES_ANIMO]
    if not bloques:
        return None

    # El prompt pide terminar el turno con la frase objetivo como último bloque
    # 【】 ("Repite: 【…】"). Así que el objetivo es el ÚLTIMO bloque, no el más
    # largo (antes cogía 【お元気ですか】 en vez de 【晴れた】 por tener más letras).
    return bloques[-1]


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

        # Llamar al LLM
        try:
            respuesta = self.provider.completar(
                historial_sensei,
                # Techo alto para todos los turnos: el desglose gramatical es
                # justo lo que se quedaba a medias. La selección por tipo de
                # turno (MAX_TOKENS_SENSEI para los normales) espera a que el
                # prompt distinga registros.
                max_tokens=MAX_TOKENS_EXPLICACION,
                temperature=TEMPERATURE_SENSEI,
                reasoning_effort=REASONING_EFFORT_SENSEI,
            )
        except Exception as e:
            print(f"❌ Error LLM en modo sensei: {e}")
            return "【ちょっとまってください。】 Un momento, hubo un problema técnico."

        # El modelo a veces devuelve vacío (todo el presupuesto se fue en
        # razonamiento). No guardamos el turno y pedimos que repita.
        if not respuesta or not respuesta.strip():
            print("⚠️ Respuesta vacía del LLM en modo sensei")
            return "Perdona, se me ha cruzado un cable. ¿Me lo repites? 【もういちど おねがいします】"

        # Guardar turno limpio en el historial propio
        self.mensajes.append({"role": "user", "content": mensaje})
        self.mensajes.append({"role": "assistant", "content": respuesta})

        # Frase objetivo para la evaluación de pronunciación del PRÓXIMO turno.
        self.ultima_frase_objetivo = _extraer_frase_objetivo(respuesta)
        if self.ultima_frase_objetivo:
            print(f"🎯 Frase objetivo: {self.ultima_frase_objetivo}")

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

        # Fase 16: los deberes de la última sesión entran PRIMEROS en el FOCO,
        # con marca para que Kaito pregunte qué tal fueron antes de nada. El
        # getter solo devuelve los de la última sesión cerrada, así que esto
        # sale una única sesión (la inmediatamente posterior) y luego se apaga.
        deberes = perfil_jap.get("deberes_ultima_sesion")
        if deberes:
            lineas_f.append(
                "DEBERES DE LA SEMANA PASADA (pregúntale qué tal le fueron antes "
                f"de entrar en materia): {deberes}"
            )

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
        activo = next(
            (cd for cd in can_dos
             if prog.get(cd["id"], {}).get("estado") != "dominado"),
            None,
        )
        if activo:
            lineas_f.append(f"Can-do de hoy: {activo['texto']}")
            items = unidad.get("items", [])[:ITEMS_CANDO_FOCO]
            if items:
                lineas_f.append(
                    "  lo que necesita (las [sabida] úsalas en japonés directamente):"
                )
                estados_it = self.jap_memory.estado_items_bulk(
                    (it["jp"], it["kind"]) for it in items
                )
                # Marca intra-sesión: si Kaito ya citó 【jp】 en un turno suyo de
                # esta sesión, un ítem que aún sería [nueva] pasa a
                # [trabajándose hoy] (no repitas la glosa, pero sigue en el FOCO).
                # Se busca el bloque 【jp】 con corchetes, no el jp suelto, para no
                # dar falsos positivos con ítems de una sola kana (「て」, 「に」).
                dicho_por_kaito = "\n".join(
                    m["content"] for m in self.mensajes if m["role"] == "assistant"
                )
                for it in items:
                    kind = "gramatica" if it["kind"] == "gramatica" else "vocabulario"
                    estado = estados_it.get((it["jp"], kind), "nuevo")
                    if estado == "nuevo" and f"【{it['jp']}】" in dicho_por_kaito:
                        marca = "[trabajándose hoy]"
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

        nuevos = self._foco_nuevos      # elegidos en entrar(), solo lectura aquí
        if nuevos:
            lineas_f.append(f"Ítems nuevos a introducir ({len(nuevos)}):")
            for nuevo in nuevos:
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

        # (la línea de deberes de Fase 16, si está, no cuenta como contenido)
        if not [ln for ln in lineas_f
                if not ln.startswith("DEBERES DE LA SEMANA")
                and not ln.startswith("FASE DE LA SESIÓN")]:
            lineas_f.append(
                "Sin unidad abierta. Conversa libremente en japonés sobre cualquier tema."
            )

        foco_de_hoy = "\n".join(lineas_f)
        return recuerdas_de_laura, foco_de_hoy

    # ── Cierre de sesión y extracción (Fase 5) ───────────────────────────────

    def cerrar_sesion_y_extraer(self):
        """Extrae el aprendizaje de la sesión con LLM ligero y actualiza el SRS."""
        if not self.session_id:
            return
        session_id = self.session_id
        self.session_id = None  # liberar antes; la extracción puede tardar varios segundos
        try:
            self._ejecutar_extraccion(session_id)
        except Exception as e:
            print(f"⚠️ Error inesperado en extracción de sesión {session_id}: {e}")
            try:
                self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
            except Exception:
                pass

    def _ejecutar_extraccion(self, session_id: int):
        if not self.mensajes:
            self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
            return

        # Copia local: una sesión nueva puede pisar self._foco_* mientras
        # esta extracción corre en segundo plano (igual que session_id).
        foco_nuevos = list(self._foco_nuevos)
        unidad = self._foco_unidad or {}
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

        transcript = self._construir_transcript()

        # Nivel 1: resumen en texto libre con cualquier modelo disponible.
        # Se guarda siempre para que la próxima sesión tenga continuidad aunque
        # la extracción completa no sea posible.
        summary_basico = self._extraer_resumen_basico(transcript)

        # Nivel 2: extracción completa. El extractor califica los CAN-DOS ACTIVOS
        # de la unidad abierta (se los pasamos con id + texto), no ítems SRS.
        # Solo con el modelo principal (strict=True) — los alternativos producen
        # JSON con japonés corrupto que contamina la BD.
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
            print("⚠️ JSON inválido en extracción (intento 1). Reintentando…")
            historial_retry = historial + [
                {"role": "user", "content": "Devuelve SOLO el JSON válido, sin ningún texto adicional."},
            ]
            try:
                texto = self._llamar_extractor(historial_retry)
                data = self._parsear_json_sesion(texto)
            except Exception as e:
                print(f"⚠️ Error en extractor (intento 2): {e}")

        if data is None:
            # Extractor caído: no se toca ningún can-do, solo se guarda el
            # resumen básico para dar continuidad a la próxima sesión.
            print(f"⚠️ Extracción completa no disponible (sesión {session_id}). No se tocan can-dos.")
            self.jap_memory.guardar_resumen_sesion(session_id, summary=summary_basico)
            return

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
        for cd in data.get("can_dos", []):
            cid = (cd.get("id") or "").strip()
            resultado = (cd.get("resultado") or "").strip().lower()
            if not cid or resultado not in _RESULTADOS_CAN_DO:
                continue
            if ids_validos and cid not in ids_validos:
                print(f"⚠️ Can-do '{cid}' no está entre los activos de la sesión; ignorado.")
                continue
            evidencia = (cd.get("evidencia") or "").strip() or None
            try:
                self.jap_memory.set_can_do(cid, resultado, session_id, nota=evidencia)
            except Exception as e:
                print(f"⚠️ Error registrando can-do '{cid}': {e}")

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
            # Fase 16: la tarea que Kaito propuso al despedirse. Si no viene, ''.
            deberes=(data.get("deberes") or "").strip(),
        )
        # Memoria episódica: lo que Laura contó de su vida, y lo que Kaito
        # afirmó de sí mismo (para que no se contradiga entre sesiones).
        self.jap_memory.guardar_episodios(session_id, data.get("episodios", []))
        self.jap_memory.guardar_anecdotas_kaito(session_id, data.get("kaito_dijo", []))

    def _construir_transcript(self) -> str:
        lines = []
        for m in self.mensajes:
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

    def _llamar_extractor(self, historial: list) -> str:
        # strict=True: si el modelo principal está en rate limit no usamos fallback —
        # un modelo alternativo produce JSON corrupto que contamina la BD.
        return self.provider.completar(
            historial,
            max_tokens=1000,
            response_format={"type": "json_object"},
            strict=True,
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
