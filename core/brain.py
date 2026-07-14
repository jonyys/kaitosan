import json
import threading
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
import time
from datetime import datetime
import re as regex

# Limitar tamaño del historial para sesiones largas
MAX_MENSAJES = 20

class Brain:

    SALUDOS_SENSEI = [
            "Modo Sensei activado! 【こんにちは、ラウラさん。おげんきですか。】",
            "Modo Sensei activado! 【おはようございます、ラウラさん。きょうはなにをしたいですか。】",
            "Modo Sensei activado! 【こんばんは、ラウラさん。げんきですか。】",
            "Modo Sensei activado! 【やあ、ラウラさん。ちょうしはどうですか。】",
            "Modo Sensei activado! 【ラウラさん、こんにちは。にほんごをべんきょうしましょう。】"
    ]

    DESPEDIDAS_SENSEI = [
        "【またね、ラウラさん】",
        "【じゃあね、ラウラさん。また会いましょう】",
        "【おつかれさまでした。またね】",
        "【さようなら、ラウラさん。また今度】",
        "【バイバイ、ラウラさん。気をつけてね】"
    ]

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
        self.ultima_frase_objetivo = None
        self.search = SearchProvider()
        self.modo_sensei = False
        self.timer_sensei = None
        self.sensei_lento = False
        self.weather = WeatherSkill()
        self.alarm = AlarmSkill()
        self.reminder = ReminderSkill()

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
                - agente: "general" para conversación normal, preguntas, saludos, peticiones de traducción, significado de palabras, etc. 
                    "tarea" para crear/modificar/consultar recordatorios, alarmas, hora/fecha, temporizadores, tiempo, clima, etc.
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

    def responder(self, mensaje: str) -> str:

        # Detectar comandos de modo sensei
        if any(frase in mensaje.lower() for frase in ["sensei", "entrar en modo", "entra en modo", "modo sensei on", "activar modo sensei", "activar modo", "en modo"]):
            if not self.modo_sensei:
                self.entrar_modo_sensei()
                return random.choice(self.SALUDOS_SENSEI)

        if any(frase in mensaje.lower() for frase in ["salir del modo sensei", "sal del modo sensei", "modo sensei off", "salir del modo", "sal del modo", "desactivar modo", "desactivar modo", "desctivar", "desactiva"]):
            if self.modo_sensei:
                self.salir_modo_sensei()
                return random.choice(self.DESPEDIDAS_SENSEI)

         # ── Si ya estamos en modo sensei, saltamos el enrutador ──
        if self.modo_sensei:
            # Detectar si Laura pide más lento (solo para esta respuesta)
            lento_extra = any(
                p in mensaje.lower() for p in ["más lento", "despacio", "lentamente", "despacito"]
            )

            self._renovar_timer_sensei()
            self.historial.append({"role": "user", "content": mensaje})
            respuesta = self._responder_profesor_japones(mensaje)
            self.historial.append({"role": "assistant", "content": respuesta})
            self.memory.guardar_mensaje(self.session_id, "user", mensaje)
            self.memory.guardar_mensaje(self.session_id, "assistant", respuesta)
            respuesta = self._limpiar_json_de_respuesta(respuesta)
            print(f"🤖 Kaito [sensei]: {respuesta}")
            return respuesta, lento_extra

        # Si estamos en modo sensei, forzar agente japones
        if self.modo_sensei and agente != "japones":
            agente = "japones"
            decision["consultar_progreso"] = True

        if self.modo_sensei and any(p in mensaje.lower() for p in ["más lento", " mas despacio", "lentamente", "despacito"]):
            self.sensei_lento = True
        else:
            self.sensei_lento = False

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
        if agente == "japones":
            respuesta = self._responder_profesor_japones(mensaje)   # ya con contexto
        elif agente == "tarea":
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

        # Inyectar estado de la sesión
        estado = self._generar_estado_japones()
        self.historial.insert(1, {"role": "system", "content": estado})

        try:
            # Evaluar pronunciación si hay frase objetivo
            if self.ultima_frase_objetivo:
                from ai.pronunciation import comparar_pronunciacion
                evaluacion = comparar_pronunciacion(
                    self.ultima_frase_objetivo, mensaje
                )
                self.historial.append({
                    "role": "system",
                    "content": f"La pronunciación de Laura obtuvo {evaluacion['precision']}%. "
                               f"IPA objetivo: {evaluacion['ipa_objetivo']}. "
                               f"IPA hablado: {evaluacion['ipa_hablado']}. "
                               f"Incluye este feedback en tu respuesta: {evaluacion['feedback']}"
                })
                self.ultima_frase_objetivo = None

            respuesta = self.provider.completar(self.historial)

            # Extraer frase objetivo si la hay
            frase = self._extraer_frase_objetivo(respuesta)
            if frase:
                self.ultima_frase_objetivo = frase

            # ── Extraer y guardar progreso ──
            match = regex.split(r'---\s*(?:JSON)?\s*---', respuesta, maxsplit=1)
            if len(match) >= 2:
                json_str = match[-1].strip()
                try:
                    if json_str.startswith("```"):
                        json_str = json_str.split("```")[1]
                        if json_str.startswith("json"):
                            json_str = json_str[4:]
                    progreso = json.loads(json_str)
                    for item in progreso.get("items", []):
                        cat = item.get("category", "vocabulario")
                        if cat in ("vocabulario", "frase"):
                            self.jap_memory.registrar_vocabulario(
                                word=item.get("jp", item.get("item", "")),
                                reading=item.get("jp", ""),
                                meaning=item.get("es", item.get("detail", "")),
                                word_type=cat
                            )
                        elif cat == "gramatica":
                            self.jap_memory.registrar_gramatica(
                                grammar_point=item.get("jp", item.get("item", "")),
                                description=item.get("es", item.get("detail", ""))
                            )
                        print(f"🎌 Progreso guardado: {item}")
                except Exception as e:
                    print(f"⚠️ Error guardando progreso: {e}")

            # Limpiar cualquier JSON residual antes de devolver
            respuesta = self._limpiar_json_de_respuesta(respuesta)
            return respuesta

        finally:
            self.historial.pop()

    def _generar_estado_japones(self, modo: str) -> str:
        """
        Genera un bloque de contexto para el profesor de japonés
        con el progreso real de Laura y el modo actual.
        """
        perfil = self.jap_memory.obtener_perfil_completo()  # ya tienes este método
        
        # Determinar objetivo según el modo
        objetivos = {
            "conversacion": "Practicar conversación natural usando vocabulario y gramática ya dominados.",
            "traduccion": "Traducir palabras o frases solicitadas por Laura.",
            "practica": "Reforzar estructuras gramaticales con ejercicios guiados."
        }
        objetivo = objetivos.get(modo, objetivos["conversacion"])
        
        estado = f"""ESTADO DE LA SESIÓN

            Modo: {modo.capitalize()}

            Objetivo: {objetivo}

            {perfil}

            Reglas importantes:
            - NO enseñes palabras que ya aparezcan como dominadas, salvo que Laura pida repasarlas explícitamente.
            - Introduce como máximo UNA palabra o estructura nueva por respuesta.
            - Prioriza que Laura gane confianza. No interrumpas para corregir errores menores.
            - Si un error no impide entender el mensaje, continúa y coméntalo después.
            - Reutiliza vocabulario ya aprendido para reforzar la memoria.
            - Alterna entre enseñar, preguntar y conversar.
            """
        return estado

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

    def entrar_modo_sensei(self):
        self.modo_sensei = True
        print("🎌 Modo Sensei activado")
        # Cancelar timer de salida si existía
        if self.timer_sensei:
            self.timer_sensei.cancel()
        self.socketio.emit("modo_sensei", {"activo": True})

    def salir_modo_sensei(self):
        self.modo_sensei = False
        print("🎌 Modo Sensei desactivado")
        # Cancelar timer
        if self.timer_sensei:
            self.timer_sensei.cancel()
            self.timer_sensei = None
        self.socketio.emit("modo_sensei", {"activo": False})

    def _renovar_timer_sensei(self):
        """Reinicia el contador de inactividad de 20 minutos."""
        if self.timer_sensei:
            self.timer_sensei.cancel()
        self.timer_sensei = threading.Timer(20 * 60, self.salir_modo_sensei)
        self.timer_sensei.daemon = True
        self.timer_sensei.start()

    def _procesar_json_progreso(self, respuesta: str):
        """Extrae y guarda el progreso si la respuesta contiene JSON."""
        import re as regex
        match = regex.split(r'---\s*(?:JSON)?\s*---', respuesta, maxsplit=1)
        if len(match) >= 2:
            json_str = match[-1].strip()
            try:
                if json_str.startswith("```"):
                    json_str = json_str.split("```")[1]
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
                progreso = json.loads(json_str)
                for item in progreso.get("items", []):
                    cat = item.get("category", "vocabulario")
                    if cat in ("vocabulario", "frase"):
                        self.jap_memory.registrar_vocabulario(
                            word=item.get("jp", item.get("item", "")),
                            reading=item.get("jp", ""),
                            meaning=item.get("es", item.get("detail", "")),
                            word_type=cat
                        )
                    elif cat == "gramatica":
                        self.jap_memory.registrar_gramatica(
                            grammar_point=item.get("jp", item.get("item", "")),
                            description=item.get("es", item.get("detail", ""))
                        )
                    print(f"🎌 Progreso guardado: {item}")
            except Exception as e:
                print(f"⚠️ Error guardando progreso: {e}")

    def _limpiar_json_de_respuesta(self, texto: str) -> str:
        """
        Elimina cualquier bloque JSON (delimitado por ---JSON--- o ---)
        y cualquier JSON suelto al final del texto antes de enviarlo al TTS.
        """
        if not texto:
            return texto

        # Eliminar bloques ---JSON--- ... contenido ... ---
        texto = regex.sub(
            r'---\s*(?:JSON)?\s*---.*?---\s*(?:JSON)?\s*---',
            '',
            texto,
            flags=regex.DOTALL | regex.IGNORECASE
        )

        # Eliminar JSON suelto al final (ej: {"items": [...]})
        texto = regex.sub(r'\n?\{[^{}]*\}[^{}]*$', '', texto)
        texto = regex.sub(r'\n?\[[^\[\]]*\][^\[\]]*$', '', texto)

        return texto.strip()