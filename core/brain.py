import json

from ai.groq_provider import GroqProvider
from ai.prompts import cargar_prompt
from ai.fallback_provider import FallbackProvider

from core.japanese_memory import JapaneseMemory
from core.memory import DB_PATH, Memory
import time
from datetime import datetime
import re as regex

# Limitar tamaño del historial para sesiones largas
MAX_MENSAJES = 20

class Brain:
    def __init__(self, state_manager, socketio):
        self.state = state_manager
        self.socketio = socketio
        self.provider = FallbackProvider(model="llama-3.3-70b-versatile")
        self.router_provider = GroqProvider(model="llama-3.1-8b-instant") # modelo ligero para enrutar
        self.memory = Memory()
        self.jap_memory = JapaneseMemory(DB_PATH)    
        self.session_id = None
        self._iniciar_sesion()
        self.ultimo_agente = "general"
        self.ultima_frase_objetivo = None

    def _iniciar_sesion(self):
        """
        Inicia sesión con:
        - System prompt base
        - Perfil fijo de Laura
        Sin historial de conversaciones (solo cuando lo pida)
        """
        self.session_id = self.memory.iniciar_sesion()

        # System prompt base + perfil de Laura
        system_prompt = cargar_prompt("system_prompt")
        perfil = self.memory.obtener_perfil()

        system_completo = f"{system_prompt}\n\n{perfil}"

        self.historial = [
            {"role": "system", "content": system_completo}
        ]
        print(f"✅ Sesión {self.session_id} iniciada")

    def _detectar_intencion(self, mensaje: str) -> dict:
        # Heurística rápida primero (opcional, la mantienes)

        ultimo_asistente = self._ultimo_contexto_asistente()
        contexto = ""
        if ultimo_asistente:
            contexto = f"Último mensaje del asistente: \"{ultimo_asistente}\"\n"

        prompt = f"""Eres un clasificador avanzado. Analiza el mensaje y esponde EXCLUSIVAMENTE con un JSON en el formato indicado.
            No escribas explicaciones, análisis ni ningún otro texto. Solo el JSON.

            Formato exacto requerido:

            {{
            "agente": "general" | "tarea" | "japones",
            "usar_memoria": true/false,
            "buscar_historial": true/false,
            "terminos_memoria": ["..."],
            "consultar_progreso": true/false
            }}

            Reglas:
            - agente "general": conversación normal, preguntas personales, saludos, recuerdos.
            - agente "tarea": crear/modificar/consultar recordatorios, alarmas, calendario, hora/fecha.
            - agente "japones": aprender japonés, traducir, gramática, vocabulario, ejercicios, practicar conversación en japonés, repasar.
            - usar_memoria: true si necesita información personal de Laura (gustos, trabajo, familia, perfil). NO lo uses para vocabulario de japonés.
            - buscar_historial: true crees que debes recordar una conversación pasada ("recuerdas...", "dijiste...", "ayer", "la última vez","lo que hablamos", "lo que dijimos", "el otro dia").
            - terminos_memoria: 1-3 palabras clave SOLO si buscar_historial es true. Si no, array vacío [].
            - consultar_progreso: true si el agente es "japones" y la petición implica recordar o usar lo ya aprendido. Ejemplos donde DEBE ser true:
            - "practicar lo que hemos aprendido"
            - "repasar", "repaso"
            - "lo que me enseñaste", "lo que vimos"
            - "examen", "ejercicios", "practicar"
            - "hablar en japonés", "conversar en japonés"
            - "usa lo que sé", "con lo que ya sé"

            Importante: Si el mensaje actual es una respuesta directa a lo que el asistente acaba de preguntar o proponer (por ejemplo, "sí",
            "practicar esa misma frase", "otra vez", "dime más"), mantén el mismo agente que se deduce del contexto.
            {contexto}
            Mensaje del usuario: "{mensaje}"
            JSON:"""

        try:
            respuesta = self.router_provider.completar([
                {"role": "user", "content": prompt}
            ])
            # Limpiar posibles marcas de código
            json_str = respuesta.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]

            print(f"🧭 Router JSON crudo:\n{json_str}")

            decision = json.loads(json_str)

            # Validar campos mínimos
            decision.setdefault("agente", "general")
            decision.setdefault("usar_memoria", False)
            decision.setdefault("buscar_historial", False)
            decision.setdefault("terminos_memoria", [])
            decision.setdefault("consultar_progreso", False)
            return decision
        except Exception as e:
            print(f"⚠️ Router falló: {e}")
            return {
                "agente": "general",
                "usar_memoria": False,
                "buscar_historial": False,
                "terminos_memoria": [],
                "consultar_progreso": False
            }

    def responder(self, mensaje: str) -> str:
        decision = self._detectar_intencion(mensaje)
        agente = decision["agente"]

        # Memoria conversacional (general)
        if decision["usar_memoria"]:
            self._inyectar_perfil_si_falta()

        if decision["buscar_historial"] and decision["terminos_memoria"]:
            contexto_bd = self.memory.buscar_en_historial(decision["terminos_memoria"])
            if contexto_bd:
                self.historial.append({
                    "role": "system",
                    "content": f"Información relevante del pasado:\n{contexto_bd}"
                })

        # Memoria de japonés
        if decision["consultar_progreso"]:
            progreso = self.jap_memory.obtener_progreso()
            self.historial.append({
                "role": "system",
                "content": f"Progreso actual de japonés:\n{progreso}"
            })

        # Añadir mensaje del usuario
        self.historial.append({"role": "user", "content": mensaje})

        # Agentes especializados
        if agente == "japones":
            respuesta = self._responder_profesor_japones(mensaje)   # ya con contexto
        elif agente == "tarea":
            respuesta = self._procesar_tarea(mensaje)
        else:
            respuesta = self.provider.completar(self.historial)

        self.historial.append({"role": "assistant", "content": respuesta})
        self.memory.guardar_mensaje(self.session_id, "user", mensaje)
        self.memory.guardar_mensaje(self.session_id, "assistant", respuesta)

        self.ultimo_agente = agente

        print(f"🤖 Kaito [{agente}]: {respuesta}")

        if len(self.historial) > MAX_MENSAJES + 1:
            self.historial = [self.historial[0]] + self.historial[-(MAX_MENSAJES):]
            print(f"🧹 Historial truncado a {MAX_MENSAJES} mensajes")

        return respuesta

    def saludar(self):
        """Saluda a Laura cuando la detecta"""
        try:
            self.state.cambiar("thinking")

            saludo = self.responder(
                "Laura acaba de sentarse delante de ti, "
                "salúdala de forma breve, cariñosa y personalizada"
            )

            print(f"🤖 Kaito: {saludo}")
            self.state.cambiar("speaking")
            self.socketio.emit("mensaje", {"texto": saludo})

            tiempo = min(len(saludo) * 0.05, 6)
            time.sleep(tiempo)
            self.state.cambiar("idle")

        except Exception as e:
            print(f"❌ Error saludando: {e}")
            self.state.cambiar("idle")

    def _responder_profesor_japones(self, mensaje: str) -> str:
        prompt_japones = cargar_prompt("profesor_japones")
        self.historial.append({"role": "system", "content": prompt_japones})
        try:
            # Si hay frase objetivo guardada, evaluamos pronunciación
            if self.ultima_frase_objetivo:
                from ai.pronunciation import comparar_pronunciacion
                evaluacion = comparar_pronunciacion(
                    self.ultima_frase_objetivo, mensaje
                )
                # Añadir contexto de evaluación al historial
                self.historial.append({
                    "role": "system",
                    "content": f"La pronunciación de Laura obtuvo {evaluacion['precision']}%. "
                               f"IPA objetivo: {evaluacion['ipa_objetivo']}. "
                               f"IPA hablado: {evaluacion['ipa_hablado']}. "
                               f"Incluye este feedback en tu respuesta: {evaluacion['feedback']}"
                })
                self.ultima_frase_objetivo = None

            respuesta = self.provider.completar(self.historial)

            # Dar ritmo natural a las frases de práctica
            if "repite" in respuesta.lower() or "di" in respuesta.lower():
                # Insertar pausas con puntos suspensivos
                respuesta = respuesta.replace(
                    "Repite conmigo",
                    "Repite conmigo... despacio..."
                )
            
            # Extraer nueva frase objetivo si la hay
            frase = self._extraer_frase_objetivo(respuesta)
            if frase:
                self.ultima_frase_objetivo = frase
            
            # ── Extraer y guardar progreso ──
            # Busca "---JSON---" o solo "---" seguido de posible JSON
            match = regex.split(r'---\s*(?:JSON)?\s*---', respuesta, maxsplit=1)
            if len(match) >= 2:
                texto_respuesta = match[0].strip()
                json_str = match[-1].strip()
                try:
                    if json_str.startswith("```"):
                        json_str = json_str.split("```")[1]
                        if json_str.startswith("json"):
                            json_str = json_str[4:]
                    progreso = json.loads(json_str)
                    for item in progreso.get("items", []):
                        self.jap_memory.registrar_item(
                            item.get("category", "general"),
                            item.get("item", ""),
                            item.get("detail", "")
                        )
                        print(f"🎌 Progreso guardado: {item}")
                except Exception as e:
                    print(f"⚠️ Error guardando progreso: {e}")
                return texto_respuesta
            # Si no hay JSON, devolvemos la respuesta completa
            return respuesta
        finally:
            self.historial.pop()

    def cerrar_sesion(self):
        """Cierra la sesión actual en la BD"""
        if self.session_id:
            self.memory.cerrar_sesion(self.session_id)

    def limpiar_historial(self):
        """Resetea el historial de RAM manteniendo la BD"""
        self._iniciar_sesion()
        print("🧹 Historial limpiado")

    def _procesar_tarea(self, mensaje: str) -> str:
        # 1. Obtener el JSON del LLM
        prompt_tareas = cargar_prompt("tareas_system")
        historial_tareas = [
            {"role": "system", "content": prompt_tareas},
            {"role": "user", "content": mensaje}
        ]
        respuesta_json = self.provider.completar(historial_tareas)

        # 2. Parsear
        try:    
            accion = json.loads(respuesta_json)
        except json.JSONDecodeError:
            # Si falla, responde amablemente
            return "No he entendido bien la tarea. ¿Puedes repetirlo?"

        # 3. Ejecutar acción
        tipo = accion.get("tipo")
        if tipo == "hora":
            ahora = datetime.now().strftime("%H:%M")
            return f"Son las {ahora}."
        elif tipo == "fecha":
            hoy = datetime.now().strftime("%d de %B de %Y")
            return f"Hoy es {hoy}."
        elif tipo == "recordatorio":
            # Aquí guardarías en BD de recordatorios (otra tabla o servicio)
            texto = accion.get("texto", "")
            hora = accion.get("hora", "")
            print(f"⏰ Recordatorio creado: {texto} a las {hora}")
            return f"¡Listo! Te recordaré '{texto}' a las {hora}."
        # ... otros casos ...
        else:
            return self._responder_conversacion("Esa tarea aún no sé hacerla, pero estoy aprendiendo.")

    def _inyectar_perfil_si_falta(self):
        """Añade el perfil al historial si aún no está presente"""
        # El perfil se añadió al iniciar sesión en _iniciar_sesion,
        # pero podemos verificar que siga estando en el primer mensaje system
        if not any("=== INFORMACIÓN SOBRE LAURA ===" in msg["content"] for msg in self.historial if msg["role"] == "system"):
            perfil = self.memory.obtener_perfil()
            self.historial.insert(1, {"role": "system", "content": perfil})  # justo después del system prompt base

    def _responder_conversacion(self, mensaje: str) -> str:
        # Asume que el mensaje ya está añadido al historial antes de llamar
        respuesta = self.provider.completar(self.historial)
        return respuesta

    def _ultimo_contexto_asistente(self) -> str:
        for msg in reversed(self.historial):
            if msg["role"] == "assistant":
                return msg["content"]
        return ""

    def _extraer_frase_objetivo(self, respuesta: str) -> str | None:
        """
        Si la respuesta contiene una frase para repetir,
        la extrae y la guarda.
        Busca patrones como 'Repite conmigo: X' o 'Di: X'
        """
        import re
        patrones = [
            r"(?:repit[ea]|di|pronuncia)\s+(?:conmigo\s*)?(?::|,)?\s*[「「]([^」」]+)[」」]",
            r"(?:repit[ea]|di|pronuncia)\s+(?:conmigo\s*)?(?::|,)?\s*([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+)",
        ]
        for patron in patrones:
            match = re.search(patron, respuesta, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None