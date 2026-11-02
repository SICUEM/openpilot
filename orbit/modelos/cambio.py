"""Cambio de modelo EN MARCHA, sin reiniciar modeld ni el coche.

modeld llama a Vigilante.revisar() en cada ciclo. Una vez por segundo mira lo que decide la
eleccion (OrbitModeloDeseado y si chestnut esta conectado). Si eso cambia y el modelo que tocaria
cargar no es el que esta corriendo, el cambio queda PENDIENTE y se publica en OrbitModeloActivo.

  cambio pedido (app o chestnut que aparece) ... se aplica con el coche PARADO y openpilot
                                                 DESACOPLADO: recargar deja ~1-5 s sin modelV2 y
                                                 eso no puede pasar conduciendo
  chestnut desaparece con el modelo en el ...... se aplica YA, aunque el coche se mueva: el
  chestnut                                       modelo ya no tiene donde ejecutarse y el de
                                                 serie del comma carga en menos de un segundo

Si el modelo pedido no se puede cargar, se carga lo que diria el arranque (seleccion.candidatos):
el mismo valor de OrbitModeloDeseado da siempre el mismo modelo, arranque o en marcha. Si fallo
AL CARGAR (la GPU aun ocupada por el compilador del gestor al arrancar el coche, p. ej.), se
reintenta REINTENTO_S despues, hasta MAX_REINTENTOS veces, tambien con el coche parado y
desacoplado. Despues no se vuelve a intentar hasta que algo cambie: un modelo que no carga no se
reintenta en cada parada.

Tiempo real: el modelo en el comma corre con SCHED_FIFO en un nucleo (como el modeld de serie);
el de chestnut NO, porque el USB satura un nucleo. tiempo_real() lo pone o lo quita en cada carga.
"""
import gc
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

from openpilot.common.realtime import config_realtime_process, set_core_affinity
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware import PC
from openpilot.orbit.modelos import seleccion
from openpilot.orbit.modelos.seleccion import Candidato

PERIODO_S = 1.0
V_PARADO = 0.1  # m/s
REINTENTO_S = 10.0
MAX_REINTENTOS = 2
NUCLEO_RT, PRIORIDAD_RT = 7, 54

CAMBIO_PEDIDO = "cambio pedido"
CHESTNUT_PERDIDO = "chestnut desconectado"
FALLO_EJECUCION = "el modelo fallo ejecutandose"


@dataclass(frozen=True)
class Entrada:
  """Lo que decide que modelo toca cargar."""
  deseado: str | None
  chestnut: bool


def parado(v_ego: float, standstill: bool) -> bool:
  return standstill or v_ego < V_PARADO


def mismo_modelo(a: Candidato, b: Candidato) -> bool:
  return a.pkl == b.pkl and a.destino == b.destino


def tiempo_real(activar: bool, actual: bool) -> bool:
  """Pone o quita el tiempo real de modeld. Devuelve el estado nuevo."""
  if activar == actual:
    return actual
  if activar:
    config_realtime_process(NUCLEO_RT, PRIORIDAD_RT)
  else:
    if sys.platform == 'linux' and not PC:
      os.sched_setscheduler(0, os.SCHED_OTHER, os.sched_param(0))
    set_core_affinity(list(range(os.cpu_count() or 1)))
    gc.enable()
  return activar


class Vigilante:
  def __init__(self, params, activo: Candidato, entrada: Entrada, estado: dict,
               leer_entrada: Callable[[], Entrada], objetivo: Callable[[Entrada], Candidato],
               ahora: Callable[[], float] = time.monotonic, fallo_carga: bool = False):
    """`leer_entrada()`: la Entrada de ahora. `objetivo(entrada)`: el primer candidato que daria
    la eleccion con esa entrada. `estado`: lo publicado en OrbitModeloActivo al cargar."""
    self.params = params
    self.leer_entrada = leer_entrada
    self.objetivo = objetivo
    self.ahora = ahora
    self.pendiente: Candidato | None = None
    self.entrada: Entrada | None = None
    self.reintentos = 0
    self.cargado(activo, entrada, estado, fallo_carga)

  def cargado(self, activo: Candidato, entrada: Entrada, estado: dict, fallo_carga: bool = False) -> None:
    """modeld acaba de cargar `activo` con `entrada`. `fallo_carga`: un candidato anterior no cargo."""
    if entrada != self.entrada:
      self.reintentos = 0
    self.activo, self.entrada, self.estado = activo, entrada, estado
    self.pendiente = None
    self._t = self.ahora()
    self._reintento: float | None = None
    if fallo_carga and self.reintentos < MAX_REINTENTOS:
      self.reintentos += 1
      self._reintento = self._t + REINTENTO_S

  def revisar(self, coche_parado: bool, acoplado: bool) -> str | None:
    """El motivo para recargar el modelo AHORA, o None."""
    if self.ahora() - self._t >= PERIODO_S:
      self._t = self.ahora()
      entrada = self.leer_entrada()
      if self.activo.en_chestnut and not entrada.chestnut:
        self.entrada = entrada
        return CHESTNUT_PERDIDO
      if entrada != self.entrada:
        self.entrada = entrada
        objetivo = self.objetivo(entrada)
        self._marcar_pendiente(None if mismo_modelo(objetivo, self.activo) else objetivo)
      elif self._reintento is not None and self.ahora() >= self._reintento:
        self._reintento = None
        objetivo = self.objetivo(entrada)
        if not mismo_modelo(objetivo, self.activo):
          self._marcar_pendiente(objetivo)
    if self.pendiente is not None and coche_parado and not acoplado:
      return CAMBIO_PEDIDO
    return None

  def _marcar_pendiente(self, objetivo: Candidato | None) -> None:
    if objetivo == self.pendiente:
      return
    self.pendiente = objetivo
    texto = "" if objetivo is None else f"{objetivo.origen} {objetivo.modelo_id or ''}".strip()
    self.estado = {**self.estado, "deseado": self.entrada.deseado, "pendiente": texto}
    try:
      seleccion.publicar_activo(self.params, self.estado)
    except Exception:
      cloudlog.exception("orbit: no se pudo publicar OrbitModeloActivo")
