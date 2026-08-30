#!/bin/bash
# Abre el panel de Kaito a pantalla completa en la pantalla del propio robot.
# Lo lanza /etc/xdg/autostart/kaito-kiosk.desktop al iniciar el escritorio (§8.3).
# Laura no necesita IP ni nombre: el panel de Ajustes se abre desde otro
# dispositivo por http://kaitosan.local:5000.
set -u

URL="http://localhost:5000"

# Espera a que el servicio kaito responda (hasta ~2 min).
for _ in $(seq 1 60); do
  if command -v curl >/dev/null 2>&1; then
    curl -sf -o /dev/null "$URL" && break
  else
    </dev/tcp/localhost/5000 && break
  fi
  sleep 2
done 2>/dev/null

# Chromium: "chromium-browser" en Bullseye, "chromium" en Bookworm.
BIN="$(command -v chromium-browser || command -v chromium || true)"
[ -z "$BIN" ] && { echo "kaito-kiosk: no encuentro chromium" >&2; exit 0; }

exec "$BIN" \
  --kiosk --incognito --noerrdialogs --disable-infobars \
  --disable-session-crashed-bubble --disable-features=TranslateUI \
  --check-for-update-interval=31536000 \
  --overscroll-history-navigation=0 \
  --autoplay-policy=no-user-gesture-required \
  "$URL"
