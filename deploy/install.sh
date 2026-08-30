#!/bin/bash
# ---------------------------------------------------------------------------
# install.sh — deja una Raspberry Pi virgen lista para Kaito de una pasada.
# PLAN_AJUSTES.md fase 16 (§6, §8). Idempotente: se puede volver a lanzar.
#
# Copia a sus rutas del sistema:
#   deploy/kaito.service                  -> /etc/systemd/system/
#   deploy/kaitosan-wifi-connect.service  -> /etc/systemd/system/
#   deploy/5?-kaito-*.rules               -> /etc/polkit-1/rules.d/
#   deploy/90-kaito-backlight.rules       -> /etc/udev/rules.d/
#   deploy/kaito-mantenimiento.sudoers    -> /etc/sudoers.d/kaito-mantenimiento
#   onboarding/ui/                        -> /opt/wifi-connect/ui/
# Ajusta hostname (kaitosan.local), grupos (audio/video/bluetooth), venv,
# instala tzupdate, y hace daemon-reload + enable + restart.
#
# Uso:
#   sudo deploy/install.sh [--user NOMBRE] [--kiosk] [--wifi-connect] [--no-apt] [--no-venv]
#
#   --user NOMBRE   usuario del servicio (por defecto: $SUDO_USER o el dueño del repo o "kaitosan")
#   --kiosk         instala el autostart de Chromium en modo kiosco (§8.3)
#   --wifi-connect  descarga el binario balena-wifi-connect (§3.2) además de la UI
#   --no-apt        no toca apt (ni tzupdate ni avahi)
#   --no-venv       no crea/actualiza el entorno virtual
# ---------------------------------------------------------------------------
set -euo pipefail

KAITO_USER=""
DO_KIOSK=0
DO_WIFI_CONNECT=0
DO_APT=1
DO_VENV=1

while [ $# -gt 0 ]; do
  case "$1" in
    --user) KAITO_USER="${2:-}"; shift 2 ;;
    --kiosk) DO_KIOSK=1; shift ;;
    --wifi-connect) DO_WIFI_CONNECT=1; shift ;;
    --no-apt) DO_APT=0; shift ;;
    --no-venv) DO_VENV=0; shift ;;
    -h|--help) sed -n '3,23{s/^# \{0,1\}//;p}' "$0"; exit 0 ;;
    *) echo "opción desconocida: $1" >&2; exit 2 ;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  echo "Ejecuta con sudo:  sudo $0 $*" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$SCRIPT_DIR")"

if [ -z "$KAITO_USER" ]; then
  KAITO_USER="${SUDO_USER:-}"
  [ -z "$KAITO_USER" ] && KAITO_USER="$(stat -c '%U' "$REPO" 2>/dev/null || true)"
fi
if [ -z "$KAITO_USER" ] || [ "$KAITO_USER" = "root" ]; then
  KAITO_USER="kaitosan"
fi
id "$KAITO_USER" >/dev/null 2>&1 || { echo "El usuario '$KAITO_USER' no existe" >&2; exit 1; }

VENV="$REPO/venv"
HOSTNAME_NUEVO="kaitosan"

echo "==> Repo:    $REPO"
echo "==> Usuario: $KAITO_USER"
echo "==> Host:    $HOSTNAME_NUEVO  (-> http://$HOSTNAME_NUEVO.local:5000)"
echo

log() { printf '  \033[1;35m%s\033[0m\n' "$*"; }

# --- 1. Paquetes del sistema ------------------------------------------------
if [ "$DO_APT" -eq 1 ] && command -v apt-get >/dev/null 2>&1; then
  log "apt: tzupdate, avahi-daemon, network-manager, bluez, python3-venv"
  apt-get update -qq || echo "  (aviso: apt-get update falló; sigo con lo que haya)"
  apt-get install -y -qq tzupdate avahi-daemon network-manager bluez python3-venv \
    >/dev/null || echo "  (aviso: algún paquete no se pudo instalar; sigo)"
else
  log "apt: omitido"
fi

# --- 2. Grupos ------------------------------------------------------------------
log "grupos: audio, video, bluetooth -> $KAITO_USER"
for g in audio video bluetooth; do
  getent group "$g" >/dev/null 2>&1 && usermod -aG "$g" "$KAITO_USER" || true
done

# --- 3. Hostname / mDNS (§8.2) ------------------------------------------------
if [ "$(hostnamectl --static 2>/dev/null || true)" != "$HOSTNAME_NUEVO" ]; then
  log "hostname -> $HOSTNAME_NUEVO"
  hostnamectl set-hostname "$HOSTNAME_NUEVO"
fi
if grep -qE '^127\.0\.1\.1' /etc/hosts; then
  grep -qE "^127\.0\.1\.1[[:space:]]+$HOSTNAME_NUEVO(\$|[[:space:]])" /etc/hosts \
    || sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$HOSTNAME_NUEVO/" /etc/hosts
else
  printf '127.0.1.1\t%s\n' "$HOSTNAME_NUEVO" >> /etc/hosts
fi

# --- 4. Reglas polkit (§6.1-6.3, 6.7) --------------------------------------
log "polkit: reglas 5?-kaito-*.rules -> /etc/polkit-1/rules.d/"
install -d -m 0755 /etc/polkit-1/rules.d
for f in "$SCRIPT_DIR"/5?-kaito-*.rules; do
  [ -e "$f" ] || continue
  install -m 0644 -o root -g root "$f" "/etc/polkit-1/rules.d/$(basename "$f")"
done
systemctl try-restart polkit 2>/dev/null || true

# --- 5. Regla udev del brillo (§6.4) --------------------------------------
if [ -e "$SCRIPT_DIR/90-kaito-backlight.rules" ]; then
  log "udev: 90-kaito-backlight.rules -> /etc/udev/rules.d/"
  install -m 0644 -o root -g root "$SCRIPT_DIR/90-kaito-backlight.rules" \
    /etc/udev/rules.d/90-kaito-backlight.rules
  udevadm control --reload && udevadm trigger --subsystem-match=backlight || true
fi

# --- 6. sudoers acotado (§6.8) ------------------------------------------------
if [ -e "$SCRIPT_DIR/kaito-mantenimiento.sudoers" ]; then
  log "sudoers: kaito-mantenimiento -> /etc/sudoers.d/"
  tmp="$(mktemp)"
  sed "s/^kaitosan /$KAITO_USER /" "$SCRIPT_DIR/kaito-mantenimiento.sudoers" > "$tmp"
  if visudo -cf "$tmp" >/dev/null 2>&1; then
    install -m 0440 -o root -g root "$tmp" /etc/sudoers.d/kaito-mantenimiento
  else
    echo "  ERROR: el sudoers no valida, no lo instalo" >&2
  fi
  rm -f "$tmp"
fi

# --- 7. Entorno virtual + dependencias -------------------------------------
if [ "$DO_VENV" -eq 1 ]; then
  if [ ! -x "$VENV/bin/python" ]; then
    log "venv: creando en $VENV"
    sudo -u "$KAITO_USER" python3 -m venv "$VENV"
  fi
  log "venv: pip install -r requirements.txt"
  sudo -u "$KAITO_USER" "$VENV/bin/pip" install -q --upgrade pip
  sudo -u "$KAITO_USER" "$VENV/bin/pip" install -q -r "$REPO/requirements.txt"
else
  log "venv: omitido"
fi

# --- 8. Unidad systemd de la app (§8.1) -----------------------------------
log "systemd: kaito.service -> /etc/systemd/system/"
sed -e "s|^User=.*|User=$KAITO_USER|" \
    -e "s|^WorkingDirectory=.*|WorkingDirectory=$REPO|" \
    -e "s|^ExecStart=.*|ExecStart=$VENV/bin/python app.py|" \
    "$SCRIPT_DIR/kaito.service" > /etc/systemd/system/kaito.service

# --- 9. Onboarding WiFi (§3) ---------------------------------------------------
log "onboarding: UI -> /opt/wifi-connect/ui/"
install -d -m 0755 /opt/wifi-connect
rm -rf /opt/wifi-connect/ui
cp -r "$REPO/onboarding/ui" /opt/wifi-connect/ui

if [ "$DO_WIFI_CONNECT" -eq 1 ] && [ ! -x /opt/wifi-connect/wifi-connect ]; then
  case "$(uname -m)" in
    aarch64) WC_ARCH="aarch64-unknown-linux-gnu" ;;
    armv7l|armv6l) WC_ARCH="armv7-unknown-linux-gnueabihf" ;;
    x86_64) WC_ARCH="x86_64-unknown-linux-gnu" ;;
    *) WC_ARCH="" ;;
  esac
  if [ -n "$WC_ARCH" ] && command -v curl >/dev/null 2>&1; then
    log "onboarding: descargando binario wifi-connect ($WC_ARCH)"
    curl -Ls "https://github.com/balena-os/wifi-connect/releases/latest/download/wifi-connect-$WC_ARCH.tar.gz" \
      -o /tmp/wifi-connect.tgz && tar -xzf /tmp/wifi-connect.tgz -C /opt/wifi-connect \
      && rm -f /tmp/wifi-connect.tgz
  else
    echo "  (no sé qué binario bajar para $(uname -m); hazlo a mano, ver la cabecera del .service)"
  fi
fi

if [ -e "$SCRIPT_DIR/kaitosan-wifi-connect.service" ]; then
  log "systemd: kaitosan-wifi-connect.service -> /etc/systemd/system/"
  install -m 0644 -o root -g root "$SCRIPT_DIR/kaitosan-wifi-connect.service" \
    /etc/systemd/system/kaitosan-wifi-connect.service
fi

# --- 10. Kiosco Chromium (opcional, §8.3) --------------------------------
if [ "$DO_KIOSK" -eq 1 ]; then
  log "kiosco: /usr/local/bin/kaito-kiosk.sh + /etc/xdg/autostart/"
  install -m 0755 "$SCRIPT_DIR/kaito-kiosk.sh" /usr/local/bin/kaito-kiosk.sh
  install -d -m 0755 /etc/xdg/autostart
  install -m 0644 "$SCRIPT_DIR/kaito-kiosk.desktop" /etc/xdg/autostart/kaito-kiosk.desktop
  echo "  (en Wayland/wayfire quizá haya que añadir kaito-kiosk.sh a ~/.config/wayfire.ini)"
fi

# --- 11. Arrancar ---------------------------------------------------------------
log "systemd: daemon-reload + enable + restart"
systemctl daemon-reload
systemctl enable kaito.service >/dev/null 2>&1 || true
systemctl enable kaitosan-wifi-connect.service >/dev/null 2>&1 || true
systemctl restart kaito.service || echo "  AVISO: kaito no arrancó — revisa 'journalctl -u kaito -n 50'"

echo
echo "==> Listo. El panel está en:  http://$HOSTNAME_NUEVO.local:5000"
echo "    Estado:   systemctl status kaito --no-pager"
echo "    Logs:     journalctl -u kaito -f"
echo "    NOTA: si '$KAITO_USER' tenía sesión abierta, que vuelva a entrar para que"
echo "          los grupos audio/video/bluetooth tengan efecto (el servicio ya los tiene"
echo "          vía SupplementaryGroups)."
