"""Clase ProfesorJapones: orquestador del modo sensei.

Estado propio, historial independiente del de Brain, integración
de SRS (Fase 1) y currículo (Fase 2).
"""

import json
import re
import threading
from datetime import datetime

from ai.sensei.curriculum import siguiente_items_nuevos
from core.config import MAX_ITEMS_NUEVOS, MAX_TOKENS_SENSEI, TEMPERATURE_SENSEI, THROTTLE_DUE

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

_QUALITY_MAP = {"bien": 5, "duda": 3, "mal": 1}

_EXTRACCION_PROMPT = (
    "Eres un extractor de datos de sesiones de japonés.\n"
    "Analiza la conversación y devuelve ÚNICAMENTE un JSON con este esquema exacto:\n\n"
    '{\n'
    '  "summary": "<2-3 frases sobre qué se trabajó en la sesión>",\n'
    '  "reviewed": [{"jp": "<ítem en japonés sin corchetes>", "resultado": "bien|duda|mal"}],\n'
    '  "new_items": [{"category": "vocabulario|gramatica", "jp": "<japonés sin corchetes>", "es": "<español>"}]\n'
    '}\n\n'
    "Reglas:\n"
    "- Incluye SOLO ítems que aparecieron realmente en la conversación.\n"
    "- Los ítems en japonés van sin los corchetes 【】.\n"
    "- reviewed: TODO lo que el alumno intentó producir o practicar, en dos tipos:\n"
    "  * VOCABULARIO: palabras sueltas y expresiones fijas (みず, ありがとう, みずをください…).\n"
    "  * GRAMÁTICA / CONJUGACIÓN: cuando Laura usó un patrón de conjugación o estructura,\n"
    "    añade el PATRÓN CANÓNICO, NO el verbo concreto. Ejemplos:\n"
    "      - dijo 食べた, 行った → jp: '〜た'\n"
    "      - dijo 食べています → jp: '〜ている'\n"
    "      - dijo むずかしくない → jp: '〜くない'\n"
    "      - dijo おいしかった → jp: '〜かった'\n"
    "      - dijo 食べてください → jp: '〜てください'\n"
    "      - usó は/が/を/に en una oración → jp: la partícula (は, が…)\n"
    "    Usa el jp exacto del FOCO si el patrón aparece en él.\n"
    "  Juzga resultado: bien (correcto o casi), duda (intentó con errores), mal (no lo logró).\n"
    "- new_items: vocabulario, expresiones o puntos gramaticales introducidos por primera vez.\n"
    "  Para gramática usa el jp canónico del patrón (〜て, 〜た, る動詞…).\n"
    "- Si el alumno no intentó producir nada, reviewed = [].\n"
    "- Responde SOLO con el JSON, sin markdown ni texto adicional.\n\n"
    "=== EJEMPLO ===\n"
    "FOCO:\n"
    "  Vocabulario para repasar: 【みず】 agua\n"
    "  Gramática para repasar: 【〜てください】 petición formal\n"
    "  Ítem nuevo: 【〜た】 pasado casual\n"
    "Conversación:\n"
    "Profesor: Hoy repasamos 【みず】. Di conmigo.\n"
    "Laura: みず\n"
    "Profesor: 【いいね】! Ahora 【みずをください】.\n"
    "Laura: みずをくなさい\n"
    "Profesor: Casi, es 【みずをください】. ¿Puedes repetirlo?\n"
    "Laura: みずをください\n"
    "Profesor: 【いいね】! Ahora el pasado: ayer comiste, que se dice 【食べた】.\n"
    "Laura: たべた\n"
    "Profesor: 【すごい】! ¿Y bebiste? 【飲んだ】.\n"
    "Laura: のんだ\n"
    "Salida esperada:\n"
    '{\n'
    '  "summary": "Se repasó みず y 〜てください; Laura logró みずをください al segundo intento. '
    'Se introdujo el pasado casual 〜た: acertó 食べた y 飲んだ sin dificultad.",\n'
    '  "reviewed": [\n'
    '    {"jp": "みず", "resultado": "bien"},\n'
    '    {"jp": "〜てください", "resultado": "duda"},\n'
    '    {"jp": "〜た", "resultado": "bien"}\n'
    '  ],\n'
    '  "new_items": [\n'
    '    {"category": "vocabulario", "jp": "みず", "es": "agua"},\n'
    '    {"category": "gramatica", "jp": "〜た", "es": "pasado casual del verbo"}\n'
    '  ]\n'
    '}\n'
    "=== FIN EJEMPLO ==="
)


class ProfesorJapones:

    def __init__(self, jap_memory, provider, memory, socketio):
        """
        jap_memory — JapaneseMemory (capa de datos japonés + SRS)
        provider   — proveedor LLM principal (llama-3.3-70b)
        memory     — core.memory.Memory (perfil general de Laura)
        socketio   — instancia Flask-SocketIO para emitir eventos
        """
        self.jap_memory = jap_memory
        self.provider = provider
        self.memory = memory
        self.socketio = socketio

        self.activo = False
        self.timer = None
        self.session_id = None
        self.mensajes = []          # historial propio de la sesión sensei (solo user/assistant)

        # Estado del último FOCO (para cierre resiliente en Fase 4)
        self._foco_due_vocab = []
        self._foco_due_gram = []
        self._foco_nuevos = []

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def entrar(self):
        """Activa el modo sensei y abre una sesión en la BD."""
        self.activo = True
        self.mensajes = []
        self._foco_due_vocab = []
        self._foco_due_gram = []
        self._foco_nuevos = []

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

    def responder_turno(self, mensaje: str, lento_extra: bool = False) -> str:
        """Genera la respuesta del sensei para un turno.

        Construye el historial desde cero usando el estado actual (SRS +
        currículo) sin tocar el historial de Brain. No lanza excepciones al
        exterior — ante fallos del proveedor devuelve mensaje de error amable.
        """
        from ai.prompts import cargar_prompt  # import diferido para evitar ciclos

        self._renovar_timer()

        # Construir historial del sensei desde cero (sin mutar el de Brain)
        try:
            prompt_base = cargar_prompt("profesor_japones")
        except Exception as e:
            print(f"⚠️ No se pudo cargar prompt profesor_japones: {e}")
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

        historial_sensei.append({"role": "user", "content": mensaje})

        # Llamar al LLM
        try:
            respuesta = self.provider.completar(
                historial_sensei,
                max_tokens=MAX_TOKENS_SENSEI,
                temperature=TEMPERATURE_SENSEI,
            )
        except Exception as e:
            print(f"❌ Error LLM en modo sensei: {e}")
            return "【ちょっとまってください。】 Un momento, hubo un problema técnico."

        # Guardar turno limpio en el historial propio
        self.mensajes.append({"role": "user", "content": mensaje})
        self.mensajes.append({"role": "assistant", "content": respuesta})

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
        if due_count >= THROTTLE_DUE:
            nuevos = []
        else:
            nuevos = siguiente_items_nuevos(self.jap_memory, MAX_ITEMS_NUEVOS)

        # Persistir ítems nuevos en cuanto se seleccionan — add_item es idempotente
        for nuevo in nuevos:
            self.jap_memory.add_item(
                nuevo["kind"], nuevo["jp"],
                reading=nuevo.get("reading"),
                meaning=nuevo.get("meaning"),
                tipo=nuevo.get("tipo"),
                session_id=self.session_id,
            )
        self._foco_due_vocab = due_vocab
        self._foco_due_gram = due_gram
        self._foco_nuevos = nuevos

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
        for nuevo in self._foco_nuevos:
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
            max_tokens=700,
            response_format={"type": "json_object"},
            strict=True,
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
