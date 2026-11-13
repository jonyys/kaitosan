#!/bin/bash
# Instala la pantalla de arranque/apagado de Kaito (Plymouth) y la de carga del kiosko.
#   sudo deploy/instalar-splash.sh            # instala (antes hace copia de seguridad)
#   sudo deploy/instalar-splash.sh --quitar   # vuelve al estado de la última copia
#
# Qué toca: /boot/firmware/{cmdline.txt,config.txt,initramfs8}, el tema de Plymouth
# (/etc/plymouth/plymouthd.conf), /usr/local/bin/kaito-kiosk.sh y los archivos del tema.
# Copia de seguridad: ~/respaldo-arranque/<fecha>/ y, para poder recuperar con la SD en
# un PC (la partición de arranque se lee en Windows), /boot/firmware/respaldo-arranque/.
# Si algo no cuadra se deshace solo antes de seguir. Probado el flujo por pasos: cada uno
# comprueba el anterior.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "ejecútalo con sudo" >&2; exit 1; }

SRC="$(cd "$(dirname "$0")" && pwd)"
USUARIO="${SUDO_USER:-kaitosan}"
CASA="$(getent passwd "$USUARIO" | cut -d: -f6)"
BOOT=/boot/firmware
CMD=$BOOT/cmdline.txt
CFG=$BOOT/config.txt
INITRD=$BOOT/initramfs8
CONF=/etc/plymouth/plymouthd.conf
THEME=/usr/share/plymouth/themes/kaito
LAB="$CASA/.config/labwc"
RESP_BASE="$CASA/respaldo-arranque"
RESP_BOOT=$BOOT/respaldo-arranque

restaurar() {   # $1 = carpeta de copia
  local d="$1"
  echo "restaurando desde $d"
  cp "$d/cmdline.txt" "$CMD"
  cp "$d/config.txt" "$CFG"
  [ -f "$d/plymouthd.conf" ] && cp "$d/plymouthd.conf" "$CONF"
  [ -f "$d/initramfs8" ] && cp "$d/initramfs8" "$INITRD"
  [ -f "$d/kaito-kiosk.sh" ] && install -m 0755 "$d/kaito-kiosk.sh" /usr/local/bin/kaito-kiosk.sh
  [ -f "$d/labwc-environment" ] && cp "$d/labwc-environment" "$LAB/environment"
  [ -f "$d/labwc-rc.xml" ] && cp "$d/labwc-rc.xml" "$LAB/rc.xml"
  if [ -f "$d/labwc-autostart" ]; then cp "$d/labwc-autostart" "$LAB/autostart"; else rm -f "$LAB/autostart"; fi
  [ -f "$d/labwc-autostart-sistema" ] && cp "$d/labwc-autostart-sistema" /etc/xdg/labwc/autostart
  sync
}

if [ "${1:-}" = "--quitar" ]; then
  ULTIMA="$(ls -1d "$RESP_BASE"/*/ 2>/dev/null | tail -n 1 || true)"
  [ -n "$ULTIMA" ] || { echo "no hay copias en $RESP_BASE" >&2; exit 1; }
  restaurar "${ULTIMA%/}"
  rm -f /usr/local/share/kaito/arranque/index.html   # el kiosko vuelve a esperar al servicio
  echo "restaurado; reinicia para ver el arranque anterior"; exit 0
fi

# 1) Comprobaciones previas: nada se toca si falta algo.
for f in "$CMD" "$CFG" "$INITRD" "$CONF" "$SRC/arranque/index.html" "$SRC/plymouth/kaito/kaito.script" \
         "$SRC/plymouth/kaito/fondo.png" "$SRC/kaito-kiosk.sh" "$SRC/labwc/autostart" \
         "$SRC/labwc/crear-cursor-vacio.py" "$LAB/environment"; do
  [ -f "$f" ] || { echo "falta $f: no hago nada" >&2; exit 1; }
done
grep -q 'root=' "$CMD" || { echo "cmdline.txt sin root=: no hago nada" >&2; exit 1; }

# 2) Copia de seguridad (dos sitios).
FECHA="$(date +%Y%m%d-%H%M%S)"
RESP="$RESP_BASE/$FECHA"
install -d -m 0755 "$RESP" "$RESP_BOOT"
cp "$CMD" "$CFG" "$INITRD" "$RESP/"
cp "$CONF" "$RESP/plymouthd.conf"
cp /usr/local/bin/kaito-kiosk.sh "$RESP/kaito-kiosk.sh" 2>/dev/null || true
cp "$LAB/environment" "$RESP/labwc-environment"
cp "$LAB/rc.xml" "$RESP/labwc-rc.xml" 2>/dev/null || true
if [ -f "$LAB/autostart" ]; then cp "$LAB/autostart" "$RESP/labwc-autostart"; fi
cp /etc/xdg/labwc/autostart "$RESP/labwc-autostart-sistema"
[ -f /etc/xdg/labwc/autostart.orig-pi ] || cp /etc/xdg/labwc/autostart /etc/xdg/labwc/autostart.orig-pi   # el original de Raspberry Pi OS, una sola vez
plymouth-set-default-theme > "$RESP/tema-anterior.txt" 2>/dev/null || true
cp "$CMD" "$CFG" "$INITRD" "$RESP_BOOT/"
chown -R "$USUARIO": "$RESP_BASE"
sync
echo "copia de seguridad en $RESP y en $RESP_BOOT"

# 3) Archivos del tema y de la pantalla de carga.
install -d -m 0755 "$THEME" /usr/local/share/kaito/arranque
rm -f "$THEME"/*.png   # quita las imágenes del diseño anterior
install -m 0644 "$SRC"/plymouth/kaito/{kaito.plymouth,kaito.script,fondo.png,apagado.png,perla.png,negro.png,tabla*.png} "$THEME/"
install -m 0644 "$SRC/arranque/index.html" /usr/local/share/kaito/arranque/index.html
install -m 0755 "$SRC/kaito-kiosk.sh" /usr/local/bin/kaito-kiosk.sh

# 3b) Sesión sin escritorio (sin barra, fondo ni avisos de red) y sin puntero de ratón.
install -d -o "$USUARIO" -g "$USUARIO" "$LAB" "$CASA/.config/kaito" "$CASA/.icons"
# labwc arranca con -m: mezcla la configuración del sistema y la del usuario, y corren los DOS autostart.
# Por eso el del sistema (el que lanza el escritorio y la barra) se sustituye por el de Kaito y se quita el
# del usuario, para que nada corra dos veces. (Con una actualización de labwc-pi puede volver el original.)
install -m 0644 "$SRC/labwc/autostart" /etc/xdg/labwc/autostart
rm -f "$LAB/autostart"
python3 "$SRC/labwc/crear-cursor-vacio.py" "$CASA/.icons/vacio"
chown -R "$USUARIO": "$CASA/.icons/vacio"
grep -q '^XCURSOR_THEME=' "$LAB/environment" || echo 'XCURSOR_THEME=vacio' >> "$LAB/environment"

# 4) Tema nuevo + regenerar initramfs; si el tema no entra, se deshace antes de tocar el arranque.
plymouth-set-default-theme -R kaito
if ! lsinitramfs "$INITRD" | grep -q 'themes/kaito/kaito.script'; then
  echo "el initramfs no contiene el tema: restauro y paro" >&2
  restaurar "$RESP"
  exit 1
fi

# 5) Arranque en silencio.
linea="$(tr -d '\n' < "$CMD")"
linea="${linea//console=tty1/console=tty3}"          # el texto del kernel no sale en la pantalla
for p in quiet splash loglevel=3 logo.nologo vt.global_cursor_default=0; do
  case " $linea " in *" $p "*) ;; *) linea="$linea $p" ;; esac
done
echo "$linea" > "$CMD"
grep -q '^disable_splash=1' "$CFG" || sed -i '0,/^\[all\]/s//[all]\ndisable_splash=1/' "$CFG"
if ! grep -q 'root=' "$CMD" || [ "$(wc -l < "$CMD")" -ne 1 ]; then
  echo "cmdline.txt quedó mal: restauro" >&2; restaurar "$RESP"; exit 1
fi
sync
echo "listo. Reinicia para verlo. Para deshacerlo: sudo $0 --quitar"
echo "Si no arrancara: saca la SD, abre en un PC la partición 'bootfs' y copia de respaldo-arranque/ cmdline.txt y config.txt encima de los de la raíz."
