import subprocess
import threading

try:
    from gpiozero import Button as _Button
    _GPIO_DISPONIBLE = True
except Exception:
    _GPIO_DISPONIBLE = False


class PowerButton:
    """
    Pulsación corta → on_short_press()
    Pulsación larga (hold_time seg) → sudo shutdown -h now
    Pulsar para hablar: si on_press() devuelve True (en modo sensei), esa pulsación es de hablar: al
    soltar se llama a on_release() y mantenerlo NUNCA apaga la Pi.
    """

    def __init__(self, on_short_press, pin=3, hold_time=3, on_press=None, on_release=None):
        self._on_short = on_short_press
        self._on_press = on_press
        self._on_release = on_release
        self._held = False
        self._hablando = False

        if not _GPIO_DISPONIBLE:
            print("⚠️  PowerButton: gpiozero no disponible, botón desactivado")
            return

        btn = _Button(pin, pull_up=True, hold_time=hold_time)
        btn.when_pressed = self._on_pressed
        btn.when_held = self._on_held
        btn.when_released = self._on_released
        self._btn = btn
        print(f"🔘 PowerButton iniciado en GPIO {pin}")

    def _on_pressed(self):
        self._hablando = False
        if self._on_press:
            try:
                self._hablando = bool(self._on_press())
            except Exception as e:  # noqa: BLE001 — un fallo aquí no puede dejar el botón muerto
                print(f"⚠️ Botón: error al empezar a escuchar: {e}")

    def _on_held(self):
        if self._hablando:  # manteniéndolo en sensei se habla, no se apaga
            return
        self._held = True
        print("🔴 Apagando Pi...")
        subprocess.run(["sudo", "shutdown", "-h", "now"])

    def _on_released(self):
        if self._hablando:
            self._hablando = False
            if self._on_release:
                self._on_release()
        elif not self._held:
            threading.Thread(target=self._on_short, daemon=True).start()
        self._held = False
