#!/usr/bin/env bash
# ============================================================================
# fix_telemetria_comma.sh
#   Arregla EN EL COMMA (por SSH) el problema de "llegan eventos pero no
#   telemetria ni comandos a la app AdriPilot".
#
#   Lo que hace, en orden:
#     1) Muestra el GitCommit del comma y lo compara con este repo local.
#     2) FUERZA telemetria_uem=1 (los builds antiguos tenian la telemetria
#        y los comandos gated por ese param; si el comma corre uno viejo y
#        el toggle esta OFF, esto solo ya lo arregla).
#     3) Compara sicuem/adripilot/config_mqtt.json del comma con el de este
#        repo y, si difiere, sube el de este repo (broker correcto).
#     4) Ejecuta tools/sicuem/diag_mqtt_adripilot.py EN EL COMMA y muestra
#        el resultado (import del stack, broker, DongleId, TCP/CONNACK,
#        lineas [Bemposta] del swaglog).
#     5) Opcionalmente reinicia openpilot via param DoReboot (--reiniciar),
#        necesario tras cambiar config o el toggle en builds antiguos.
#
# USO:
#   tools/sicuem/fix_telemetria_comma.sh                 # diagnostica + aplica fixes
#   tools/sicuem/fix_telemetria_comma.sh --reiniciar     # ademas reinicia el comma
#   tools/sicuem/fix_telemetria_comma.sh comma@IP        # host explicito
#
# VARIABLES DE ENTORNO (opcionales):
#   HOST=comma@192.168.43.1   Tethering USB -> 192.168.43.1.
#                             comma prime -> HOST=comma-<dongleid> (ssh.comma.ai)
#   KEY=~/.ssh/mi_github_key  Clave privada SSH (la registrada en el comma).
#   PORT=22                   Puerto SSH.
# ============================================================================
set -uo pipefail

REINICIAR=0
HOST_ARG=""
for a in "$@"; do
  case "$a" in
    --reiniciar) REINICIAR=1 ;;
    *) HOST_ARG="$a" ;;
  esac
done

HOST="${HOST_ARG:-${HOST:-comma@192.168.43.1}}"
PORT="${PORT:-22}"
REMOTE_OP="/data/openpilot"
LOCAL_CFG="$(cd "$(dirname "$0")/../.." && pwd)/sicuem/adripilot/config_mqtt.json"

SSH_OPTS=(-p "$PORT" -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new)
if [ -n "${KEY:-}" ]; then SSH_OPTS+=(-i "$KEY"); fi
ssh_do() { ssh "${SSH_OPTS[@]}" "$HOST" "$@"; }

banner() { printf '\n\033[1;36m==== %s ====\033[0m\n' "$*"; }
err()    { printf '\033[1;31m%s\033[0m\n' "$*" >&2; }

banner "Probando conexion SSH a $HOST"
if ! ssh_do "echo conectado_ok" 2>/dev/null | grep -q conectado_ok; then
  err "No se pudo conectar a $HOST por SSH (puerto $PORT)."
  err "  - Tethering USB: el comma suele ser 192.168.43.1"
  err "  - comma prime:   HOST=comma-<dongleid> (config ssh.comma.ai)"
  err "  - Clave:         KEY=~/.ssh/tu_clave (la registrada en Settings del comma)"
  exit 1
fi
echo "OK"

banner "1) Version del codigo en el comma"
REMOTE_COMMIT="$(ssh_do "cat /data/params/d/GitCommit 2>/dev/null || cd $REMOTE_OP && git rev-parse HEAD 2>/dev/null" | tr -d '\r')"
LOCAL_COMMIT="$(git -C "$(dirname "$0")/../.." rev-parse HEAD 2>/dev/null)"
echo "  comma : ${REMOTE_COMMIT:-desconocido}"
echo "  local : ${LOCAL_COMMIT:-desconocido}"
if [ -n "$REMOTE_COMMIT" ] && [ -n "$LOCAL_COMMIT" ] && [ "$REMOTE_COMMIT" != "$LOCAL_COMMIT" ]; then
  err "  >>> EL COMMA CORRE UN BUILD DISTINTO A ESTE REPO <<<"
  echo "      Si el build del comma es antiguo, la telemetria podia estar gated por"
  echo "      el toggle telemetria_uem (paso 2 lo activa). Lo ideal es actualizar el"
  echo "      comma a este build (git pull + scons en el comma)."
fi

banner "2) Forzando telemetria_uem=1 en el comma"
ssh_do "mkdir -p /data/params/d && printf '1' > /data/params/d/telemetria_uem && echo -n 'telemetria_uem=' && cat /data/params/d/telemetria_uem"

banner "3) Broker MQTT (config_mqtt.json)"
REMOTE_CFG="$(ssh_do "cat $REMOTE_OP/sicuem/adripilot/config_mqtt.json 2>/dev/null" | tr -d '\r')"
echo "  comma : ${REMOTE_CFG:-<no existe>}"
echo "  local : $(cat "$LOCAL_CFG")"
if [ -z "$REMOTE_CFG" ] || ! echo "$REMOTE_CFG" | grep -q "$(grep -o '\"broker\": *\"[^\"]*\"' "$LOCAL_CFG" | grep -o '[0-9.]*')"; then
  echo "  -> Subiendo el config_mqtt.json de este repo al comma..."
  ssh_do "cat > $REMOTE_OP/sicuem/adripilot/config_mqtt.json" < "$LOCAL_CFG"
  ssh_do "cat $REMOTE_OP/sicuem/adripilot/config_mqtt.json"
else
  echo "  OK: el comma ya apunta al broker correcto."
fi

banner "4) Diagnostico MQTT en el comma"
ssh_do "cd $REMOTE_OP && { [ -x .venv/bin/python3 ] && PB=.venv/bin/python3 || PB=python3; }; PYTHONPATH=$REMOTE_OP \$PB tools/sicuem/diag_mqtt_adripilot.py 2>&1"

if [ "$REINICIAR" -eq 1 ]; then
  banner "5) Reiniciando openpilot en el comma (param DoReboot)"
  ssh_do "cd $REMOTE_OP && PYTHONPATH=$REMOTE_OP python3 -c \"from openpilot.common.params import Params; Params().put_bool('DoReboot', True)\""
  echo "  El comma se reiniciara en unos segundos. Espera ~1 min y comprueba la app."
else
  banner "5) Reinicio"
  echo "  Para aplicar los cambios reinicia el comma (o relanza con --reiniciar):"
  echo "    $0 --reiniciar ${HOST_ARG:-}"
fi

banner "FIN"
echo "Si el diagnostico (4) muestra '[Bemposta] fallo iniciando' o el import FALLA,"
echo "el comma necesita actualizar el codigo a este build (los fixes nuevos incluyen"
echo "reintento automatico del hilo MQTT cada 30 s desde el manager)."
