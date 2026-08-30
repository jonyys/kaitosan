# Plan — Panel de Ajustes de la Pi + Onboarding WiFi

Objetivo: que Kaito funcione como un aparato comprado. Laura lo enchufa en su casa,
elige su WiFi desde el móvil y, a partir de ahí, controla **todos** los ajustes de la
Raspberry (hora, WiFi, Bluetooth, audio, brillo, modelos de IA, mantenimiento…) desde una
pantalla web con usuario y contraseña, con el mismo estilo que el resto del panel de admin.

La web es **móvil primero** (el 95% de los accesos son desde el móvil, táctiles, sin ratón)
y además tiene que verse bien en la **pantalla táctil redonda de ~2.8" del propio robot**
(≈ 480×480 px, circular). Estética pastel rosa y responsive de verdad: ver §13.

---

## 1. Arquitectura: dos capas

| Capa | Cuándo actúa | Herramienta | Para qué |
|---|---|---|---|
| **Onboarding** | La Pi **no tiene conexión** (primer arranque en casa nueva, o se perdió el WiFi) | `balena-wifi-connect` + systemd | La Pi crea su propio WiFi `Kaitosan-Setup`; Laura mete su red desde el móvil |
| **Ajustes** | La Pi **ya tiene conexión** | Rutas nuevas en `app.py` (`/admin/ajustes`) + `core/system_settings.py` | Cambiar WiFi, Bluetooth, hora, audio, brillo, modelos de IA, actualizar, reiniciar… desde la web normal |

Las dos capas hablan con **NetworkManager**, así que no se pisan. Y se complementan:
si desde Ajustes cambias a un WiFi que falla y la Pi se queda sin conexión, el
onboarding vuelve a levantar el portal solo → red de seguridad automática.

Requisito de sistema: **Raspberry Pi OS Bookworm** (usa NetworkManager por defecto).
En Bullseye habría que migrar de `dhcpcd`/`wpa_supplicant` a NetworkManager primero
(`sudo raspi-config` → Advanced → Network Config → NetworkManager).

Supuesto en todo el documento: el proyecto corre como **servicio systemd de sistema**
con el usuario `kaito` (ajusta el nombre si usas `pi`). Unidad de ejemplo en §8.

---

## 2. Inventario de ajustes (alcance)

| Ajuste | Cómo se hace por debajo | Viabilidad |
|---|---|---|
| Ver/cambiar **WiFi**, escanear redes, olvidar red | `nmcli` (D-Bus NetworkManager) | ✅ |
| **Hora y fecha** manual | `timedatectl set-time` | ✅ |
| **Hora automática** (NTP) on/off | `timedatectl set-ntp true/false` | ✅ |
| **Zona horaria** manual (desplegable) | `timedatectl set-timezone` + `list-timezones` | ✅ |
| **Zona horaria automática por ubicación** | `tzupdate` (geolocaliza por IP) → `set-timezone` | ✅ (hace 1 petición saliente a un servicio geo; avisar) |
| **Volumen** | `amixer` sobre la tarjeta ALSA (o `wpctl` si PipeWire de usuario) | ✅ |
| **Brillo de pantalla** | escribir en `/sys/class/backlight/*/brightness` | ✅ solo pantalla oficial DSI/SPI; monitor HDMI normalmente **no** |
| **Reiniciar / apagar** | `systemctl reboot` / `poweroff` (logind) | ✅ |
| **Nombre del equipo** (`kaitosan.local`) | `hostnamectl set-hostname` | ✅ (opcional) |
| Cambiar **usuario/contraseña** del panel | tabla `app_settings` en SQLite | ✅ |

### 2.1 Ampliación del alcance (v1 y backlog)

> Aquí "v1" y "backlog" son **alcance** (qué entra en la primera entrega y qué se deja para
> después). El **trabajo** se parte en fases pequeñas numeradas en §9 ("Fase 1", "Fase 2"…),
> que son otra cosa: cada una es una conversación nueva.

**Alcance v1** — entra en la primera versión de Ajustes, junto a la tabla de arriba:

| Ajuste | Cómo se hace por debajo | Viabilidad |
|---|---|---|
| **Bluetooth**: adaptador on/off, escanear, emparejar, conectar, olvidar | `bluetoothctl` (D-Bus BlueZ) | ✅ |
| **Dispositivo de salida de audio** (hifiberry / G435 / altavoz BT / HDMI) | listar tarjetas ALSA (+ sinks BT) y guardar preferencia; sustituye a `AUDIO_OUTPUT_HINT` | ✅ |
| **Dispositivo de entrada** (micrófono) | ídem; sustituye a `AUDIO_INPUT_HINT` | ✅ |
| **Ganancia del micrófono** | `amixer sset Capture` sobre la tarjeta de entrada | ✅ |
| **Probar sonido / probar micro** | reproducir un wav corto / grabar 2 s y reproducir | ✅ |
| **Silenciar micrófono** (interruptor de privacidad) | corta la escucha en el propio proceso (no toca ALSA) | ✅ |
| **Modelos de Groq** que consume Kaito (principal, sensei, alternativos, con tools) | `GET https://api.groq.com/openai/v1/models` con la API key → lista real; la selección se guarda en `app_settings` y **sobrescribe** los valores fijos de `core/config.py` / `GroqProvider` | ✅ |
| **Actualizar Kaito** | `git pull` + `pip install -r` + `systemctl restart kaito` (en hilo, con aviso) | ✅ |
| **Reiniciar solo el servicio** | `systemctl restart kaito` (sin reiniciar la Pi entera) | ✅ |
| **Ver logs** | `journalctl -u kaito -n 200 --no-pager` | ✅ |
| **Salud del sistema** | temperatura, `vcgencmd get_throttled`, CPU/RAM, disco, uptime | ✅ (amplía `sistema_info()`) |
| **Copia de seguridad / restaurar BD** | descargar / subir `kaito.db` | ✅ |
| **Descargar diagnóstico** | zip con logs + config **sin secretos** para soporte | ✅ |
| **Reset de fábrica** | borra BD, credenciales y redes WiFi → vuelve al onboarding; pide PIN | ✅ |

**Backlog** — cuando la v1 esté estable en la Pi (detalle y mecanismo en §12):
horario "no molestar", apagado de pantalla por inactividad / horario nocturno,
rotación y tema de la cara, cámara y detección de rostro on/off, modo al
arrancar (charla/sensei), `AZURE_PRON_EN_CHARLA` como interruptor, barra de cuota de
Azure y de tokens/coste, QR con la URL del panel, "probar Internet", SSID oculto,
modo avión, reinicio diario programado (cron), formato de hora 12/24, ciudad por
defecto de la skill del tiempo, tono/volumen de alarma, cerrar todas las sesiones,
restringir el panel a la LAN, PIN para acciones peligrosas.

La **voz / TTS de Kaito** (velocidad, pausas ES/JP, silencio inicial, volumen relativo) y
el **wakeword** (on/off, sensibilidad) quedan **fuera de Ajustes** a propósito: se afinan
solo por `.env` / código.

---

## 3. Parte 1 — Onboarding WiFi con `balena-wifi-connect` (UI propia)

### 3.1 Qué es
Un binario que, cuando se lanza, levanta un punto de acceso y sirve una web mínima con
dos endpoints:

- `GET /network s` → lista de redes visibles (JSON)
- `POST /connect` → `{ ssid, identity, passphrase }` → NetworkManager se conecta y el AP se apaga

La UI que sirve es una carpeta estática. **Podemos sustituirla entera** siempre que
llame a esos dos endpoints. Ese es el punto de personalización.

### 3.2 Instalación en la Pi
```bash
# binario ARM oficial (elegir la release y arquitectura correctas: aarch64 en Pi 4/5 de 64 bits)
cd /tmp
curl -Ls https://github.com/balena-os/wifi-connect/releases/latest/download/wifi-connect-aarch64-unknown-linux-gnu.tar.gz -o wc.tar.gz
sudo mkdir -p /opt/wifi-connect/ui
sudo tar -xzf wc.tar.gz -C /opt/wifi-connect
# el .tar.gz trae el binario `wifi-connect` y una carpeta `ui/` de ejemplo
```

### 3.3 UI personalizada
1. Copia la `ui/` de ejemplo a `kaitosan/onboarding/ui/` **dentro del repo** (así va versionada).
2. Rehazla con la **paleta pastel de Kaito** (§13): fondo blush, tarjetas blancas, rosa
   pastel de acento, tipografía redondeada, logo 🤖🌸, textos en español. Reutiliza los
   mismos tokens CSS que el panel. Puede ser un `index.html` único con CSS y JS embebidos;
   no necesita framework.
3. Contrato mínimo que tu JS debe cumplir:
   ```js
   // listar redes
   const redes = await fetch('/networks').then(r => r.json());
   // conectar
   await fetch('/connect', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({ ssid, identity: '', passphrase })
   });
   ```
4. En el `deploy`, copia `kaitosan/onboarding/ui/` a `/opt/wifi-connect/ui/`.

### 3.4 Servicio + disparador (solo si no hay conexión)
`/etc/systemd/system/kaitosan-wifi-connect.service`:
```ini
[Unit]
Description=Kaito WiFi onboarding portal
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=simple
ExecStartPre=/usr/bin/nm-online -s -q --timeout=30
ExecStartPre=/bin/bash -c '/usr/bin/nmcli -t -f STATE g | grep -q "connected" && exit 1 || exit 0'
ExecStart=/opt/wifi-connect/wifi-connect \
  --portal-ssid "Kaitosan-Setup" \
  --portal-listening-port 80 \
  --activity-timeout 0 \
  --ui-directory /opt/wifi-connect/ui
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```
- El primer `ExecStartPre` espera a que NetworkManager termine de intentar conectarse.
- El segundo aborta el arranque **si ya hay conexión** (así el portal solo aparece cuando hace falta).
- `--portal-ssid "Kaitosan-Setup"`: nombre del WiFi temporal. Opcional `--portal-passphrase "..."` para protegerlo.
- `--activity-timeout 0`: no se rinde solo; se queda esperando a Laura.

Habilitar: `sudo systemctl enable kaitosan-wifi-connect`.
Para recuperación en caliente (Laura quiere re-configurar): un botón físico o una opción
en Ajustes que haga `nmcli con down <actual>` y `systemctl start kaitosan-wifi-connect`.

### 3.5 Pruebas
- En la Pi: `sudo nmcli radio wifi off && sudo systemctl start kaitosan-wifi-connect`
  → con el móvil, conéctate a `Kaitosan-Setup`, comprueba que sale tu UI y que conecta.
- La UI en sí se puede maquetar en el portátil abriendo el `index.html` y mockeando
  `/networks` con datos falsos.

---

## 4. Parte 2 — Autenticación con usuario + contraseña

Hoy `app.py` sólo comprueba `ADMIN_PASSWORD` (una cadena en claro en `.env`). Cambios:

### 4.1 Almacén de ajustes de la app
Nuevo módulo `core/settings_store.py` con una tabla en la BD que ya existe
(`brain.memory._conectar()`), o un fichero JSON `config/ajustes.json`. Recomendado tabla:
```sql
CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
```
API: `get(key, default=None)`, `set(key, value)`. Guarda:
- `admin_user` (por defecto `"laura"`)
- `admin_pass_hash` (werkzeug `generate_password_hash`)
- `tz_auto` → `"1"`/`"0"`
- `audio_output`, `audio_input` (nombre de tarjeta; precede a los `*_HINT` del `.env`)  [v1]
- `groq_models` (JSON: `{principal, sensei, alternativos:[...], tools:[...]}`)  [v1]
- `pin_hash` (acciones peligrosas), `modo_inicial`, `weather_ciudad`, … (backlog)

Primera vez: si no hay `admin_pass_hash`, se siembra con `ADMIN_USER`/`ADMIN_PASSWORD`
del `.env` (retrocompatibilidad) y se hashea.

### 4.2 `core/config.py`
```python
ADMIN_USER     = os.getenv("ADMIN_USER", "laura")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kaito123")  # solo semilla inicial
```

### 4.3 `app.py` — login
```python
from werkzeug.security import check_password_hash, generate_password_hash
from core.settings_store import settings_get, settings_set

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = request.form.get("user", "").strip()
        pwd  = request.form.get("password", "")
        if user == settings_get("admin_user") and \
           check_password_hash(settings_get("admin_pass_hash"), pwd):
            session.permanent = True
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        return render_template("admin_login.html", error="Usuario o contraseña incorrectos")
    return render_template("admin_login.html")
```

### 4.4 `templates/admin_login.html`
Añadir un `<input name="user" placeholder="Usuario" autofocus>` antes del de contraseña.
El resto del estilo ya vale.

### 4.5 Cambiar credenciales desde Ajustes
POST `/admin/ajustes/cuenta` con `user`, `password_actual`, `password_nueva` →
verifica la actual, guarda `admin_user` y `admin_pass_hash`, `flash()` y redirect.

`requirements.txt`: `werkzeug` ya viene con Flask, no hace falta añadir nada.

---

## 5. Parte 3 — `core/system_settings.py` (capa de sistema)

Módulo único que envuelve los comandos del SO. Reglas:
- Siempre `subprocess.run([...], capture_output=True, text=True, timeout=15)`, **nunca** `shell=True`.
- Cada función devuelve un `dict` con datos ya parseados o `{"error": "..."}`.
- Validar entradas antes de pasarlas (SSID/timezone contra lista blanca, brillo/volumen a rango).

```python
# --- WiFi (NetworkManager) ---
def wifi_estado() -> dict          # {conectado, ssid, señal, ip}
def wifi_escanear() -> list[dict]  # [{ssid, señal, seguridad, en_uso}]
def wifi_guardadas() -> list[str]
def wifi_conectar(ssid, psk) -> dict
def wifi_olvidar(ssid) -> dict
def wifi_abrir_portal() -> dict    # baja la conexión y arranca kaitosan-wifi-connect

# --- Hora ---
def hora_estado() -> dict          # {hora, zona, ntp, tz_auto}
def hora_set_manual(iso) -> dict   # requiere ntp=off
def hora_set_ntp(on: bool) -> dict
def zona_listar() -> list[str]     # timedatectl list-timezones (cachear)
def zona_set(tz) -> dict
def zona_auto(on: bool) -> dict    # on -> tzupdate; guarda pref en app_settings

# --- Sonido ---
def volumen_get() -> int           # 0..100
def volumen_set(pct: int) -> dict  # amixer -M sset sobre la tarjeta de salida

# --- Pantalla ---
def brillo_get() -> dict           # {soportado: bool, valor, max}
def brillo_set(pct: int) -> dict

# --- Sistema ---
def sistema_info() -> dict         # hostname, modelo, uptime, temperatura, disco
def hostname_set(nombre) -> dict
def reiniciar() -> None
def apagar() -> None

# --- Bluetooth (BlueZ / bluetoothctl) ---  [v1]
def bt_estado() -> dict            # {adaptador_on, conectados:[{mac,nombre,tipo}]}
def bt_radio(on: bool) -> dict
def bt_escanear(seg: int = 10) -> list[dict]   # [{mac,nombre,tipo,emparejado,conectado,rssi}]
def bt_emparejados() -> list[dict]
def bt_conectar(mac) -> dict       # pair + trust + connect (en ese orden)
def bt_desconectar(mac) -> dict
def bt_olvidar(mac) -> dict        # bluetoothctl remove <mac>

# --- Audio: selección de dispositivo ---  [v1]
def audio_salidas() -> list[dict]  # [{id, nombre, en_uso}]  (tarjetas ALSA + sinks BT)
def audio_entradas() -> list[dict]
def audio_salida_set(id) -> dict   # guarda pref en app_settings (sustituye AUDIO_OUTPUT_HINT)
def audio_entrada_set(id) -> dict  # idem AUDIO_INPUT_HINT
def micro_ganancia_get() -> int    # 0..100
def micro_ganancia_set(pct) -> dict
def audio_probar_salida() -> dict  # reproduce un wav corto por la salida activa
def audio_probar_micro() -> dict   # graba 2 s y lo reproduce

# --- Modelos de IA (Groq) ---  [v1]
def groq_modelos() -> list[dict]   # GET /openai/v1/models con la API key; cachear ~1 h
def groq_seleccion_get() -> dict   # {principal, sensei, alternativos:[...], tools:[...]}
def groq_seleccion_set(sel) -> dict  # valida contra groq_modelos() y guarda en app_settings

# --- Mantenimiento ---  [v1]
def salud() -> dict                # temp, throttled(vcgencmd get_throttled), cpu, ram, disco, uptime
def logs(n: int = 200) -> str      # journalctl -u kaito -n <n> --no-pager
def actualizar() -> dict           # git pull + pip install -r + restart (en hilo; responde antes)
def reiniciar_servicio() -> dict   # systemctl restart kaito
def backup_bd() -> str             # ruta a una copia de kaito.db para descargar
def restaurar_bd(fichero) -> dict  # valida que es SQLite, reemplaza y reinicia el servicio
def diagnostico_zip() -> str       # zip: logs + config SIN secretos
def reset_fabrica(pin) -> dict     # borra kaito.db, claves de app_settings y conexiones NM
```

Notas de implementación:
- **WiFi escanear**: `nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list --rescan yes`.
  Separar por `:` teniendo en cuenta el escape de `nmcli` (`\:` dentro de un SSID).
- **WiFi conectar**: `nmcli dev wifi connect <ssid> password <psk>`. Ojo: esto **desconecta
  la red actual**. Ver §7 (UX del cambio de WiFi).
- **tzupdate**: `pip install tzupdate` o `apt install tzupdate`. Hace 1 GET a un servicio de
  geolocalización por IP y llama a `timedatectl`. Documentar esa petición saliente.
- **Volumen**: la tarjeta de salida depende de `AUDIO_OUTPUT_HINT` (hifiberry vs G435).
  Reutiliza la lógica de autodetección que ya tienes en audio para elegir `-c <card>` y el
  nombre del control (`PCM`, `Master`, `Speaker`…). Exponer `AJUSTES_MIXER_CONTROL` en `.env`
  como escape, igual que hiciste con los hints de audio.
- **Brillo**: al arrancar, `glob('/sys/class/backlight/*')`. Si no hay ninguno →
  `brillo_get()` devuelve `{soportado: false}` y la tarjeta se oculta en la UI.
  Pantalla oficial de 7": suele ser `10-0045` / `rpi_backlight` (Bullseye) o `6-0045` (Bookworm).
- **temperatura**: `vcgencmd measure_temp` o `/sys/class/thermal/thermal_zone0/temp`.
- **Bluetooth**: `bluetoothctl` es interactivo; usarlo en modo no interactivo con
  `bluetoothctl --timeout N scan on` para el escaneo y pasando comandos por stdin para el
  resto (`printf 'pair %s\nquit\n' "$MAC" | bluetoothctl`). Parsear `devices` e `info <mac>`.
  Si el dispositivo emparejado es de audio (`Icon: audio-card` / UUID A2DP), tras conectar
  refrescar `audio_salidas()` para que aparezca como salida elegible. Fallback obligatorio:
  si el sink BT desaparece (fuera de rango), volver a la tarjeta local.
- **Selección de audio**: al elegir salida/entrada se guarda en `app_settings`
  (`audio_output`, `audio_input`). El arranque de audio lee **primero** esa preferencia y
  solo si está vacía usa `AUDIO_OUTPUT_HINT` / `AUDIO_INPUT_HINT` del `.env` (que pasan a ser
  semilla / override de fábrica). Reutilizar la autodetección que ya existe para resolver el
  `id` guardado a tarjeta concreta (los índices ALSA bailan entre arranques; guardar el
  nombre, no el número).
- **Modelos de Groq**: `GET https://api.groq.com/openai/v1/models` con cabecera
  `Authorization: Bearer $GROQ_API_KEY` devuelve `{data:[{id, active, context_window,
  owned_by, ...}]}`. Para los desplegables de chat: filtrar `active == true` y excluir los de
  audio (`whisper`, `tts`). La selección guardada (`groq_models` en `app_settings`, JSON con
  `principal`, `sensei`, `alternativos`, `tools`) **sobrescribe** `DEFAULT_MODEL`,
  `MODEL_SENSEI`, `GroqProvider.modelos_alternativos` y `GroqProvider.modelos_tools`; esos
  valores del código pasan a ser el *default* si no hay nada guardado. En cada arranque,
  validar la selección contra la lista real y descartar los modelos retirados
  (`decommissioned` / `model_not_found`) cayendo al default — el `_saltar_modelo()` de
  `groq_provider.py` ya cubre el caso en caliente. Mostrar junto a cada modelo los tokens
  consumidos hoy (ya está en `core/token_tracker.py`). Esta llamada **sí funciona en el
  portátil** (es HTTP), así que en modo simulado se puede dejar real y mockear solo el resto.
- **actualizar()**: responder al `fetch` antes de ejecutar; correr en
  `threading.Thread(daemon=True)`; guardar el commit anterior (`git rev-parse HEAD`) para
  ofrecer "volver a la versión anterior"; nunca auto-actualizar. Al final, `systemctl restart
  kaito` corta la sesión un momento → mismo aviso que el cambio de WiFi (§7.4).
- **reiniciar_servicio() / actualizar()**: el servicio corre como `kaito` sin root; necesita
  `sudo` acotado solo para `systemctl restart kaito` (ver §6.8). El `git pull` / `pip` corren
  como `kaito` en su propio checkout, sin sudo.
- **reset_fabrica()**: borra `kaito.db`, las claves de `app_settings` y las conexiones de
  NetworkManager (`for c in $(nmcli -g NAME con show); do nmcli con delete "$c"; done`), luego
  `systemctl start kaitosan-wifi-connect`. Doble confirmación + PIN corto.
- **diagnostico_zip()**: incluir `journalctl -u kaito`, `.env` **con los valores de claves
  ofuscados**, salida de `salud()` y `nmcli dev status`. Revisar a mano que no se cuela ningún
  secreto antes de dar el enlace de descarga.

### Pruebas fuera de la Pi
En Windows/Mac los comandos no existen. Añadir un modo simulado:
`if platform.system() != "Linux" or os.getenv("AJUSTES_FAKE"): return <datos de ejemplo>`.
Así puedes maquetar la UI en el portátil.

---

## 6. Parte 4 — Permisos (lo más delicado)

El servicio corre como `kaito`, sin root. Hay que conceder **exactamente** lo necesario.

### 6.1 NetworkManager — regla polkit
`/etc/polkit-1/rules.d/50-kaito-nm.rules` (Bookworm, polkit con reglas JS):
```javascript
polkit.addRule(function(action, subject) {
  if (action.id.indexOf("org.freedesktop.NetworkManager.") === 0 &&
      subject.user === "kaito") {
    return polkit.Result.YES;
  }
});
```
(Bullseye/polkit 0.105: usar `.pkla` en `/etc/polkit-1/localauthority/50-local.d/`.)

### 6.2 Hora / zona horaria — regla polkit
`/etc/polkit-1/rules.d/51-kaito-timedate.rules`:
```javascript
polkit.addRule(function(action, subject) {
  if ((action.id === "org.freedesktop.timedate1.set-time" ||
       action.id === "org.freedesktop.timedate1.set-timezone" ||
       action.id === "org.freedesktop.timedate1.set-ntp") &&
      subject.user === "kaito") {
    return polkit.Result.YES;
  }
});
```

### 6.3 Reiniciar / apagar / hostname — regla polkit
`/etc/polkit-1/rules.d/52-kaito-power.rules`:
```javascript
polkit.addRule(function(action, subject) {
  if ((action.id === "org.freedesktop.login1.reboot" ||
       action.id === "org.freedesktop.login1.power-off" ||
       action.id === "org.freedesktop.hostname1.set-static-hostname" ||
       action.id === "org.freedesktop.hostname1.set-hostname") &&
      subject.user === "kaito") {
    return polkit.Result.YES;
  }
});
```

### 6.4 Brillo — regla udev + grupo
`/etc/udev/rules.d/90-kaito-backlight.rules`:
```
SUBSYSTEM=="backlight", ACTION=="add", \
  RUN+="/bin/chgrp video /sys%p/brightness", \
  RUN+="/bin/chmod g+w /sys%p/brightness"
```
Y `sudo usermod -aG video kaito`. Tras esto la app escribe el fichero directamente.

### 6.5 Sonido
`sudo usermod -aG audio kaito` y usar `amixer` (ALSA) contra la tarjeta hardware.
(Si acabas usando PipeWire de usuario, el servicio tendría que correr como servicio
*de usuario* con `linger` activado — más lío; ALSA es más simple para un servicio de sistema.)

### 6.6 Alternativa a polkit: sudoers acotado
Si polkit da guerra, `/etc/sudoers.d/kaito-ajustes` (con `visudo -f`):
```
kaito ALL=(root) NOPASSWD: /usr/bin/nmcli, /usr/bin/timedatectl, /usr/bin/tzupdate, /usr/bin/hostnamectl, /usr/sbin/reboot, /usr/sbin/poweroff
```
y en `system_settings.py` anteponer `sudo`. Más simple de entender, algo más de superficie.
Elige **una** de las dos vías (polkit recomendada) y sé consistente.

### 6.7 Bluetooth — grupo + regla polkit
`sudo usermod -aG bluetooth kaito`.
`/etc/polkit-1/rules.d/53-kaito-bluez.rules`:
```javascript
polkit.addRule(function(action, subject) {
  if (action.id.indexOf("org.bluez.") === 0 && subject.user === "kaito") {
    return polkit.Result.YES;
  }
});
```
Con el grupo `bluetooth` y la config por defecto de BlueZ suele bastar sin la regla; añádela
solo si `bluetoothctl` responde `Authentication required`.

### 6.8 Mantenimiento — `systemctl restart kaito` sin contraseña
Único privilegio que "Actualizar Kaito" y "Reiniciar servicio" necesitan de root.
`/etc/sudoers.d/kaito-mantenimiento` (con `visudo -f`):
```
kaito ALL=(root) NOPASSWD: /usr/bin/systemctl restart kaito, /usr/bin/systemctl restart kaito.service
```
`git pull`, `pip install`, `journalctl -u kaito` (el usuario ya puede leer su propio journal
si está en el grupo `systemd-journal`, o con `journalctl --user` según cómo esté la unidad),
la copia de la BD y el zip de diagnóstico corren como `kaito`, sin sudo.

Todos estos ficheros van versionados en `kaitosan/deploy/` y los copia el script de deploy.

---

## 7. Parte 5 — Rutas Flask y plantillas

### 7.1 Página
Nueva `templates/ajustes.html`, misma estructura que `admin.html`. El `_estilos.html` pasa a
la **paleta pastel de Kaito** (§13) — mismos tokens para el panel viejo, la página de Ajustes
y la UI de onboarding, así todo combina:
```html
<head> {% include 'partials/admin/_estilos.html' %} </head>
<body>
  <h1>⚙️ Kaito — Ajustes <a href="/admin">← Panel</a></h1>
  {% with messages = get_flashed_messages(with_categories=true) %} ... {% endwith %}
  <div class="grid">
    {% include 'partials/ajustes/_wifi.html' %}
    {% include 'partials/ajustes/_bluetooth.html' %}   {# v1 #}
    {% include 'partials/ajustes/_hora.html' %}
    {% include 'partials/ajustes/_sonido.html' %}      {# + selector de salida/entrada y ganancia de micro #}
    {% include 'partials/ajustes/_pantalla.html' %}
    {% include 'partials/ajustes/_modelos.html' %}     {# v1 — modelos de Groq #}
    {% include 'partials/ajustes/_sistema.html' %}
    {% include 'partials/ajustes/_mantenimiento.html' %} {# v1 — actualizar, logs, backup, reset #}
    {% include 'partials/ajustes/_cuenta.html' %}
  </div>
</body>
```
Añadir enlace a `/admin/ajustes` en la cabecera de `templates/admin.html`.

### 7.2 Reparto form-POST vs fetch/JSON
- **Estático** (hora, zona, volumen, brillo, cuenta, reiniciar): `<form method="POST">` +
  `flash()` + `redirect(url_for("ajustes"))`. Idéntico al patrón de `_perfil.html` / `_recordatorios.html`.
- **WiFi** (escaneo en vivo, feedback asíncrono): `fetch()` a una mini-API JSON, igual que
  hace `reloj.html`:
  ```
  GET  /admin/ajustes/wifi              -> {estado, guardadas}
  GET  /admin/ajustes/wifi/escanear     -> [redes...]
  POST /admin/ajustes/wifi/conectar     -> {ok, mensaje}
  POST /admin/ajustes/wifi/olvidar      -> {ok}
  POST /admin/ajustes/wifi/portal       -> {ok}   (recuperación: abre Kaitosan-Setup)
  ```
- **Bluetooth** (mismo patrón que WiFi — escaneo y emparejado asíncronos):
  ```
  GET  /admin/ajustes/bluetooth              -> {estado, emparejados}
  GET  /admin/ajustes/bluetooth/escanear     -> [dispositivos...]
  POST /admin/ajustes/bluetooth/conectar     -> {ok, mensaje}
  POST /admin/ajustes/bluetooth/desconectar  -> {ok}
  POST /admin/ajustes/bluetooth/olvidar      -> {ok}
  POST /admin/ajustes/bluetooth/radio        -> {ok}   (adaptador on/off)
  ```
- **Modelos de Groq** (lista en vivo desde la API):
  ```
  GET  /admin/ajustes/modelos           -> {disponibles:[...], seleccion:{...}}
  POST /admin/ajustes/modelos           -> {ok}   (principal, sensei, alternativos[], tools[])
  ```
- **Mantenimiento** (form-POST salvo `logs` y `actualizar`, que son fetch):
  ```
  POST /admin/ajustes/audio/salida          (form)  -> flash + redirect
  POST /admin/ajustes/audio/entrada         (form)
  POST /admin/ajustes/audio/micro-ganancia  (form)
  POST /admin/ajustes/audio/probar          -> {ok}         (fetch)
  GET  /admin/ajustes/sistema/logs          -> text/plain   (fetch)
  POST /admin/ajustes/sistema/actualizar    -> {ok, mensaje} (fetch + hilo; cae la sesión)
  POST /admin/ajustes/sistema/reiniciar-servicio
  GET  /admin/ajustes/sistema/backup        -> descarga kaito.db
  POST /admin/ajustes/sistema/restaurar     (multipart) -> flash + redirect
  GET  /admin/ajustes/sistema/diagnostico   -> descarga .zip
  POST /admin/ajustes/sistema/reset         -> {ok}   (requiere PIN en el body)
  ```

### 7.3 Rutas (todas con `@login_requerido`)
```python
@app.route("/admin/ajustes")
@login_requerido
def ajustes():
    return render_template("ajustes.html",
        wifi=system_settings.wifi_estado(),
        hora=system_settings.hora_estado(),
        zonas=system_settings.zona_listar(),
        volumen=system_settings.volumen_get(),
        brillo=system_settings.brillo_get(),
        sistema=system_settings.sistema_info(),
        admin_user=settings_get("admin_user"))

@app.route("/admin/ajustes/hora", methods=["POST"])
@login_requerido
def ajustes_hora():
    modo = request.form.get("modo")  # "ntp" | "manual"
    if modo == "ntp":
        system_settings.hora_set_ntp(True)
    else:
        system_settings.hora_set_ntp(False)
        system_settings.hora_set_manual(request.form["datetime"])
    flash("✅ Hora actualizada", "success")
    return redirect(url_for("ajustes"))

@app.route("/admin/ajustes/zona", methods=["POST"])
@login_requerido
def ajustes_zona():
    if request.form.get("auto"):
        system_settings.zona_auto(True)
        flash("✅ Zona horaria automática activada", "success")
    else:
        system_settings.zona_auto(False)
        system_settings.zona_set(request.form["tz"])
        flash("✅ Zona horaria fijada", "success")
    return redirect(url_for("ajustes"))

# ... /volumen, /brillo, /hostname, /reiniciar, /apagar, /cuenta análogos
# ... el bloque WiFi como API JSON (fetch), no form-POST
```

### 7.4 UX crítica del cambio de WiFi
Al conectar a otra red, **se cae la conexión con la que Laura está viendo la página**.
Mitigaciones (implementar las tres):
1. Responder al `fetch` **antes** de ejecutar el cambio; lanzar el `nmcli connect` en un
   hilo con `threading.Thread(daemon=True)`.
2. Mensaje en la UI: *"Kaito se está conectando a **&lt;SSID&gt;**. Si pierdes esta página,
   conéctate a esa misma red y vuelve a entrar en `http://kaitosan.local:5000`."*
3. **Watchdog de reversión**: guardar el SSID anterior; si a los 60 s no hay conectividad
   (`nmcli -t -f CONNECTIVITY g` ≠ `full`), `nmcli con up <anterior>`. Y si aun así se queda
   sin nada, el servicio `kaitosan-wifi-connect` levanta el portal solo (red de seguridad).

---

## 8. Parte 6 — Servicio systemd de la app y acceso sin IP

### 8.1 Unidad `/etc/systemd/system/kaito.service`
```ini
[Unit]
Description=Kaitosan
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=kaito
SupplementaryGroups=audio video
WorkingDirectory=/home/kaito/kaitosan
ExecStart=/home/kaito/kaitosan/venv/bin/python app.py
Restart=on-failure
KillSignal=SIGTERM
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
```
(El manejador de `SIGTERM` de `app.py:749` ya hace el cierre ordenado.)

### 8.2 Acceso por nombre (nada de IPs)
```bash
sudo hostnamectl set-hostname kaitosan      # -> http://kaitosan.local:5000
```
Avahi ya viene en Raspberry Pi OS. Funciona en iPhone/Mac/Windows; Android moderno casi siempre.

### 8.3 Kiosco (si la Pi tiene su propia pantalla)
Autostart de Chromium en modo kiosco a `http://localhost:5000` → Laura nunca necesita IP
ni nombre para el uso normal; el panel de Ajustes se abre desde otro dispositivo por
`kaitosan.local`.

---

## 9. Plan de trabajo por fases pequeñas

**Cómo se trabaja.** Cada fase se hace en una **conversación nueva de Claude Code, con el
contexto vacío**. La sesión empieza leyendo este fichero (`PLAN_AJUSTES.md`), hace **solo esa
fase**, la prueba contra su hito, y **cierra con un commit**. La siguiente fase arranca limpia.
No encadenar fases en la misma conversación.

Cada fase indica: **qué se hace** (una frase), **ficheros**, **hito** (cómo saber que está
lista) y **secciones del plan** que hay que leer. Las "**Partes**" (§3–§8) no son tareas: son
la documentación de cada subsistema a la que apuntan las fases con su "Leer:".

**Arranque de cada sesión** (conversación nueva, contexto vacío). Copia y pega, cambiando el
número:

> Lee `PLAN_AJUSTES.md`. Haz **solo la Fase N** de la §9, y lo que diga su "Leer:".
> Al terminar: comprueba el hito y haz un commit. No sigas con la Fase N+1.

Las fases 1–11 y 5b se hacen en el portátil; las 12–16 requieren la Raspberry Pi.

### Bloque A — Cimientos (en el portátil, sin Raspberry)

**Fase 1 — Almacén de ajustes.**
Crear `core/settings_store.py` con la tabla `app_settings` (`key`/`value`) y siembra desde `.env`.
- Ficheros: `core/settings_store.py`, tocar el `_conectar()` de la BD si hace falta.
- Hito: en un `python -c`, `settings_get("admin_user")` devuelve `"laura"`; `settings_set` + `settings_get` de ida y vuelta funciona.
- Leer: §4.1.

**Fase 2 — Login con usuario + contraseña.**
Cambiar el login de solo-password a usuario + contraseña con hash werkzeug.
- Ficheros: `core/config.py` (`ADMIN_USER`), `app.py` (`admin_login`), `templates/admin_login.html` (campo usuario), `.env.example`.
- Hito: entra `laura` + contraseña; la contraseña sola ya no entra; la siembra desde `.env` solo ocurre la primera vez.
- Leer: §4.1, §4.2, §4.3, §4.4.

**Fase 3 — `core/system_settings.py` (solo lecturas) + modo simulado.**
Crear el módulo con las funciones de **lectura** (`wifi_estado`, `hora_estado`, `volumen_get`, `brillo_get`, `sistema_info`) devolviendo datos de ejemplo cuando no es Linux o `AJUSTES_FAKE=1`.
- Ficheros: `core/system_settings.py`, `.env.example` (`AJUSTES_FAKE`).
- Hito: en el portátil, cada función devuelve un `dict` de ejemplo sin lanzar excepción.
- Leer: §5 (reglas y "Pruebas fuera de la Pi").

**Fase 4 — Paleta pastel + base responsive.**
Reescribir `templates/partials/admin/_estilos.html` con los tokens CSS de §13 (tema claro
rosa pastel, fuente redondeada) **y las reglas de dispositivo de §13.3**: móvil primero,
táctil (sin depender de `:hover`), controles nativos, una columna por debajo de 640px.
Comprobar que el panel viejo (`admin.html`, `japones.html`, `reloj.html`, `face.html`) sigue
legible.
- Ficheros: `templates/partials/admin/_estilos.html`, `<meta viewport>` + `<link>` a Google Fonts en las plantillas.
- Hito: el panel se ve en rosas pastel y **usable con el pulgar a 390px de ancho**; contraste AA; nada roto.
- Leer: §13 (entero, sobre todo §13.3).

**Fase 5 — Página de Ajustes + ruta GET + enlace.**
`templates/ajustes.html` en **una columna de "filas de ajuste"** (no tablas) con los parciales `_hora`, `_sonido`, `_pantalla`, `_sistema`, `_cuenta`; ruta `/admin/ajustes` con `@login_requerido`; enlace desde `admin.html`.
- Ficheros: `templates/ajustes.html`, `templates/partials/ajustes/_hora.html` `_sonido.html` `_pantalla.html` `_sistema.html` `_cuenta.html`, `app.py`, `templates/admin.html`.
- Hito: la página se ve bien y se opera con el dedo a **390×844** (móvil) y a **480×480** (robot, contenido dentro del círculo seguro, ver §13.3.B); muestra los datos simulados de la Fase 3.
- Leer: §7.1, §7.3, §13.3.

**Fase 5b — Vista "modo robot" reducida.**
Servir en la pantalla del robot (por `@media (max-width:520px)` + host `localhost`/`?kiosk=1`) solo lo esencial en filas gigantes: volumen, brillo, estado WiFi/BT, reiniciar.
- Ficheros: `templates/ajustes.html` (o un parcial `_robot.html`), `templates/partials/admin/_estilos.html`.
- Hito: abrir `http://localhost:5000/admin/ajustes` a 480×480 muestra la vista reducida, todo dentro del círculo, botones de 56–64px.
- Leer: §13.3.B.

**Fase 6 — Escrituras estáticas (hora, zona, volumen, brillo).**
Añadir a `system_settings.py` las funciones de escritura (con simulado) y las rutas `POST` form + `flash` + redirect.
- Ficheros: `core/system_settings.py`, `app.py`, parciales de la Fase 5.
- Hito: cada formulario hace `flash` "✅ actualizado" en el portátil (sin tocar el sistema real).
- Leer: §5, §7.2 (bloque "estático"), §7.3.

**Fase 7 — Cambiar credenciales del panel.**
`POST /admin/ajustes/cuenta` (usuario, contraseña actual, contraseña nueva) + parcial `_cuenta.html`.
- Ficheros: `app.py`, `templates/partials/ajustes/_cuenta.html`.
- Hito: cambias la contraseña, cierras sesión y entras con la nueva; con la contraseña actual mal, no deja.
- Leer: §4.5.

### Bloque B — Audio y modelos (en el portátil)

**Fase 8 — Selector de dispositivo de audio.**
Funciones `audio_salidas/entradas/*_set`, `micro_ganancia_*`, `audio_probar_*` (con simulado); parcial `_sonido.html` ampliado; el arranque de audio lee `app_settings` antes que los `*_HINT` del `.env`.
- Ficheros: `core/system_settings.py`, `templates/partials/ajustes/_sonido.html`, `app.py`, arranque de audio (`audio/recorder.py` y donde se resuelva el device).
- Hito: los desplegables se rellenan con tarjetas de ejemplo; la selección se guarda en `app_settings` y se relee al arrancar.
- Leer: §2.1, §5 (nota "Selección de audio").

**Fase 9 — Selección de modelos de Groq.**
`groq_modelos()` (GET real a `api.groq.com/openai/v1/models`, funciona en el portátil), `groq_seleccion_get/set`; parcial `_modelos.html`; `groq_provider.py` y `config.py` leen la selección de `app_settings`.
- Ficheros: `core/system_settings.py`, `ai/groq_provider.py`, `core/config.py`, `templates/partials/ajustes/_modelos.html`, `app.py`.
- Hito: el desplegable muestra la lista real de tu API key; guardas principal/sensei/alternativos/tools y `GroqProvider` los usa; un modelo retirado cae al default.
- Leer: §2.1, §5 (nota "Modelos de Groq"), §11.

### Bloque C — Mantenimiento (en el portátil, salvo el restart real)

**Fase 10 — Salud, logs y copia de seguridad.**
`salud()`, `logs()`, `backup_bd()`, `restaurar_bd()`, `diagnostico_zip()` (simulado donde haga falta); parcial `_mantenimiento.html`; rutas.
- Ficheros: `core/system_settings.py`, `templates/partials/ajustes/_mantenimiento.html`, `app.py`.
- Hito: descargas `kaito.db`, la restauras y arranca; los logs se ven en la web; el zip de diagnóstico no lleva secretos en claro.
- Leer: §2.1, §5, §11 (nota "Diagnóstico").

**Fase 11 — Actualizar / reiniciar servicio / reset de fábrica.**
`actualizar()` (git pull + pip + restart en hilo, guarda el commit anterior), `reiniciar_servicio()`, `reset_fabrica(pin)`; rutas `fetch` con aviso de caída de sesión.
- Ficheros: `core/system_settings.py`, `templates/partials/ajustes/_mantenimiento.html`, `app.py`.
- Hito (portátil): `actualizar()` hace el `git pull`, responde **antes** de reiniciar y guarda el commit anterior; `reset_fabrica` exige PIN.
- Leer: §5 (notas "actualizar()" y "reset_fabrica()"), §11.

### Bloque D — En la Raspberry Pi

**Fase 12 — Servicio y permisos base en la Pi.**
`deploy/kaito.service`, instalar `tzupdate`, reglas polkit `50/51/52`, regla udev `90`, grupos `audio`/`video`, sudoers `kaito-mantenimiento`.
- Ficheros: `deploy/kaito.service`, `deploy/50-kaito-nm.rules`, `deploy/51-kaito-timedate.rules`, `deploy/52-kaito-power.rules`, `deploy/90-kaito-backlight.rules`, `deploy/kaito-mantenimiento.sudoers`.
- Hito: en la Pi, hora, zona, volumen y brillo cambian de verdad; "reiniciar servicio" funciona sin pedir contraseña.
- Leer: §6, §8.1.

**Fase 13 — WiFi real en la Pi.**
Bloque WiFi como API JSON + UI `fetch`, parcial `_wifi.html`, watchdog de reversión.
- Ficheros: `core/system_settings.py` (`wifi_*`), `templates/partials/ajustes/_wifi.html`, `app.py`.
- Hito: cambias de red desde el móvil y reconecta; con contraseña mal, revierte sola a los 60 s.
- Leer: §5 (notas WiFi), §7.2 (bloque WiFi), §7.4.

**Fase 14 — Bluetooth real en la Pi.**
`bt_*` en `system_settings.py`, parcial `_bluetooth.html`, rutas JSON, grupo `bluetooth`, regla polkit `53`.
- Ficheros: `core/system_settings.py` (`bt_*`), `templates/partials/ajustes/_bluetooth.html`, `app.py`, `deploy/53-kaito-bluez.rules`.
- Hito: emparejas un altavoz BT, lo eliges como salida y Kaito suena por él; al apagarlo, vuelve a la tarjeta local.
- Leer: §2.1, §5 (nota Bluetooth), §6.7, §7.2 (bloque Bluetooth).

**Fase 15 — Onboarding WiFi (`balena-wifi-connect`).**
Binario, `onboarding/ui/index.html` con estética Kaito, `deploy/kaitosan-wifi-connect.service` con el disparador "solo si no hay conexión".
- Ficheros: `onboarding/ui/index.html`, `deploy/kaitosan-wifi-connect.service`.
- Hito: `nmcli radio wifi off` → aparece `Kaitosan-Setup` con la UI de Kaito → conecta y el AP se apaga.
- Leer: §3.

**Fase 16 — Nombre de equipo, kiosco y script de deploy.**
`hostnamectl set-hostname kaitosan`, (opcional) autostart de Chromium en kiosco, `deploy/install.sh` que copia todo a sus rutas y hace `daemon-reload` + `restart`.
- Ficheros: `deploy/install.sh`, autostart del kiosco.
- Hito: entras por `http://kaitosan.local:5000`; `install.sh` deja una Pi virgen lista de una pasada.
- Leer: §8.2, §8.3.

---

## 10. Ficheros nuevos / tocados

**Nuevos**
```
core/settings_store.py
core/system_settings.py
templates/ajustes.html
templates/partials/ajustes/_wifi.html
templates/partials/ajustes/_bluetooth.html      (v1)
templates/partials/ajustes/_hora.html
templates/partials/ajustes/_sonido.html         (+ selector salida/entrada + ganancia micro)
templates/partials/ajustes/_pantalla.html
templates/partials/ajustes/_modelos.html        (v1 — modelos de Groq)
templates/partials/ajustes/_sistema.html
templates/partials/ajustes/_mantenimiento.html  (v1 — actualizar, logs, backup, reset)
templates/partials/ajustes/_cuenta.html
onboarding/ui/index.html            (UI del portal, estética Kaito)
deploy/kaito.service
deploy/kaitosan-wifi-connect.service
deploy/50-kaito-nm.rules
deploy/51-kaito-timedate.rules
deploy/52-kaito-power.rules
deploy/53-kaito-bluez.rules                      (v1)
deploy/90-kaito-backlight.rules
deploy/kaito-mantenimiento.sudoers              (v1 — systemctl restart kaito sin contraseña)
deploy/install.sh                   (copia todo lo anterior a sus rutas)
```

**Tocados**
```
app.py                 (login user+pass, rutas /admin/ajustes/*)
core/config.py         (ADMIN_USER; leer groq_models de app_settings antes que los valores fijos)
ai/groq_provider.py    (modelo principal / alternativos / tools desde app_settings si hay selección)
audio/recorder.py + arranque de audio  (leer audio_output/audio_input de app_settings antes que los *_HINT del .env)
templates/partials/admin/_estilos.html  (paleta pastel de Kaito — tokens CSS de §13)
templates/partials/face/_estilos.html   (misma paleta, si se quiere la cara a juego)
templates/*.html       (enlace a Google Fonts: M PLUS Rounded 1c)
templates/admin.html   (enlace a Ajustes)
templates/admin_login.html (campo usuario)
.env.example           (ADMIN_USER, AJUSTES_MIXER_CONTROL, AJUSTES_FAKE)
requirements.txt        (nada nuevo salvo que uses la lib tzupdate por pip)
README.md              (sección "Ajustes de la Pi" + "Regalar la Pi")
```

---

## 11. Riesgos y notas

- **Quedarte fuera por WiFi**: mitigado por el watchdog de reversión (§7.4) + el portal de
  onboarding como último recurso. Aun así, ten a mano SSH por cable/USB-gadget mientras desarrollas.
- **Superficie de privilegios**: cada regla polkit/sudoers amplía lo que la web puede hacer si
  alguien roba la sesión. Contraseña fuerte, `permanent_session_lifetime` ya está en 30 min, y
  considera servir solo en la LAN (no exponer el puerto 5000 a Internet).
- **Brillo HDMI**: un monitor por HDMI normalmente no se controla desde la Pi. La tarjeta de
  brillo debe ocultarse si `glob('/sys/class/backlight/*')` está vacío.
- **PipeWire vs ALSA**: en Bookworm el audio de escritorio es PipeWire de usuario; un servicio
  de sistema no lo ve. Usa `amixer` sobre la tarjeta hardware, o monta el servicio como
  servicio de usuario con `loginctl enable-linger kaito` (más complejo).
- **`tzupdate`** manda tu IP a un servicio de geolocalización. Es 1 petición y solo cuando
  Laura pulsa "automática", pero conviene decirlo en la UI.
- **Bullseye**: sin NetworkManager nada de esto aplica. Migrar primero.
- **nmcli parsing**: usa `-t` (terse) y ten en cuenta que los `:` dentro de un SSID vienen
  escapados como `\:`.
- **Actualizar Kaito desde la web**: un `git pull` puede dejar el arranque roto. Guardar el
  commit anterior y ofrecer "volver a la versión anterior"; no auto-actualizar nunca; mostrar
  el `git log` de lo que va a entrar antes de confirmar.
- **Reset de fábrica**: irreversible. Doble confirmación + PIN; hacer un `backup_bd()`
  automático justo antes, por si acaso.
- **Bluetooth + audio**: si Kaito está sonando por un altavoz BT y se sale de rango, el audio
  se pierde. `audio_salidas()` debe detectar la desaparición del sink y reasignar a la tarjeta
  local; avisar en la UI.
- **Lista de modelos de Groq**: la API cambia nombres y retira modelos (`decommissioned`).
  Validar la selección guardada en cada arranque contra `groq_modelos()` y caer al default si
  un modelo ya no existe. No dejar que la UI guarde un `id` que no esté en la lista activa.
- **Diagnóstico**: el zip puede filtrar secretos (`.env`, tokens en logs). Ofuscar claves y
  revisar el contenido antes de exponer el enlace de descarga.

---

## 12. Backlog de ajustes (mecanismo por item)

Se aborda cuando la v1 esté estable en la Pi. Cada item se convertirá en su propia fase
pequeña (como las de §9) cuando llegue su turno. Todo sigue el mismo patrón: función en
`core/system_settings.py` (o clave en `app_settings`), parcial en `templates/partials/ajustes/`,
ruta `@login_requerido`, modo simulado fuera de la Pi.

> **Fuera de alcance a propósito:** voz / TTS de Kaito (velocidad, pausas ES/JP, silencio
> inicial, volumen relativo) y wakeword (on/off, sensibilidad). Se siguen tocando solo por
> `.env` / código, nunca desde Ajustes.

| Ajuste | Mecanismo | Notas |
|---|---|---|
| **Horario "no molestar"** | franja horaria; el listener ignora audio fuera de ella | encaja con el blanking de pantalla |
| **Apagar pantalla por inactividad / horario nocturno** | `xset dpms` / escribir en `bl_power` del backlight; o cron | pantalla oficial: `bl_power` 0/1 |
| **Rotación de pantalla** | `display_rotate` en `/boot/firmware/config.txt` (requiere reinicio) o `wlr-randr` | avisar del reinicio |
| **Tema / color de acento de la cara** | variable CSS servida a `face.html` desde `app_settings` | |
| **Cámara on/off** | flag que corta `core/camera.py` | privacidad + ahorro de CPU |
| **Detección de rostro on/off** | flag en `core/detection.py` | |
| **Modo al arrancar** (charla / sensei) | `app_settings["modo_inicial"]` leído por `core/brain.py` | |
| **Evaluación de pronunciación en charla** | `AZURE_PRON_EN_CHARLA` → `app_settings` | ya existe en `.env` |
| **Barra de cuota de Azure** | segundos usados vs `AZURE_STT_LIMITE_SEG_MES` | el contador ya se lleva; falta pintarlo |
| **Uso de tokens / coste** | `core/token_tracker.py` | ya hay `_tokens.html`, reaprovechar en Ajustes |
| **QR con la URL del panel** | generar QR de `http://kaitosan.local:5000` en `_sistema.html` | qrcode por JS, sin dependencia server |
| **Probar Internet** | `nmcli -t -f CONNECTIVITY g` + un `curl -sI` a un host conocido | |
| **SSID oculto** | `nmcli dev wifi connect <ssid> password <psk> hidden yes` | campo manual en `_wifi.html` |
| **Modo avión** | `nmcli radio all off` (apaga WiFi + BT) | botón único; con confirmación (te deja sin panel) |
| **Reinicio diario programado** | unidad `systemd` timer o cron; hora en `app_settings` | estabilidad a largo plazo |
| **Formato de hora 12/24 / primer día de semana** | `app_settings`; lo consumen las plantillas | |
| **Ciudad por defecto del tiempo** | `app_settings["weather_ciudad"]` → `ai/skills/weather.py` | |
| **Tono y volumen de alarma / snooze por defecto** | `app_settings` → `ai/skills/alarm.py` / `reminder.py` | |
| **Cerrar todas las sesiones** | rotar `FLASK_SECRET_KEY` o invalidar en `app_settings` | |
| **Restringir el panel a la LAN** | bind a `0.0.0.0` vs comprobación de red de origen; o firewall | evita exponer el 5000 |
| **PIN para acciones peligrosas** | `app_settings["pin_hash"]`; exigido en reiniciar/apagar/reset/actualizar | 4–6 dígitos |

---

## 13. Estética — paleta pastel de Kaito

Sustituye el tema oscuro azul (`#0a0a0a` / `#0096ff`) por un tema **claro en rosas pastel**.
Los tokens viven en `templates/partials/admin/_estilos.html` como variables CSS en `:root` y
los usan **panel viejo, página de Ajustes y UI de onboarding** — así todo combina.

### 13.1 Tokens

```css
:root {
  /* superficies */
  --bg:            #fff5f8;   /* blush casi blanco, fondo de página */
  --bg-alt:        #ffeaf2;   /* zonas alternas, cabeceras de tabla, chips */
  --surface:       #ffffff;   /* tarjetas */
  --surface-2:     #fff0f5;   /* inputs, filas hover */
  --border:        #f6d4e2;   /* bordes suaves */
  --border-fuerte: #efb9d0;

  /* texto (nada de negro puro) */
  --text:          #5b3a4a;   /* ciruela grisáceo — cuerpo */
  --text-soft:     #9a7f8c;   /* secundario */
  --text-faint:    #c8aeba;   /* placeholders, estado vacío */

  /* rosas */
  --rosa:          #f7b8d2;   /* acento suave: chips, hover, bordes activos */
  --rosa-medio:    #f090b6;   /* iconos, detalles */
  --rosa-accion:   #d9568c;   /* botón primario y anillo de foco (blanco encima) */
  --rosa-tinta:    #9d3564;   /* títulos y texto sobre rosa claro */

  /* acentos que combinan */
  --lavanda:       #cdbdec;
  --melocoton:     #ffd6be;
  --menta:         #b7e6d1;

  /* estados */
  --ok:            #3fae86;   --ok-bg:      #e7f7f0;
  --aviso:         #d98a2b;   --aviso-bg:   #fff4e2;
  --peligro:       #c85a5a;   --peligro-bg: #fdecec;

  /* forma */
  --radio:         18px;      /* tarjetas */
  --radio-sm:      12px;      /* inputs */
  --radio-pill:    999px;     /* botones */
  --sombra:        0 8px 24px rgba(217, 86, 140, 0.15);
  --sombra-sm:     0 2px 8px  rgba(217, 86, 140, 0.12);
}
```

### 13.2 Tipografía
`font-family: 'M PLUS Rounded 1c', 'Nunito', 'Segoe UI', sans-serif;` — **M PLUS Rounded 1c**
(Google Fonts) es redondeada y trae glifos japoneses completos, muy a tono con un robot que
enseña japonés. Pesos 400 / 500 / 700. Cargar con `<link>` a `fonts.googleapis.com`.

### 13.3 Dispositivos objetivo (manda esto sobre todo lo demás)

**El 95% de los accesos son desde un móvil.** El 5% restante es la **pantalla del propio
robot**. No hay caso "escritorio con ratón" que optimizar: el escritorio solo tiene que
funcionar, no lucir.

**A. Móvil primero (diseñar a ~390px de ancho y luego ampliar):**
- Una sola columna. La rejilla `.grid` de 2 columnas es solo para pantallas anchas; por
  debajo de 640px, todo apilado.
- **Táctil, no ratón**: nada depende de `:hover` ni de `title=` para funcionar — el hover es
  un extra que en móvil no existe. Sin menús contextuales, sin doble toque, sin arrastrar
  fino, sin tooltips como única fuente de información.
- **Áreas de toque ≥ 48×48px** con ≥ 8px de separación entre ellas. Botones pill grandes.
- **Usar controles nativos**: `<input type="time">`, `type="number">`, `type="range">`,
  `<select>`, `<input type="color">`… así sale el selector del sistema operativo del móvil y
  no hay que construir date-pickers ni sliders a mano.
- Formularios largos: botón **Guardar fijo abajo** (`position: sticky; bottom`).
- Tipografía fluida con `clamp()`; base ≥ 16px para que iOS no haga zoom al enfocar un input.
- Feedback inmediato al tocar (`:active` con un leve `scale(.98)`), porque no hay hover que
  anticipe.

**B. Pantalla del robot — táctil redonda de ~2.8" (≈ 480×480 px, circular):**
- **Es un círculo: las 4 esquinas no se ven.** Nada útil fuera de un **círculo central
  seguro**. Regla práctica: zona de contenido = cuadrado centrado de ~70% del ancho
  (≈ 330–340px); el resto, solo fondo. El enlace "← Panel", el reloj, los badges… al centro,
  nunca pegados a un borde.
- Una columna, scroll vertical con inercia, sin barra de scroll visible.
- `<meta name="viewport">` + `touch-action: manipulation` (mata el zoom por doble toque).
- **Se mira de cerca pero se toca con el dedo**: fuente base 18–20px, botones de fila enormes
  (56–64px de alto), muchísimo aire.
- A este tamaño y con brillo bajo, las **sombras rosa claras casi no se ven** → reforzar cada
  tarjeta/fila con un `border` visible, no fiarlo todo a la sombra.
- **Vista "modo robot" reducida**: detectar por `@media (max-width: 520px)` **y** por que el
  host sea `localhost`/kiosco (o `?kiosk=1`), y servir solo lo esencial en filas gigantes:
  volumen, brillo, estado de WiFi/BT, "reiniciar". El resto de ajustes (modelos, cuenta,
  mantenimiento…) se hacen desde el móvil; en el robot pueden ni aparecer.

**C. Escritorio (raro):** la misma página en una sola columna centrada con `max-width: 640px`
basta. No hace falta layout de 2–3 columnas ni interacciones de ratón.

### 13.4 Componentes (reglas, no CSS literal)
- **Tarjeta**: `--surface`, borde `1px --border` (**visible**, no solo sombra),
  `border-radius: --radio`, `box-shadow: --sombra`, padding 20–24px (16px en la vista robot).
- **Fila de ajuste** (patrón principal en móvil y robot, en vez de tablas): bloque a lo ancho,
  etiqueta arriba + control debajo o a la derecha, alto mínimo 56px, todo el bloque es zona
  táctil cuando lleva un único control.
- **Botón primario**: fondo `linear-gradient(135deg, #f5a0c4, var(--rosa-accion))`, texto
  blanco, `border-radius: --radio-pill`, sin borde, `--sombra-sm`; `:active` → `scale(.98)`.
  El `:hover` (`translateY(-1px)`) es solo un extra de escritorio.
- **Botón peligro** (reiniciar, reset, olvidar): fondo `--peligro-bg`, texto `--peligro`,
  borde `1px --peligro`. Nunca rojo saturado. Confirmación explícita antes de actuar.
- **Botón secundario**: fondo `--surface-2`, texto `--rosa-tinta`, borde `1px --border`.
- **Input / select / range**: nativos; fondo `--surface-2`, borde `1px --border`,
  `border-radius: --radio-sm`, alto ≥ 48px; foco: borde `--rosa-accion` +
  `box-shadow: 0 0 0 3px rgba(217,86,140,.25)`.
- **Toggle** (on/off de WiFi, BT, cámara…): switch grande tipo iOS, pista `--rosa` cuando ON,
  ≥ 52×32px, toda la fila lo activa.
- **h1 / h2**: color `--rosa-tinta`; `h2` con línea inferior `1px --border`. `h1` lleva 🤖🌸.
- **Badge / chip**: fondo `--bg-alt`, texto `--rosa-tinta`, `border-radius: --radio-pill`.
- **Nada de tablas en la página de Ajustes**: usar listas de "filas de ajuste". (La `<table>`
  del panel viejo puede quedarse, pero debe colapsar a tarjetas por debajo de 640px.)
- **Alertas**: éxito `--ok-bg` / `--ok`; error `--peligro-bg` / `--peligro`. Que quepan en una
  línea o dos; en el robot, a pantalla completa unos segundos.
- **Medidores** (señal WiFi/BT, cuota Azure, tokens): barra sobre `--bg-alt`, relleno en
  `--rosa` → `--rosa-medio`; usa el skill `dataviz` y su validador de contraste.

### 13.5 Contraste (AA ≥ 4.5 para texto normal)
Los rosas *pastel puros* no llegan para texto pequeño: por eso `--rosa-accion` (#d9568c) es un
rosa más profundo para botones/foco y `--rosa-tinta` (#9d3564) para texto sobre fondo claro.
Verifica cada par texto/fondo antes de dar por bueno el tema. En la pantalla del robot, subir
un punto más el contraste (brillo bajo + tamaño pequeño perdonan poco).

### 13.6 Qué lo saca de lo genérico
1. Un solo sistema de tokens aplicado con disciplina (esto, no los efectos sueltos).
2. Bucle visual: renderizar → captura → ajustar (ver §13.7), a **dos viewports fijos**:
   móvil (390×844) y robot (480×480 con una máscara circular encima para ver qué se recorta).
3. Dos o tres decisiones con carácter: fuente redondeada, esquinas muy marcadas, sombras
   **rosadas** en vez de grises, un motivo 🌸, cero negro puro.
4. Referencias concretas: guarda 2–3 capturas de webs cuyo estilo te guste y pásalas como
   ejemplo; eso guía mejor que cualquier descripción abstracta.

### 13.7 Herramientas para diseñar (skills y MCPs)

**Skills que ya tienes en Claude Code:**
- **`design`** — lienzo de diseño; boceta el aspecto de las pantallas de Ajustes antes de
  tocar Jinja.
- **`artifact-design`** — fundamentos de diseño; cárgalo antes de construir cualquier página.
- **`dataviz`** — para las barras/medidores (cuota Azure, tokens, señal); trae validador de
  contraste de color.
- **`run`** — levanta la app de Kaito y saca captura para confirmar que se ve bien de verdad.

**MCPs instalados (scope user, en `~/.claude.json`):**
- **`playwright`** — el más importante: renderiza la página, saca capturas y mide estilos
  computados → bucle render→captura→ajuste. Probar siempre a **390×844** (móvil) y
  **480×480** (robot, con máscara circular). Sin este bucle, el diseño tiende a genérico.
- **`context7`** — documentación al día de Tailwind/CSS/librerías; evita patrones viejos.
- **`shadcn`** — componentes accesibles bien hechos; con los tokens de §13 como theme dejan
  de parecer plantilla. Gratis e ilimitado (es local).
- **`magic`** (21st.dev) — genera componentes de UI a partir de una descripción. **Cuota
  gratuita muy corta**: úsalo solo para piezas puntuales raras (un toggle animado, un
  selector especial) y con la descripción + tokens pastel bien concretos; no para páginas
  enteras. Para lo normal, shadcn + tokens a mano.

Figma descartado (no se va a usar).

**Recursos (no MCP):** Google Fonts (M PLUS Rounded 1c), iconos Lucide/Phosphor inline,
paletas en Coolors / Huemint / Realtime Colors, inspiración en Mobbin / Godly / Land-book.
