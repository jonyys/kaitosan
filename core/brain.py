import json
import random
from ai.groq_provider import GroqProvider
from ai.prompts import cargar_prompt
from ai.fallback_provider import FallbackProvider
from ai.search_provider import SearchProvider
from ai.skills.weather import WeatherSkill
from ai.skills.alarm import AlarmSkill
from ai.skills.reminder import ReminderSkill

from core.japanese_memory import JapaneseMemory
from core.memory import DB_PATH, Memory
from ai.sensei.profesor import ProfesorJapones, SALUDOS, DESPEDIDAS
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
        self.provider_ligero = FallbackProvider(model="llama-3.1-8b-instant")
        self.memory = Memory()
        self.jap_memory = JapaneseMemory(DB_PATH)    
        self.session_id = None
        self._iniciar_sesion()
        self.ultimo_agente = "general"
        self.search = SearchProvider()
        self.weather = WeatherSkill()
        self.alarm = AlarmSkill()
        self.reminder = ReminderSkill()
        self.profesor = ProfesorJapones(self.jap_memory, self.provider, self.provider_ligero, self.memory, self.socketio)
        self._emitir_desactivar_sensei = False  # se activa en salir; app.py lo consume tras el TTS

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

        ultimo_asistente = self._ultimo_contexto_asistente()
        contexto = ""
        if ultimo_asistente:
            contexto = f"Último mensaje del asistente: \"{ultimo_asistente}\"\n"

        prompt = f"""Eres un clasificador avanzado. Analiza el mensaje y esponde EXCLUSIVAMENTE con un JSON en el formato indicado.
            No escribas explicaciones, análisis ni ningún otro texto. Solo el JSON.

            Formato exacto requerido:

            {{
            "agente": "general" | "tarea",
            "usar_memoria": true/false,
            "buscar_historial": true/false,
            "terminos_memoria": ["..."],
            "consultar_progreso": true/false,
            "buscar_internet": false
            }}

            Reglas:
                - agente:
                    -"general" para conversación normal, preguntas, saludos, peticiones de traducción, significado de palabras, etc. 
                    -"tarea" para crear/modificar/consultar recordatorios, alarmas, hora/fecha, temporizadores, tiempo, clima, etc.
                - usar_memoria: true si necesita datos personales de Laura (gustos, trabajo, familia, perfil).
                - buscar_historial: true crees que debes recordar una conversación pasada sobre algo que ya hablasteis.
                - terminos_memoria: 1-3 palabras clave SOLO si buscar_historial es true. Si no, array vacío [].
                - consultar_progreso: true si la pregunta es sobre japonés (traducciones, vocabulario, gramática) y podría beneficiarse de conocer el progreso de Laura. Esto ayuda al agente general a responder mejor.
                - buscar_internet: true si la pregunta requiere información factual, actual o local
                    que el modelo no puede saber sin acceso a internet (restaurantes, direcciones,
                    noticias, eventos actuales, datos muy específicos).
                    NUNCA actives buscar_internet para preguntas de TRADUCCIÓN, GRAMÁTICA, VOCABULARIO
                    JAPONÉS, CLIMA, TIEMPO METEOROLÓGICO o HORA/FECHA.
                    Esas las manejan los agentes "japones" o "tarea" sin internet.


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
                "consultar_progreso": False,
                "buscar_internet": False
            }

    def responder(self, mensaje: str) -> tuple[str, bool]:
        """Devuelve siempre (respuesta, lento_extra).

        `lento_extra` solo es True dentro del modo sensei cuando Laura pide
        hablar más despacio; en el flujo normal es siempre False.
        """

        # Detectar comandos de modo sensei → delegar en ProfesorJapones
        if any(frase in mensaje.lower() for frase in ["sensei", "entrar en modo", "entra en modo", "modo sensei on", "activar modo sensei", "activar modo", "en modo"]):
            if not self.profesor.esta_activo():
                self.profesor.entrar()
                return random.choice(SALUDOS), False

        if any(frase in mensaje.lower() for frase in ["salir del modo sensei", "sal del modo sensei", "modo sensei off", "salir del modo", "sal del modo", "desactivar modo", "desactivar modo", "desctivar", "desactiva"]):
            if self.profesor.esta_activo():
                self.profesor.salir()
                self._emitir_desactivar_sensei = True
                return random.choice(DESPEDIDAS), False

         # ── Si ya estamos en modo sensei, delegamos en el profesor ──
        if self.profesor.esta_activo():
            # Detectar si Laura pide más lento (solo para esta respuesta)
            lento_extra = any(
                p in mensaje.lower() for p in ["más lento", "despacio", "lentamente", "despacito"]
            )

            respuesta = self.profesor.responder_turno(mensaje, lento_extra)
            self.memory.guardar_mensaje(self.session_id, "user", mensaje)
            self.memory.guardar_mensaje(self.session_id, "assistant", respuesta)
            respuesta = self._limpiar_json_de_respuesta(respuesta)
            print(f"🤖 Kaito [sensei]: {respuesta}")
            return respuesta, lento_extra

        # ── Flujo normal con enrutador ──
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
            progreso = self.jap_memory.obtener_perfil_completo()
            self.historial.append({
                "role": "system",
                "content": f"Progreso actual de japonés:\n{progreso}"
            })

        # Búsqueda en internet (nunca para el profesor de japonés)
        if decision.get("buscar_internet") and agente != "japones":
            print(f"🌐 Buscando en internet: {mensaje}")
            resultados = self.search.buscar(mensaje)
            self.historial.append({
                "role": "system",
                "content": f"Resultados de búsqueda en internet:\n{resultados}\n\n"
                           "Usa esta información para responder. Si no encuentras "
                           "la respuesta, dilo con sinceridad."
            })

        # Añadir mensaje del usuario
        self.historial.append({"role": "user", "content": mensaje})

        # Agentes especializados
        if agente == "tarea":
            # Si agente es "tarea", siempre sin busqueda en internet
            self.provider.buscar_internet = False
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
        respuesta = self._limpiar_json_de_respuesta(respuesta)
        return respuesta, False

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
            return self._responder_tarea_amable(f"Son las {ahora}.")
        elif tipo == "alarma":
            hora = accion.get("hora", "07:00")
            return self._responder_tarea_amable(
                self.alarm.poner_alarma(hora)
            )
        elif tipo == "temporizador":
            minutos = accion.get("minutos", 0)
            segundos = accion.get("segundos", 0)
            return self._responder_tarea_amable(
                self.alarm.poner_temporizador(minutos, segundos)
            )
        elif tipo == "fecha":
            hoy = datetime.now().strftime("%d de %B de %Y")
            return self._responder_tarea_amable(f"Hoy es {hoy}.")
        elif tipo == "clima":
            ciudad = accion.get("ciudad", None)
            cuando = accion.get("cuando", "ahora")
            datos_clima = self.weather.describir_clima(ciudad=ciudad, cuando=cuando)
            return self._responder_tarea_amable(datos_clima)     
        elif tipo == "recordatorio":
            texto = accion.get("texto", "Recordatorio")
            cuando = accion.get("cuando", "en 5 minutos")
            print(f"📌 DEBUG _procesar_tarea: texto='{texto}', cuando='{cuando}'")
            return self._responder_tarea_amable(
                self.reminder.crear_recordatorio(texto, cuando)
            )
        # ... otros casos ...
        else:
            return self._responder_tarea_amable("Esa tarea aún no sé hacerla, pero estoy aprendiendo.")

    def _responder_tarea_amable(self, datos: str) -> str:
        prompt_respuesta = cargar_prompt("responde_tarea")
        self.historial.append({"role": "system", "content": f"{prompt_respuesta}\n\nDatos: {datos}"})

        # Usamos el proveedor ligero para que no gaste tokens del modelo grande
        respuesta = self.provider_ligero.completar(self.historial)
        respuesta = self._limpiar_json_de_respuesta(respuesta)

        # Quitamos el mensaje system que acabamos de añadir para no ensuciar el historial
        self.historial.pop()
        respuesta = self._limpiar_json_de_respuesta(respuesta)
        return respuesta

    def _inyectar_perfil_si_falta(self):
        """Añade el perfil al historial si aún no está presente"""
        # El perfil se añadió al iniciar sesión en _iniciar_sesion,
        # pero podemos verificar que siga estando en el primer mensaje system
        if not any("=== INFORMACIÓN SOBRE LAURA ===" in msg["content"] for msg in self.historial if msg["role"] == "system"):
            perfil = self.memory.obtener_perfil()
            self.historial.insert(1, {"role": "system", "content": perfil})  # justo después del system prompt base

    def _ultimo_contexto_asistente(self) -> str:
        for msg in reversed(self.historial):
            if msg["role"] == "assistant":
                return msg["content"]
        return ""

    def _limpiar_json_de_respuesta(self, texto: str) -> str:
        """
        Elimina cualquier bloque JSON delimitado por ---JSON--- (o solo ---)
        y el JSON que le sigue hasta el final del texto.
        """
        if not texto:
            return texto

        # Eliminar desde el último "---" (con o sin JSON) hasta el final,
        # siempre que después venga un objeto o array JSON.
        # Esto cubre tanto "---JSON---\n{...}" como "---\n{...}".
        texto = regex.sub(
            r'---\s*(?:JSON)?\s*---\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*$',
            '',
            texto,
            flags=regex.IGNORECASE
        )

        # Por si queda algún resto de "---JSON---" suelto al final (sin JSON),
        # lo eliminamos también.
        texto = regex.sub(r'\n?---\s*(?:JSON)?\s*---\s*$', '', texto)

        return texto.strip()