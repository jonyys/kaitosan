from picamera2 import Picamera2
import cv2
import time

# Carga el detector de caras preentrenado
detector_caras = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

print("🔍 Iniciando detección de personas...")

picam = Picamera2()
config = picam.create_preview_configuration(
    main={"size": (640, 480)}
)
picam.configure(config)
picam.start()

print("✅ Cámara lista — detectando...")

hay_persona = False

while True:
    # Captura frame
    frame = picam.capture_array()
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

    # Convierte a escala de grises para el detector
    gris = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    # Detecta caras
    caras = detector_caras.detectMultiScale(
        gris,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    # ¿Hay alguien?
    if len(caras) > 0:
        if not hay_persona:
            print("✅ ¡Persona detectada! Alguien se ha sentado")
            hay_persona = True
    else:
        if hay_persona:
            print("👋 Persona se ha ido")
            hay_persona = False

    time.sleep(0.5)  # Comprueba cada 0.5 segundos