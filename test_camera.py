from picamera2 import Picamera2
import time

print("🔍 Iniciando cámara...")

picam = Picamera2()
config = picam.create_preview_configuration(
    main={"size": (640, 480)}
)
picam.configure(config)
picam.start()

print("✅ Cámara iniciada correctamente")
time.sleep(2)

# Captura un frame de prueba
frame = picam.capture_array()
print(f"✅ Frame capturado: {frame.shape}")

picam.stop()
print("✅ Cámara funciona perfectamente")