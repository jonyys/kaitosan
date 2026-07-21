import json
import random
from ai.prompts import cargar_prompt
from ai.fallback_provider import FallbackProvider
from ai.search_provider import SearchProvider
from ai.skills.weather import WeatherSkill
from ai.skills.alarm import AlarmSkill
from ai.skills.reminder import ReminderSkill
from ai.tools import TOOLS, ToolDispatcher

from core.japanese_memory import JapaneseMemory
from core.memory import DB_PATH, Memory
from ai.sensei.profesor import ProfesorJapones, SALUDOS, DESPEDIDAS
import re as regex

MAX_MENSAJES = 20


class Brain:

    def __init__(self, state_manager, socketio):
        self.state = state_manager
        self.socketio = socketio
        self.provider = FallbackProvider(model="llama-3.3-70b-versatile")
        self.provider_ligero = FallbackProvider(model="llama-3.1-8b-instant")
        self.memory = Memory()
        self.jap_memory = JapaneseMemory(DB_PATH)
        self.session_id = None
        self._iniciar_sesion()
        self.dispatcher = ToolDispatcher(
            alarm=AlarmSkill(socketio=socketio),
            reminder=ReminderSkill(socketio=socketio),
            weather=WeatherSkill(),
            search=SearchProvider(),
            memory=self.memory,
            jap_memory=self.jap_memory,
        )
        # Acceso directo para compatibilidad con app.py
        self.reminder = self.dispatcher.reminder
        self.alarm = self.dispatcher.alarm
        self.profesor = ProfesorJapones(self.jap_memory, self.provider, self.provider_ligero, self.memory, self.socketio)
        self._emitir_desactivar_sensei = False

    def _iniciar_sesion(self):
        self.session_id = self.memory.iniciar_sesion()
        system_prompt = cargar_prompt("system_prompt")
        perfil = self.memory.obtener_perfil()
        self.historial = [
            {"role": "system", "content": f"{system_prompt}\n\n{perfil}"}
        ]
        print(f"✅ Sesión {self.session_id} iniciada")

    def responder(self, mensaje: str) -> tuple[str, bool]:
        """Devuelve siempre (respuesta, lento_extra)."""

        # ── Comandos de modo sensei ──
        if any(f in mensaje.lower() for f in ["sensei", "entrar en modo", "entra en modo", "modo sensei on", "activar modo sensei", "activar modo", "en modo"]):
            if not self.profesor.esta_activo():
                self.profesor.entrar()
                return random.choice(SALUDOS), False

        if any(f in mensaje.lower() for f in ["salir del modo sensei", "sal del modo sensei", "modo sensei off", "salir del modo", "sal del modo", "desactivar modo", "desctivar", "desactiva"]):
            if self.profesor.esta_activo():
                self.profesor.salir()
                self._emitir_desactivar_sensei = True
                return random.choice(DESPEDIDAS), False

        if self.profesor.esta_activo():
            lento_extra = any(p in mensaje.lower() for p in ["más lento", "despacio", "lentamente", "despacito"])
            respuesta = self.profesor.responder_turno(mensaje, lento_extra)
            self.memory.guardar_mensaje(self.session_id, "user", mensaje)
            self.memory.guardar_mensaje(self.session_id, "assistant", respuesta)
            print(f"🤖 Kaito [sensei]: {respuesta}")
            return self._limpiar_json_de_respuesta(respuesta), lento_extra

        # ── Flujo normal con function calling ──
        if len(self.historial) > MAX_MENSAJES + 1:
            self.historial = [self.historial[0]] + self.historial[-(MAX_MENSAJES):]
            print(f"🧹 Historial truncado a {MAX_MENSAJES} mensajes")

        self.historial.append({"role": "user", "content": mensaje})

        # Primera llamada: el modelo decide si usar herramientas
        content, tool_calls = self.provider.completar_tools(self.historial, TOOLS)
        if tool_calls:
            self._aplicar_tool_calls(tool_calls)
            # Segunda llamada sin herramientas: fuerza respuesta de texto con los resultados
            content = self.provider.completar(self.historial)

        respuesta = self._limpiar_json_de_respuesta(content or "")
        self.historial.append({"role": "assistant", "content": respuesta})
        self.memory.guardar_mensaje(self.session_id, "user", mensaje)
        self.memory.guardar_mensaje(self.session_id, "assistant", respuesta)
        print(f"🤖 Kaito: {respuesta}")
        return respuesta, False

    def _aplicar_tool_calls(self, tool_calls):
        self.historial.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in tool_calls
            ]
        })
        for tc in tool_calls:
            args = json.loads(tc.function.arguments)
            resultado = self.dispatcher.ejecutar(tc.function.name, args)
            self.historial.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(resultado) if resultado else "Sin resultado"
            })

    def cerrar_sesion(self):
        if self.session_id:
            self.memory.cerrar_sesion(self.session_id)

    def limpiar_historial(self):
        self._iniciar_sesion()
        print("🧹 Historial limpiado")

    def _limpiar_json_de_respuesta(self, texto: str) -> str:
        if not texto:
            return texto
        texto = regex.sub(
            r'---\s*(?:JSON)?\s*---\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*$',
            '', texto, flags=regex.IGNORECASE
        )
        texto = regex.sub(r'\n?---\s*(?:JSON)?\s*---\s*$', '', texto)
        return texto.strip()
