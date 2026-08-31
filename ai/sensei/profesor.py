"""Clase ProfesorJapones: orquestador del modo sensei.

Estado propio, historial independiente del de Brain, integración
de SRS (Fase 1) y currículo (Fase 2).
"""

import json
import re
import threading
from datetime import datetime

from ai.prompts import cargar_prompt
from ai.sensei.curriculum import siguiente_items_nuevos
from core.config import (
    MAX_ITEMS_NUEVOS,
    MAX_TOKENS_SENSEI,
    REASONING_EFFORT_SENSEI,
    TEMPERATURE_SENSEI,
    THROTTLE_DUE,
)

# ── Constantes ────────────────────────────────────────────────────────────────

MAX_TURNOS = 10  # pares user/assistant conservados en el contexto del LLM

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

SALUDOS_CONV = [
    "¡Modo charla activado! Nada de clase, solo tú, yo y 【にほんご】. ¿Qué tal el día?",
    "¡Modo colega ON! Olvida que soy un profesor, soy tu amigo que resulta que habla japonés. 【はじめよう！】",
    "Ahora sí, modo conversación. Sin drills, sin temario. Solo 【おしゃべり】. ¿Por dónde empezamos?",
    "Cambiando al modo charla... Hecho. Ahora dime algo interesante. En español o en 【にほんご】, lo que te salga.",
    "¡Modo charla! Prometido: cero ejercicios. Solo quiero saber qué has hecho hoy. 【どうだった？】",
]

CAMBIO_A_ESTUDIO = [
    "¡Modo estudio activado! Volvemos al temario. 【さあ、べんきょうしましょう！】",
    "De acuerdo, ponemos el modo serio. Un poco. 【がんばろう！】",
    "Modo clase activado. Aunque tampoco me voy a poner muy formal, que me conozco. 【はじめましょう！】",
]

_QUALITY_MAP = {"bien": 5, "duda": 3, "mal": 1}

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
# Señales de que el turno espera una respuesta EN ESPAÑOL (sí/no, comprensión):
# ahí NO hay frase objetivo y no debe evaluarse pronunciación.
_PISTAS_COMPRENSION = (
    "sí o no", "si o no", "responde sí", "responde si", "contesta sí", "contesta si",
    "¿entiendes", "¿lo entiendes", "¿comprendes", "¿qué significa", "¿que significa",
    "¿sabes qué", "¿sabes que", "¿verdad?", "¿de acuerdo?", "¿vale?", "en español",
)


def _limpiar_objetivo(s: str) -> str:
    return (s or "").strip("　 \t\n、。・…！？!?「」『』()（）").replace("【", "").replace("】", "")


def _extraer_frase_objetivo(texto: str):
    """La frase que el profesor pide REPETIR a Laura, para comparar contra ella en
    la evaluación de pronunciación del turno siguiente.

    Devuelve None salvo que el turno pida producción explícita ('repite',
    'cómo dirías'…) y NO sea una pregunta de comprensión / sí-no (en ese caso
    Laura responde en español y no hay que puntuar nada)."""
    if not texto:
        return None

    bajo = texto.lower()
    if any(p in bajo for p in _PISTAS_COMPRENSION):
        return None
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
        self.modo_conv = False
        self.timer = None
        self.session_id = None
        self.mensajes = []          # historial propio de la sesión sensei (solo user/assistant)
        # Frase que el profesor pidió repetir en su último turno (ReferenceText de Azure).
        self.ultima_frase_objetivo = None

        # Estado del último FOCO (para cierre resiliente en Fase 4)
        self._foco_due_vocab = []
        self._foco_due_gram = []
        self._foco_nuevos = []

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def set_modo_conv(self, conv: bool):
        self.modo_conv = conv

    def entrar(self, conv: bool = False):
        """Activa el modo sensei y abre una sesión en la BD."""
        self.activo = True
        self.modo_conv = conv
        self.mensajes = []
        self.ultima_frase_objetivo = None
        self._foco_due_vocab = []
        self._foco_due_gram = []

        # Los ítems nuevos se eligen UNA vez por sesión, no una por turno.
        # Se persisten al cerrar (_ejecutar_extraccion), no aquí.
        due = self.jap_memory.resumen_perfil()["due_count"]
        self._foco_nuevos = (
            [] if due >= THROTTLE_DUE
            else siguiente_items_nuevos(self.jap_memory, MAX_ITEMS_NUEVOS)
        )

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
        self.cerrar_sesion_y_extraer()
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
        nombre_prompt = "profesor_japones_conv" if self.modo_conv else "profesor_japones"
        try:
            prompt_base = cargar_prompt(nombre_prompt)
        except Exception as e:
            print(f"⚠️ No se pudo cargar prompt {nombre_prompt}: {e}")
            prompt_base = "Eres un profesor de japonés amable. Habla en japonés con 【】."

        recuerdas, foco = self._montar_estado()

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
                max_tokens=MAX_TOKENS_SENSEI,
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

    def _montar_estado(self) -> tuple:
        """Devuelve (recuerdas_de_laura, foco_de_hoy) como par de strings."""
        # ── RECUERDAS_DE_LAURA ─────────────────────────────────────────────
        try:
            perfil_general = self.memory.obtener_perfil()
        except Exception:
            perfil_general = ""

        perfil_jap = self.jap_memory.resumen_perfil()
        lineas_r = [perfil_general] if perfil_general else []
        lineas_r.append(f"Palabras en cola de repaso (SRS): {perfil_jap['due_count']}")

        if perfil_jap.get("vocab_by_status"):
            estados = ", ".join(
                f"{k}: {v}" for k, v in perfil_jap["vocab_by_status"].items()
            )
            lineas_r.append(f"Vocabulario por estado: {estados}")

        if perfil_jap.get("last_session_summary"):
            lineas_r.append(f"Última sesión: {perfil_jap['last_session_summary']}")

        if perfil_jap.get("weak_points"):
            puntos = ", ".join(
                f"{w['word']} ({w['errors']} errores)" for w in perfil_jap["weak_points"]
            )
            lineas_r.append(f"Puntos débiles: {puntos}")

        recuerdas_de_laura = "\n".join(lineas_r)

        # ── FOCO_DE_HOY ────────────────────────────────────────────────────
        due_vocab = self.jap_memory.get_due_items(5, kind="vocabulario")
        due_gram = self.jap_memory.get_due_items(3, kind="gramatica")

        due_count = perfil_jap["due_count"]
        nuevos = self._foco_nuevos      # elegidos en entrar(), solo lectura aquí

        self._foco_due_vocab = due_vocab
        self._foco_due_gram = due_gram

        lineas_f = []
        if due_vocab:
            lineas_f.append("Vocabulario para repasar hoy:")
            for item in due_vocab:
                jp = item.get("jp") or item.get("word", "")
                meaning = item.get("meaning", "")
                lineas_f.append(f"  - 【{jp}】 {meaning}")

        if due_gram:
            lineas_f.append("Gramática para repasar hoy:")
            for item in due_gram:
                jp = item.get("jp") or item.get("grammar_point", "")
                meaning = item.get("meaning") or item.get("description", "")
                lineas_f.append(f"  - 【{jp}】 {meaning}")

        if nuevos:
            lineas_f.append(f"Ítems nuevos a introducir ({len(nuevos)}):")
            for nuevo in nuevos:
                lineas_f.append(
                    f"  - 【{nuevo['jp']}】 — {nuevo['meaning']}"
                    f" (unidad: {nuevo['unidad']})"
                )
        elif due_count >= THROTTLE_DUE:
            lineas_f.append(
                f"Carga alta de repasos ({due_count} pendientes): no introducir ítems nuevos del temario hoy. "
                f"Consolida los repasos. (Si Laura pide algo concreto, enséñalo igualmente.)"
            )

        if not lineas_f:
            lineas_f.append(
                "No hay ítems pendientes. Conversa libremente en japonés sobre cualquier tema."
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

        # Copia local: una sesión nueva puede pisar self._foco_nuevos mientras
        # esta extracción corre en segundo plano (igual que session_id).
        foco_nuevos = list(self._foco_nuevos)

        # Persistir aquí los ítems nuevos de la sesión, antes de cualquier
        # review(): sin esto get_item_id() devuelve None y las dos rutas de
        # calificación (rescate y aprobado de oficio) quedarían mudas.
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

        # Nivel 2: extracción completa de vocabulario y gramática.
        # Solo con el modelo principal (strict=True) — los alternativos producen
        # JSON con japonés corrupto que contamina la BD.
        historial = [
            {"role": "system", "content": _EXTRACCION_PROMPT},
            {"role": "user", "content": f"Conversación:\n{transcript}"},
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
            print(f"⚠️ Extracción completa no disponible (sesión {session_id}). Aplicando review de rescate.")
            # ponytail: review con quality=3 (duda) para marcar los ítems del FOCO como vistos
            for item in self._foco_due_vocab:
                try:
                    self.jap_memory.review(item["id"], 3, "vocabulario")
                except Exception:
                    pass
            for item in self._foco_due_gram:
                try:
                    self.jap_memory.review(item["id"], 3, "gramatica")
                except Exception:
                    pass
            self.jap_memory.guardar_resumen_sesion(session_id, summary=summary_basico)
            return

        # Añadir ítems nuevos primero para que review los encuentre si son de esta sesión
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

        words_learned = 0
        grammar_list = []
        errors_list = []

        for r in data.get("reviewed", []):
            jp = (r.get("jp") or "").strip()
            resultado = (r.get("resultado") or "").lower()
            quality = _QUALITY_MAP.get(resultado)
            if not jp or quality is None:
                continue
            item_id = self.jap_memory.get_item_id(jp, "vocabulario")
            kind = "vocabulario"
            if item_id is None:
                item_id = self.jap_memory.get_item_id(jp, "gramatica")
                kind = "gramatica"
            if item_id is None:
                print(f"⚠️ Ítem '{jp}' no encontrado en BD para review.")
                continue
            try:
                self.jap_memory.review(item_id, quality, kind)
                if kind == "vocabulario":
                    words_learned += 1
                else:
                    grammar_list.append(jp)
                if quality < 3:
                    errors_list.append(jp)
            except Exception as e:
                print(f"⚠️ Error en review de '{jp}': {e}")

        # Ítems nuevos del FOCO que el extractor no capturó: mínimo reps=1 (duda)
        reviewed_jp = {(r.get("jp") or "").strip() for r in data.get("reviewed", [])}
        for nuevo in foco_nuevos:
            if nuevo["jp"] not in reviewed_jp:
                item_id = self.jap_memory.get_item_id(nuevo["jp"], nuevo["kind"])
                if item_id is not None:
                    try:
                        self.jap_memory.review(item_id, 3, nuevo["kind"])
                    except Exception:
                        pass

        self.jap_memory.guardar_resumen_sesion(
            session_id,
            summary=data.get("summary") or summary_basico or None,
            words_learned=words_learned,
            grammar_practiced=", ".join(grammar_list),
            errors_noted=", ".join(errors_list),
        )

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
        data.setdefault("reviewed", [])
        data.setdefault("new_items", [])
        return data
