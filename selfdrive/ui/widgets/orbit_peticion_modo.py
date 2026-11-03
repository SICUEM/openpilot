"""
Peticion REMOTA de modo de volante (verbo steer_mode_request): la app PIDE, el comma
pregunta a pantalla completa y una persona la ACEPTA o la RECHAZA delante del coche.

El broker MQTT es abierto, asi que la autoridad del volante nunca sube solo por MQTT: el
handler (orbit/mqtt_comandos.py) deja la peticion en OrbitSteerModeRequest y la unica forma
de aplicarla es Aceptar aqui, que pasa EXACTAMENTE por el camino del selector local
(aplicar_modo_volante + fijar_objetivo_esquive, con OrbitSteerModeLocal).

Logica pura compartida por la UI grande (3X) y la mici (comma 4): aqui no se pinta nada.
El veredicto viaja al router por OrbitCmdResult, el mismo hueco que usan desire_helper y
card; si esta ocupado se guarda y se escribe en el siguiente tick (el router lo vacia a
50 Hz mientras haya algo pendiente).
"""
import json

from openpilot.common.swaglog import cloudlog
from openpilot.orbit.command_spec import Phase, ahora_epoch_ms, ahora_mono
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes

PARAM = "OrbitSteerModeRequest"
PARAM_RESULTADO = "OrbitCmdResult"
VERBO = "steer_mode_request"

# Mismos nombres que los botones del selector local (orbit_ajustes.MODE_BUTTONS).
NOMBRES = {modo: ajustes.MODE_BUTTONS[i] for modo, i in ajustes.MODE_TO_INDEX.items()}
OBJETIVOS = {"curvature": "CURVATURA", "torque": "TORQUE"}

# Veredictos que aun no han cabido en OrbitCmdResult.
_por_escribir: list[dict] = []


def _validar(crudo) -> dict | None:
  """La peticion si es una 1-3 bien formada; None si no. El 0 nunca llega aqui."""
  try:
    if isinstance(crudo, bytes):
      crudo = crudo.decode("utf-8")
    d = json.loads(crudo) if isinstance(crudo, str) else crudo
  except (ValueError, UnicodeDecodeError):
    return None
  if not isinstance(d, dict) or d.get("v") != 1:
    return None
  modo, objetivo, cid, deadline = d.get("mode"), d.get("apply_target"), d.get("id"), d.get("deadline_mono")
  if isinstance(modo, bool) or modo not in (1, 2, 3):
    return None
  if objetivo not in (None, *OBJETIVOS) or (modo == 3 and objetivo is None):
    return None
  if not isinstance(cid, str) or not cid or isinstance(deadline, bool) or not isinstance(deadline, (int, float)):
    return None
  return {"id": cid, "mode": modo, "apply_target": objetivo, "deadline_mono": float(deadline)}


def _vaciar(params) -> None:
  if _por_escribir and not params.get(PARAM_RESULTADO):
    params.put(PARAM_RESULTADO, json.dumps(_por_escribir.pop(0), separators=(",", ":")), True)


def _cerrar(params, pet: dict, fase: str, motivo: str, detalle: str) -> None:
  params.remove(PARAM)
  _por_escribir.append({"v": 2, "verb": VERBO, "id": pet["id"], "phase": fase, "reason": motivo,
                        "detail": detalle, "ts_ms": ahora_epoch_ms(), "mono_ms": int(ahora_mono() * 1000)})
  _vaciar(params)
  cloudlog.warning(f"[Orbit/UI] peticion de modo {pet['mode']} ({pet['id']}): {fase}")


def tick(params, ahora: float | None = None) -> dict | None:
  """Una vez por refresco: escribe veredictos pendientes, caduca la peticion vencida y
  devuelve la vigente (o None)."""
  _vaciar(params)
  crudo = params.get(PARAM)
  if not crudo:
    return None
  pet = _validar(crudo)
  if pet is None:
    params.remove(PARAM)   # basura: no hay nada que preguntar ni a quien contestar
    return None
  if (ahora_mono() if ahora is None else ahora) > pet["deadline_mono"]:
    _cerrar(params, pet, Phase.EXPIRED, "EXPIRED", "nadie confirmo en el comma a tiempo")
    return None
  return pet


def texto(pet: dict) -> str:
  t = f"La app pide modo {NOMBRES[pet['mode']]}"
  if pet["apply_target"]:
    t += f" ({OBJETIVOS[pet['apply_target']]})"
  return t


def aceptar(params, engaged: bool, ahora: float | None = None) -> bool:
  """Aplica la peticion vigente por el camino del selector local. Nunca con openpilot
  enganchado: el cambio de quien lleva el volante se hace con el coche en manos del conductor."""
  if engaged:
    return False
  pet = tick(params, ahora)   # se relee: pudo caducar o sustituirse desde que se pinto
  if pet is None:
    return False
  if pet["apply_target"]:
    ajustes.fijar_objetivo_esquive(params, pet["apply_target"])
  ajustes.aplicar_modo_volante(params, pet["mode"])
  _cerrar(params, pet, Phase.APPLIED, "OK", f"modo {NOMBRES[pet['mode']]} aceptado en el comma")
  return True


def rechazar(params, ahora: float | None = None) -> bool:
  pet = tick(params, ahora)
  if pet is None:
    return False
  _cerrar(params, pet, Phase.REJECTED, "MODE", "rechazado en el comma")
  return True
