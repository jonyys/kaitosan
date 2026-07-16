"""Clase ProfesorJapones: orquestador del modo sensei.

Estado propio, historial independiente del de Brain, integración
de SRS (Fase 1) y currículo (Fase 2), y evaluación de pronunciación.
"""

import json
import re
import threading
from datetime import datetime

from ai.sensei.curriculum import siguiente_item_nuevo

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
    '  "reviewed": [{"jp": "<ítem en japonés>", "resultado": "bien|duda|mal"}],\n'
    '  "new_items": [{"category": "vocabulario|gramatica", "jp": "<japonés>", "es": "<español>"}]\n'
    '}\n\n'
    "Reglas:\n"
    "- Incluye SOLO ítems que aparecieron realmente en la conversación.\n"
    "- reviewed: cada ítem que el alumno intentó usar; juzga bien/duda/mal.\n"
    "- new_items: ítems introducidos por primera vez en esta sesión.\n"
    "- Responde SOLO con el JSON, sin markdown ni texto adicional."
)


class ProfesorJapones:

    def __init__(self, jap_memory, provider, provider_ligero, memory, socketio):
        """
        jap_memory      — JapaneseMemory (capa de datos japonés + SRS)
        provider        — proveedor LLM principal (llama-3.3-70b)
        provider_ligero — proveedor LLM ligero (llama-3.1-8b), usado en Fase 5
        memory          — core.memory.Memory (perfil general de Laura)
        socketio        — instancia Flask-SocketIO para emitir eventos
        """
        self.jap_memory = jap_memory
        self.provider = provider
        self.provider_ligero = provider_ligero
        self.memory = memory
        self.socketio = socketio

        self.activo = False
        self.timer = None
        self.session_id = None
        self.mensajes = []          # historial propio de la sesión sensei (solo user/assistant)
        self.ultima_frase_objetivo = None

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def entrar(self):
        """Activa el modo sensei y abre una sesión en la BD."""
        self.activo = True
        self.mensajes = []
        self.ultima_frase_objetivo = None

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
        """Desactiva el modo sensei, cancela el timer y cierra la sesión."""
        if self.timer:
            self.timer.cancel()
            self.timer = None
        self.activo = False
        self.cerrar_sesion_y_extraer()
        self.socketio.emit("modo_sensei", {"activo": False})
        print("🎌 Modo Sensei desactivado")

    def esta_activo(self) -> bool:
        return self.activo

    def _renovar_timer(self):
        """Reinicia el contador de inactividad de 20 minutos."""
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(20 * 60, self.salir)
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

        # Evaluar pronunciación si hay frase objetivo pendiente
        contexto_pronunciacion = ""
        if self.ultima_frase_objetivo:
            try:
                from ai.pronunciation import comparar_pronunciacion
                ev = comparar_pronunciacion(self.ultima_frase_objetivo, mensaje)
                contexto_pronunciacion = (
                    f"\n[Evaluación de pronunciación: {ev['precision']}%. "
                    f"IPA objetivo: {ev['ipa_objetivo']}. "
                    f"IPA hablado: {ev['ipa_hablado']}. "
                    f"Feedback: {ev['feedback']}]"
                )
            except Exception as e:
                print(f"⚠️ Error evaluando pronunciación: {e}")
            self.ultima_frase_objetivo = None

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

        # Mensaje de usuario, con contexto de pronunciación si aplica
        contenido_usuario = mensaje + contexto_pronunciacion if contexto_pronunciacion else mensaje
        historial_sensei.append({"role": "user", "content": contenido_usuario})

        # Llamar al LLM
        try:
            respuesta = self.provider.completar(historial_sensei)
        except Exception as e:
            print(f"❌ Error LLM en modo sensei: {e}")
            return "【ちょっとまってください。】 Un momento, hubo un problema técnico."

        # Guardar turno limpio en el historial propio
        self.mensajes.append({"role": "user", "content": mensaje})
        self.mensajes.append({"role": "assistant", "content": respuesta})

        # Extraer frase objetivo para el siguiente turno
        frase = self._extraer_frase_objetivo(respuesta)
        if frase:
            self.ultima_frase_objetivo = frase

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
        nuevo = siguiente_item_nuevo(self.jap_memory)

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

        if nuevo:
            lineas_f.append(
                f"Ítem nuevo a introducir: 【{nuevo['jp']}】 — {nuevo['meaning']}"
                f" (unidad: {nuevo['unidad']})"
            )

        if not lineas_f:
            lineas_f.append(
                "No hay ítems pendientes. Conversa libremente en japonés sobre cualquier tema."
            )

        foco_de_hoy = "\n".join(lineas_f)
        return recuerdas_de_laura, foco_de_hoy

    def _extraer_frase_objetivo(self, respuesta: str):
        """Extrae frase objetivo para evaluar pronunciación en el turno siguiente."""
        patrones = [
            r"(?:repit[ea]|di|pronuncia)\s+(?:conmigo\s*)?(?::|,)?\s*[「「【]([^」」】]+)[」」】]",
            r"(?:repit[ea]|di|pronuncia)\s+(?:conmigo\s*)?(?::|,)?\s*([぀-ゟ゠-ヿ一-鿿]+)",
        ]
        for patron in patrones:
            match = re.search(patron, respuesta, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

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
            print(f"❌ Extracción fallida (sesión {session_id}). Se guarda sin resumen.")
            self.jap_memory.guardar_resumen_sesion(session_id, summary=None)
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

        self.jap_memory.guardar_resumen_sesion(
            session_id,
            summary=data.get("summary") or None,
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

    def _llamar_extractor(self, historial: list) -> str:
        try:
            return self.provider_ligero.completar(
                historial, response_format={"type": "json_object"}
            )
        except TypeError:
            return self.provider_ligero.completar(historial)

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
