import cv2
import threading
import time

class PersonDetector:
    def __init__(self, camera, state_manager, brain):
        self.camera = camera
        self.state = state_manager
        self.brain = brain
        self.hay_persona = False
        self.activo = True

        self.detector = cv2.CascadeClassifier(
            cv2.data.haarcascades +
            'haarcascade_frontalface_default.xml'
        )

    def iniciar(self):
        hilo = threading.Thread(
            target=self._detectar,
            daemon=True
        )
        hilo.start()
        print("👁️ Detección de personas iniciada")

    def _detectar(self):
        while self.activo:
            try:
                if not self.camera.disponible():
                    time.sleep(1)
                    continue

                frame = self.camera.capturar_frame()
                if frame is None:
                    continue

                gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                caras = self.detector.detectMultiScale(
                    gris,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )

                hay_persona_ahora = len(caras) > 0

                if hay_persona_ahora and not self.hay_persona:
                    print("✅ ¡Persona detectada!")
                    self.hay_persona = True
                    if self.state.es("idle"):
                        self.state.cambiar("happy")
                        threading.Thread(
                            target=self.brain.saludar,
                            daemon=True
                        ).start()

                elif not hay_persona_ahora and self.hay_persona:
                    print("👋 Persona se ha ido")
                    self.hay_persona = False
                    if not self.state.es("thinking") and \
                       not self.state.es("speaking"):
                        self.state.cambiar("idle")

            except Exception as e:
                print(f"❌ Error en detección: {e}")

            time.sleep(0.5)

    def parar(self):
        self.activo = False