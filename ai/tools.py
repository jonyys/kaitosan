from datetime import datetime

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "poner_alarma",
            "description": "Pone una alarma a una hora específica del día",
            "parameters": {
                "type": "object",
                "properties": {
                    "hora": {"type": "string", "description": "Hora en formato HH:MM, por ejemplo '07:30'"}
                },
                "required": ["hora"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "poner_temporizador",
            "description": "Pone un temporizador durante X minutos y/o segundos",
            "parameters": {
                "type": "object",
                "properties": {
                    "minutos": {"type": "integer", "description": "Minutos (default 0)"},
                    "segundos": {"type": "integer", "description": "Segundos adicionales (default 0)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_recordatorio",
            "description": "Crea un recordatorio para Laura",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Qué hay que recordar"},
                    "cuando": {"type": "string", "description": "Cuándo, por ejemplo 'en 2 horas', 'mañana a las 10'"}
                },
                "required": ["texto", "cuando"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_hora",
            "description": "Obtiene la hora actual del sistema",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_fecha",
            "description": "Obtiene la fecha de hoy",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_clima",
            "description": "Obtiene el tiempo meteorológico actual o la previsión",
            "parameters": {
                "type": "object",
                "properties": {
                    "ciudad": {"type": "string", "description": "Ciudad concreta, omitir para usar la ubicación por defecto"},
                    "cuando": {"type": "string", "description": "'ahora', 'mañana', 'esta semana'"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_internet",
            "description": "Busca información actual en internet. Usar solo para datos que cambian con frecuencia: noticias de hoy, precio actual de un producto, resultado deportivo, horario de un negocio, clima si no tienes la herramienta de clima disponible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Consulta optimizada para buscador web. Construye tú la query a partir del contexto de la conversación: usa 2-5 palabras clave en español, nunca pases literalmente lo que dijo el usuario. Ejemplos: 'recetas pollo al horno fácil', 'precio iPhone 16 España', 'Real Madrid resultado hoy', 'horario Mercadona Collado Mediano'."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_en_historial",
            "description": "Busca en conversaciones pasadas con Laura. Usar cuando ella hace referencia explícita a algo que ya hablaron: 'lo que me dijiste', 'aquella receta de antes', 'lo que comentamos'",
            "parameters": {
                "type": "object",
                "properties": {
                    "terminos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "1-3 palabras clave para buscar en el historial"
                    }
                },
                "required": ["terminos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_progreso_japones",
            "description": "Obtiene el progreso de Laura en japonés: vocabulario, gramática, nivel. Usar cuando pregunta por su nivel o cuando vas a enseñarle algo nuevo",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]


class ToolDispatcher:
    def __init__(self, alarm, reminder, weather, search, memory, jap_memory):
        self.alarm = alarm
        self.reminder = reminder
        self.weather = weather
        self.search = search
        self.memory = memory
        self.jap_memory = jap_memory

    def ejecutar(self, nombre: str, args: dict) -> str:
        print(f"🔧 Herramienta: {nombre}({args})")
        resultado = self._ejecutar(nombre, args)
        print(f"   ↳ Resultado: {resultado}")
        return resultado

    def _ejecutar(self, nombre: str, args: dict) -> str:
        if nombre == "poner_alarma":
            return self.alarm.poner_alarma(args.get("hora", "07:00"))
        elif nombre == "poner_temporizador":
            return self.alarm.poner_temporizador(args.get("minutos", 0), args.get("segundos", 0))
        elif nombre == "crear_recordatorio":
            return self.reminder.crear_recordatorio(args["texto"], args["cuando"])
        elif nombre == "obtener_hora":
            return datetime.now().strftime("%H:%M")
        elif nombre == "obtener_fecha":
            MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
                        "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            hoy = datetime.now()
            return f"{hoy.day} de {MESES_ES[hoy.month - 1]} de {hoy.year}"
        elif nombre == "obtener_clima":
            return self.weather.describir_clima(ciudad=args.get("ciudad"), cuando=args.get("cuando", "ahora"))
        elif nombre == "buscar_internet":
            return self.search.buscar(args["query"])
        elif nombre == "buscar_en_historial":
            return self.memory.buscar_en_historial(args.get("terminos", []))
        elif nombre == "consultar_progreso_japones":
            return self.jap_memory.obtener_perfil_completo()
        else:
            print(f"⚠️ Herramienta desconocida: {nombre}")
            return ""
