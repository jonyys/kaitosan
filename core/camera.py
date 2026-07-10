from picamera2 import Picamera2
import cv2

class Camera:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.picam = None

    def iniciar(self):
        try:
            self.picam = Picamera2()
            config = self.picam.create_preview_configuration(
                main={"size": (self.width, self.height)}
            )
            self.picam.configure(config)
            self.picam.start()
            print("✅ Cámara iniciada")
        except Exception as e:
            print(f"❌ Error iniciando cámara: {e}")
            self.picam = None

    def capturar_frame(self):
        if self.picam is None:
            return None
        frame = self.picam.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

    def generar_frames(self):
        while True:
            try:
                frame = self.capturar_frame()
                if frame is None:
                    break

                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n'
                       + buffer.tobytes() + b'\r\n')

            except Exception as e:
                print(f"❌ Error generando frame: {e}")
                break

    def disponible(self) -> bool:
        return self.picam is not None