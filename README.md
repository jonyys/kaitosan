
# Robot — Proyecto de ejemplo

Descripción
- Este proyecto es una plataforma modular en Python para un "robot" software que integra capacidades de percepción (visión y audio), procesamiento de lenguaje natural y motores de síntesis/reconocimiento de voz.
- Objetivo: facilitar experimentación y prototipado de asistentes conversacionales físicos o virtuales que combinen detección visual, diálogo y audio en tiempo real.

Principales funcionalidades
- Captura y procesamiento de vídeo (detección/seguimiento de objetos/rostros).
- Procesamiento de audio: grabación, reconocimiento de voz (STT) y síntesis de voz (TTS).
- Integración con proveedores de modelos de lenguaje/IA (módulos en `ai/`) con abstracción para cambiar de backend.
- Módulo de memoria y estado para manejar contexto conversacional y eventos (guardado en `core/memory.py` y `core/japanese_memory.py`).

Arquitectura y organización
- `app.py`: arranque de la aplicación y orquestación básica.
- `ai/`: adaptadores para distintos proveedores (por ejemplo, `groq_provider.py`, `gemini_provider.py`) y utilidades de prompts y pronunciación.
- `core/`: componentes centrales — `brain.py` (lógica de alto nivel), `camera.py` (interfaz con cámara), `detection.py` (algoritmos de detección), `state.py` y `memory.py`.
- `audio/`: grabación y utilidades de audio (por ejemplo `recorder.py`).
- `tests/`: pruebas unitarias para componentes críticos.

Flujo de datos (resumido)
1. La cámara captura fotogramas (`core/camera.py`).
2. `core/detection.py` analiza los fotogramas y envía eventos al `brain`.
3. El `brain` decide acciones: consultar modelos de lenguaje (`ai/`), reproducir TTS, o guardar contexto en `core/memory.py`.
4. El subsistema de audio gestiona la entrada/salida (grabación → STT → procesamiento → TTS → salida de audio).

Variables de entorno y configuración
- Copia `.env.example` a `.env` y añade las claves de los proveedores de IA y configuración del audio/cámara.
- Ejemplos de variables comunes: claves de API para proveedores en `ai/`, parámetros de dispositivo de audio, rutas de almacenamiento.

Cómo desarrollar localmente
1. Crear y activar un entorno virtual:
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```
2. Instalar dependencias:
  ```bash
  pip install -r requirements.txt
  ```
3. Copiar el ejemplo de variables de entorno y editar:
  ```bash
  cp .env.example .env
  # editar .env según las credenciales y dispositivos
  ```
4. Ejecutar la aplicación:
  ```bash
  python app.py
  ```

Pruebas
- Ejecutar todas las pruebas con `pytest`:
  ```bash
  pytest -q
  ```

Consejos de depuración
- Si hay errores al inicializar un proveedor de IA, revisa las variables en `.env` y los archivos bajo `ai/`.
- Para problemas con la cámara, prueba primero con scripts pequeños que abran el dispositivo (ver `core/camera.py`).

Contribuir
- Añade issues para bugs o mejoras y crea pull requests pequeños y con pruebas cuando sea posible.

Licencia
- Añade una licencia en `LICENSE` según prefieras (MIT, Apache, etc.).

Contacto
- Abre un issue en el repositorio para discutir características o problemas.

