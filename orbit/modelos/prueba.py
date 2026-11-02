"""Periodo de prueba y vetos: que un modelo que carga pero no funciona no deje el coche sin modelo.

Cargar un .pkl (pickle.loads) no garantiza que funcione: un tinygrad distinto o un warp compilado
para otro dispositivo revientan en la PRIMERA ejecucion. Sin esto, modeld se caeria, el manager lo
reiniciaria, volveria a elegir el mismo modelo y asi todo el viaje.

  PRUEBA ...... los primeros FRAMES_PRUEBA frames con salida de un modelo recien cargado (menos el
                pequeno de serie, que es la red final). Mientras dura, OrbitModeloEnPrueba dice cual.
  falla en prueba (excepcion o salidas no finitas) ... se VETA y modeld carga el siguiente al momento
  falla despues de la prueba ......................... se descarta en esta sesion de modeld, sin veto
  modeld muere en prueba (segfault, cuelgue...) ...... al arrancar, OrbitModeloEnPrueba sigue ahi:
                                                       cuenta una caida; con MAX_CAIDAS, se VETA
  chestnut desconectado .............................. nunca veta: el modelo no tiene la culpa

Un veto (OrbitModeloVetos) vale mientras no cambien el .pkl ni el tinygrad del repo: entregar o
compilar de nuevo el modelo lo levanta. Todo queda en OrbitModeloErrores (errores.py).
"""
import json
import time
from pathlib import Path

import numpy as np

from openpilot.orbit.modelos import errores
from openpilot.orbit.modelos import paquete as pq
from openpilot.orbit.modelos.seleccion import SERIE, Candidato

PARAM_EN_PRUEBA = "OrbitModeloEnPrueba"
PARAM_VETOS = "OrbitModeloVetos"
FRAMES_PRUEBA = 40      # ~2 s a 20 Hz
MAX_CAIDAS = 2          # una caida suelta puede ser otra cosa (apagar el coche justo al arrancar)
PRESUPUESTO_S = 0.05    # modeld corre a 20 Hz: mas lento que esto pierde frames


def clave(c: Candidato) -> str:
  return str(c.pkl)


def nombre(c: Candidato) -> str:
  return f"{c.origen} {c.modelo_id or ''}".strip()


def protegido(c: Candidato) -> bool:
  """El pequeno de serie no tiene red: si falla, falla como antes de ORBIT."""
  return c.origen != SERIE


def huella_actual(pkl) -> dict:
  return {"pkl": pq.huella(Path(pkl)), "tinygrad": pq.tinygrad_ref()}


def _leer(params, clave_param: str):
  try:
    datos = json.loads(params.get(clave_param) or "null")
  except (TypeError, ValueError):
    return None
  return datos if isinstance(datos, dict) else None


# ------------------------------------------------------------------ vetos

def vetos(params) -> dict:
  return _leer(params, PARAM_VETOS) or {}


def motivo_veto(params, c: Candidato) -> str | None:
  v = vetos(params).get(clave(c))
  if isinstance(v, dict) and v.get("huella") == huella_actual(c.pkl):
    return str(v.get("motivo", ""))
  return None


def vetar(params, pkl, modelo_id: str | None, origen: str, huella: dict, motivo: str) -> None:
  todos = vetos(params)
  todos[str(pkl)] = {"modelo_id": modelo_id, "origen": origen, "huella": huella, "motivo": motivo[:300],
                     "ts_ms": time.time_ns() // 1_000_000}
  params.put(PARAM_VETOS, json.dumps(todos, sort_keys=True))


def filtrar(params, lista: list[Candidato], motivos: list[str], excluidos=frozenset()) -> list[Candidato]:
  """Quita los vetados y los descartados en esta sesion (`excluidos`: claves). El ultimo candidato
  (el pequeno de serie) se queda siempre."""
  quedan = []
  for c in lista[:-1]:
    if clave(c) in excluidos:
      motivos.append(f"{nombre(c)} descartado: fallo ejecutandose en esta sesion")
    elif (m := motivo_veto(params, c)) is not None:
      motivos.append(f"{nombre(c)} vetado: {m}")
    else:
      quedan.append(c)
  return quedan + lista[-1:]


# ------------------------------------------------------------------ periodo de prueba

def abandonar(params) -> None:
  """modeld se cierra normal (el manager lo para): no cuenta como caida."""
  params.remove(PARAM_EN_PRUEBA)


def revisar_arranque(params, chestnut_presente: bool) -> None:
  """Al arrancar modeld: si quedo un modelo en prueba, el modeld anterior murio con el."""
  previo = _leer(params, PARAM_EN_PRUEBA)
  if previo is None:
    return
  modelo_id, origen = previo.get("modelo_id"), previo.get("origen", "")
  if previo.get("en_chestnut") and not chestnut_presente:
    params.remove(PARAM_EN_PRUEBA)
    errores.registrar(params, "arranque", "modeld murio con el modelo en prueba y chestnut ya no esta: no cuenta contra el modelo",
                      modelo_id, errores.AVISO, origen=origen, pkl=previo.get("pkl"))
    return
  caidas = int(previo.get("caidas", 0)) + 1
  detalle = f"modeld murio con el modelo en prueba (caida {caidas} de {MAX_CAIDAS}): cuelgue o fallo nativo al ejecutarlo"
  if caidas >= MAX_CAIDAS:
    params.remove(PARAM_EN_PRUEBA)
    vetar(params, previo.get("pkl"), modelo_id, origen, previo.get("huella"), detalle)
    detalle += "; VETADO hasta que cambie el .pkl o el tinygrad"
  else:
    params.put(PARAM_EN_PRUEBA, json.dumps({**previo, "caidas": caidas}, sort_keys=True))
  errores.registrar(params, "arranque", detalle, modelo_id, origen=origen, pkl=previo.get("pkl"))


def salidas_no_finitas(salidas: dict) -> list[str]:
  return sorted(k for k, v in salidas.items() if isinstance(v, np.ndarray) and v.dtype.kind == "f" and not np.isfinite(v).all())


class Prueba:
  """El periodo de prueba del modelo que modeld acaba de cargar."""
  def __init__(self, params, c: Candidato):
    self.params, self.c = params, c
    self.activa = protegido(c)
    self.frames = 0
    self.tiempos: list[float] = []
    if not self.activa:
      params.remove(PARAM_EN_PRUEBA)
      return
    self.huella = huella_actual(c.pkl)
    previo = _leer(params, PARAM_EN_PRUEBA) or {}
    mismo = previo.get("pkl") == clave(c) and previo.get("huella") == self.huella
    params.put(PARAM_EN_PRUEBA, json.dumps({
      "pkl": clave(c), "modelo_id": c.modelo_id, "origen": c.origen, "en_chestnut": c.en_chestnut,
      "huella": self.huella, "caidas": int(previo.get("caidas", 0)) if mismo else 0,
    }, sort_keys=True))

  def _info(self) -> dict:
    return {"origen": self.c.origen, "destino": self.c.destino, "pkl": clave(self.c)}

  def revisar(self, salidas: dict, t_ejecucion: float) -> str | None:
    """Tras cada frame con salida. Devuelve el motivo si el modelo falla la prueba (ya vetado)."""
    if not self.activa:
      return None
    if malas := salidas_no_finitas(salidas):
      detalle = f"salidas no finitas (NaN/inf) en el frame {self.frames + 1}: {', '.join(malas)}"
      self.fallo("salidas", detalle)
      return detalle
    self.frames += 1
    self.tiempos.append(t_ejecucion)
    if self.frames >= FRAMES_PRUEBA:
      self.activa = False
      self.params.remove(PARAM_EN_PRUEBA)
      mediana = sorted(self.tiempos)[len(self.tiempos) // 2]
      if mediana > PRESUPUESTO_S:
        errores.registrar(self.params, "rendimiento",
                          f"mediana {mediana * 1000:.0f} ms por frame (presupuesto {PRESUPUESTO_S * 1000:.0f} ms): perdera frames",
                          self.c.modelo_id, errores.AVISO, **self._info())
    return None

  def fallo(self, fase: str, detalle: str) -> None:
    """El modelo fallo ejecutandose (no por chestnut desconectado). En prueba se veta."""
    if self.activa:
      self.activa = False
      self.params.remove(PARAM_EN_PRUEBA)
      vetar(self.params, self.c.pkl, self.c.modelo_id, self.c.origen, self.huella, f"{fase}: {detalle}")
      detalle += "; VETADO hasta que cambie el .pkl o el tinygrad"
    else:
      detalle += "; descartado hasta que reinicie modeld"
    errores.registrar(self.params, fase, detalle, self.c.modelo_id, **self._info())
