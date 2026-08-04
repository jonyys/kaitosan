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
    """

    def __init__(self, on_short_press, pin=3, hold_time=3):
        self._on_short = on_short_press
        self._held = False

        if not _GPIO_DISPONIBLE:
            print("⚠️  PowerButton: gpiozero no disponible, botón desactivado")
            return

        btn = _Button(pin, pull_up=True, hold_time=hold_time)
        btn.when_held = self._on_held
        btn.when_released = self._on_released
        self._btn = btn
        print(f"🔘 PowerButton iniciado en GPIO {pin}")

    def _on_held(self):
        self._held = True
        print("🔴 Apagando Pi...")
        subprocess.run(["sudo", "shutdown", "-h", "now"])

    def _on_released(self):
        if not self._held:
            threading.Thread(target=self._on_short, daemon=True).start()
        self._held = False
