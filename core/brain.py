from ai.groq_provider import GroqProvider
from ai.prompts import cargar_prompt
from core.memory import Memory
import time

# Palabras que indican que Laura pregunta por el pasado
PALABRAS_MEMORIA = [
    "recuerdas", "acuerdas", "dijiste", "hablamos",
    "comenté", "mencioné", "ayer", "semana pasada",
    "última vez", "antes", "anteriormente"
]

class Brain:
    def __init__(self, state_manager, socketio):
        self.state = state_manager
        self.socketio = socketio
        self.provider = GroqProvider()
        self.memory = Memory()
        self.session_id = None
        self._iniciar_sesion()

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

    def _necesita_memoria(self, mensaje: str) -> bool:
        """
        Detecta si Laura está preguntando
        por conversaciones pasadas
        """
        mensaje_lower = mensaje.lower()
        return any(
            palabra in mensaje_lower
            for palabra in PALABRAS_MEMORIA
        )

    def _añadir_contexto_historico(self):
        """
        Añade el historial de conversaciones
        al contexto solo cuando es necesario
        """
        historial_texto = self.memory.obtener_historial_reciente()
        if historial_texto:
            self.historial.append({
                "role": "system",
                "content": f"Contexto de conversaciones anteriores:\n{historial_texto}"
            })
            print("📚 Contexto histórico añadido")

    def _extraer_terminos(self, mensaje: str) -> list:
        """
        Extrae palabras clave del mensaje
        para buscar en la BD
        """
        # Palabras a ignorar
        stopwords = {
            "que", "de", "la", "el", "en", "y", "a",
            "los", "las", "un", "una", "es", "se", "no",
            "me", "te", "le", "lo", "con", "por", "para",
            "como", "cuando", "donde", "quien", "cual",
            "tengo", "tienes", "tiene", "hay", "hola",
            "qué", "cuál", "cuándo", "dónde", "cómo"
        }

        palabras = mensaje.lower().split()
        terminos = [
            p for p in palabras
            if len(p) > 3 and p not in stopwords
        ]

        return terminos[:5]  # Máximo 5 términos

    def responder(self, mensaje: str) -> str:
        """
        Responde al mensaje de Laura.
        Busca siempre en la BD por términos relevantes.
        """
        # Extrae términos clave del mensaje
        terminos = self._extraer_terminos(mensaje)

        # Busca en BD mensajes relevantes
        if terminos:
            contexto_bd = self.memory.buscar_en_historial(terminos)
            if contexto_bd:
                print(f"📚 Memoria encontrada para: {terminos}")
                # Añade contexto relevante al historial
                self.historial.append({
                    "role": "system",
                    "content": f"Información relevante de conversaciones anteriores:\n{contexto_bd}"
                })

        # Añade mensaje al historial
        self.historial.append({
            "role": "user",
            "content": mensaje
        })

        # Llama a Groq
        respuesta = self.provider.completar(self.historial)

        # Añade respuesta al historial
        self.historial.append({
            "role": "assistant",
            "content": respuesta
        })

        # Guarda en BD
        self.memory.guardar_mensaje(
            self.session_id, "user", mensaje
        )
        self.memory.guardar_mensaje(
            self.session_id, "assistant", respuesta
        )

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

    def cerrar_sesion(self):
        """Cierra la sesión actual en la BD"""
        if self.session_id:
            self.memory.cerrar_sesion(self.session_id)

    def limpiar_historial(self):
        """Resetea el historial de RAM manteniendo la BD"""
        self._iniciar_sesion()
        print("🧹 Historial limpiado")