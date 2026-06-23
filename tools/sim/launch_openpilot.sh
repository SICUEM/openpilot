#!/usr/bin/env bash

export PASSIVE="0"
export NOBOARD="1"
export SIMULATION="1"
export SKIP_FW_QUERY="1"
export FINGERPRINT="HONDA_CIVIC_2022"
# Forzar la pantalla del Comma 3X (tici, 2160x1080) en el sim del PC en vez de la
# UI pequena 536x240 del dispositivo "mici". Se puede sobreescribir con BIG=0.
export BIG="${BIG:-1}"

export BLOCK="${BLOCK},camerad,loggerd,encoderd,micd,logmessaged,manage_athenad,manage_sunnylinkd"
if [[ "$CI" ]]; then
  # TODO: offscreen UI should work
  export BLOCK="${BLOCK},ui"
fi

python3 -c "from openpilot.selfdrive.test.helpers import set_params_enabled; set_params_enabled()"

SCRIPT_DIR=$(dirname "$0")
OPENPILOT_DIR=$SCRIPT_DIR/../../

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $OPENPILOT_DIR/system/manager && exec ./manager.py
