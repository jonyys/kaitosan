import requests
from core.config import TAVILY_API_KEY

class SearchProvider:
    def __init__(self):
        self.api_key = TAVILY_API_KEY
        self.url = "https://api.tavily.com/search"

    def buscar(self, consulta: str) -> str:
        """
        Busca en internet con Tavily y devuelve un resumen
        formateado para inyectar en el contexto del LLM.
        """
        try:
            response = requests.post(
                self.url,
                json={
                    "query": consulta,
                    "search_depth": "basic",
                    "include_answer": True,
                    "max_results": 3
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            data = response.json()

            # Construir un texto limpio con los resultados
            resultados = []
            if data.get("answer"):
                resultados.append(f"Respuesta: {data['answer']}")

            for r in data.get("results", []):
                resultados.append(f"- {r['title']}: {r['content']} (Fuente: {r['url']})")

            return "\n".join(resultados) if resultados else "Sin resultados."

        except Exception as e:
            print(f"❌ Error en búsqueda Tavily: {e}")
            return "No se pudo realizar la búsqueda en este momento."