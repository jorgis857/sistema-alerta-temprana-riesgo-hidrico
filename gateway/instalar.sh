#!/usr/bin/env bash
# Instala el gateway WREWS en una Raspberry Pi (Raspberry Pi OS / Debian).
# Uso, desde la carpeta gateway/ del repo:   sudo ./instalar.sh
# (o, sin preguntas:  sudo CLAVE_ESP32=... CLAVE_GATEWAY=... CLAVE_MONITOR=... ./instalar.sh)
# Se puede correr de nuevo sin problema: no borra datos ni claves existentes.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then echo "Correr con sudo: sudo ./instalar.sh"; exit 1; fi
AQUI="$(cd "$(dirname "$0")" && pwd)"

echo "== 1/6 Paquetes (Mosquitto, Python, SQLite)"
apt-get update -q
apt-get install -y -q mosquitto mosquitto-clients python3-venv python3-pip sqlite3 ca-certificates

echo "== 2/6 Usuario de servicio y carpetas"
id wrews &>/dev/null || useradd --system --home /var/lib/wrews --shell /usr/sbin/nologin wrews
mkdir -p /opt/wrews /var/lib/wrews /etc/wrews
chown wrews:wrews /var/lib/wrews
rm -rf /opt/wrews/gateway
mkdir -p /opt/wrews/gateway
cp -r "$AQUI/wrews_gw" "$AQUI/requirements.txt" "$AQUI/simulador_esp32.py" /opt/wrews/gateway/
find /opt/wrews/gateway -name __pycache__ -prune -exec rm -rf {} +
chown -R root:root /opt/wrews/gateway

echo "== 3/6 Entorno de Python (paho-mqtt, requests, anthropic)"
[[ -d /opt/wrews/venv ]] || python3 -m venv /opt/wrews/venv
/opt/wrews/venv/bin/pip install -q --upgrade pip
/opt/wrews/venv/bin/pip install -q -r /opt/wrews/gateway/requirements.txt

echo "== 4/6 Mosquitto con usuario y clave"
cp "$AQUI/mosquitto/wrews.conf" /etc/mosquitto/conf.d/wrews.conf
cp "$AQUI/mosquitto/wrews.acl"  /etc/mosquitto/wrews.acl
PW=/etc/mosquitto/wrews.passwd
# Las claves se pueden pasar en el comando para no escribirlas a mano:
#   sudo CLAVE_ESP32=... CLAVE_GATEWAY=... CLAVE_MONITOR=... ./instalar.sh
nueva_clave() {   # usuario
  local var="CLAVE_$(echo "$1" | tr '[:lower:]' '[:upper:]')"
  local clave="${!var:-}"
  local crear=""
  [[ -f $PW ]] || crear="-c"
  if [[ -f $PW ]] && grep -q "^$1:" "$PW"; then
    if [[ -n $clave ]]; then
      mosquitto_passwd -b "$PW" "$1" "$clave"
      echo "   usuario '$1': clave actualizada"
    else
      echo "   usuario '$1' ya existe (no se cambia; para cambiarlo: sudo mosquitto_passwd $PW $1)"
    fi
  elif [[ -n $clave ]]; then
    mosquitto_passwd $crear -b "$PW" "$1" "$clave"
    echo "   usuario '$1' creado"
  else
    echo "   Clave para el usuario MQTT '$1' (se pide dos veces, no se ve al escribir):"
    mosquitto_passwd $crear "$PW" "$1"
  fi
}
nueva_clave esp32
nueva_clave gateway
nueva_clave monitor
chown root:mosquitto "$PW" /etc/mosquitto/wrews.acl
chmod 640 "$PW" /etc/mosquitto/wrews.acl
systemctl enable mosquitto
systemctl restart mosquitto
sleep 1
if ! systemctl is-active --quiet mosquitto; then
  echo "ERROR: Mosquitto no arranco. Ver: sudo tail -n 30 /var/log/mosquitto/mosquitto.log"
  exit 1
fi

echo "== 5/6 Configuracion del gateway"
if [[ ! -f /etc/wrews/gateway.env ]]; then
  cp "$AQUI/gateway.env.example" /etc/wrews/gateway.env
  echo "   Creado /etc/wrews/gateway.env: EDITELO antes de seguir (claves y token)"
fi
chown root:wrews /etc/wrews/gateway.env
chmod 640 /etc/wrews/gateway.env

echo "== 6/6 Servicio systemd"
cp "$AQUI/systemd/wrews-gateway.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable wrews-gateway

echo
echo "Listo. Siguiente:"
echo "  1. sudo nano /etc/wrews/gateway.env      (MQTT_PASS, UBIDOTS_TOKEN, ANTHROPIC_API_KEY)"
echo "  2. sudo systemctl restart wrews-gateway"
echo "  3. journalctl -u wrews-gateway -f        (ver que conecte)"
echo "IP de esta Pi para el secrets.h del ESP32 (MQTT_HOST): $(hostname -I | awk '{print $1}')"
