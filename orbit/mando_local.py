"""Interruptor local del mando remoto (OrbitRemoteOff) y registro de ordenes remotas.

El interruptor lo escribe SOLO la pantalla del comma. Aqui no hay cache: se lee el Param
en cada decision, porque el bucle de telemetria puede no correr (sin conexion o sin
dongle) mientras el cliente de mando sigue recibiendo ordenes.

El registro (OrbitRemoteLog) vive en RAM y se vuelca a disco como mucho cada 60 s. El
hilo de red solo llama a anotar(), que no toca el disco.
"""
import json
import threading
import time

from openpilot.orbit.command_spec import COMMANDS, REASONS, Gate, ahora_epoch_ms, gate_reason

PARAM_REMOTE_OFF = "OrbitRemoteOff"
PARAM_REMOTE_LOG = "OrbitRemoteLog"

REGISTRO_MAX = 50
VOLCAR_CADA_S = 60.0

ORIGENES = ("v2", "v1", "cfg", "cam", "paso", "dev")
FASES = ("applied", "rejected", "failed", "expired", "superseded", "held", "ignored")
# Conjunto CERRADO: el broker es abierto y un texto libre acabaria pintado en la pantalla.
VERBOS_EXTRA = ("cfg", "cam", "roundabout", "speed_increment")
DESCONOCIDO = "desconocido"
_MOTIVOS = frozenset(REASONS) | {gate_reason(g) for g in Gate}

# Reloj monotono del volcado; los tests lo sustituyen.
_mono = time.monotonic


def remoto_apagado(params) -> bool:
  """Lee OrbitRemoteOff EN CADA LLAMADA. Cualquier fallo cuenta como apagado (falla cerrado)."""
  try:
    return bool(params.get_bool(PARAM_REMOTE_OFF))
  except Exception:
    return True


def _sanear(o, v, f, r) -> dict | None:
  if f not in FASES:
    return None
  return {
    "o": o if o in ORIGENES else DESCONOCIDO,
    "v": v if isinstance(v, str) and (v in COMMANDS or v in VERBOS_EXTRA) else DESCONOCIDO,
    "f": f,
    "r": r if r in _MOTIVOS else "",
  }


class MandoLocal:
  def __init__(self):
    self._lock = threading.Lock()
    self._filas: list[dict] = []   # mas nueva primero
    self._sucio = False
    self._ultimo_volcado = None

  def anotar(self, origen, verbo, fase, motivo="") -> None:
    """Solo RAM: apto para el hilo de red."""
    fila = _sanear(origen, verbo, fase, motivo)
    if fila is None:
      return
    ahora = ahora_epoch_ms() // 1000
    with self._lock:
      cabeza = self._filas[0] if self._filas else None
      if cabeza is not None and all(cabeza[k] == fila[k] for k in ("o", "v", "f", "r")):
        cabeza["n"] += 1
        cabeza["t"] = ahora
      else:
        fila["t"] = ahora
        fila["n"] = 1
        self._filas.insert(0, fila)
        del self._filas[REGISTRO_MAX:]
      self._sucio = True

  def filas(self) -> list[dict]:
    with self._lock:
      return [dict(f) for f in self._filas]

  def volcar(self, params) -> None:
    """Escribe OrbitRemoteLog si hay cambios, como mucho cada VOLCAR_CADA_S."""
    ahora = _mono()
    with self._lock:
      if not self._sucio:
        return
      if self._ultimo_volcado is not None and ahora - self._ultimo_volcado < VOLCAR_CADA_S:
        return
      texto = json.dumps(self._filas, separators=(",", ":"))
      self._sucio = False
      self._ultimo_volcado = ahora
    try:
      params.put(PARAM_REMOTE_LOG, texto)
    except Exception:
      with self._lock:
        self._sucio = True

  def cargar(self, params) -> None:
    """Al arrancar: continua el anillo persistido (detras de lo que ya haya en RAM)."""
    try:
      crudo = params.get(PARAM_REMOTE_LOG)
      if isinstance(crudo, bytes):
        crudo = crudo.decode("utf-8", "replace")
      datos = json.loads(crudo) if crudo else []
    except Exception:
      return
    if not isinstance(datos, list):
      return
    cargadas = []
    for d in datos:
      if not isinstance(d, dict):
        continue
      fila = _sanear(d.get("o"), d.get("v"), d.get("f"), d.get("r"))
      t, n = d.get("t"), d.get("n")
      if fila is None or isinstance(t, bool) or not isinstance(t, int) or isinstance(n, bool) \
         or not isinstance(n, int) or n < 1:
        continue
      fila["t"] = t
      fila["n"] = n
      cargadas.append(fila)
    with self._lock:
      self._filas = (self._filas + cargadas)[:REGISTRO_MAX]


_singleton: MandoLocal | None = None
_singleton_lock = threading.Lock()


def get_mando_local() -> MandoLocal:
  global _singleton
  with _singleton_lock:
    if _singleton is None:
      _singleton = MandoLocal()
    return _singleton
