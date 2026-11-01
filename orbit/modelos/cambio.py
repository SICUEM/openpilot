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
el mismo valor de OrbitModeloDeseado da siempre el mismo modelo, arranque o en marcha. Tras
recargar no se vuelve a intentar hasta que algo cambie de nuevo: un modelo que no carga no se
reintenta en cada parada.
"""
import time
from collections.abc import Callable
from dataclasses import dataclass

from openpilot.common.swaglog import cloudlog
from openpilot.orbit.modelos import seleccion
from openpilot.orbit.modelos.seleccion import Candidato

PERIODO_S = 1.0
V_PARADO = 0.1  # m/s

CAMBIO_PEDIDO = "cambio pedido"
CHESTNUT_PERDIDO = "chestnut desconectado"


@dataclass(frozen=True)
class Entrada:
  """Lo que decide que modelo toca cargar."""
  deseado: str | None
  chestnut: bool


def parado(v_ego: float, standstill: bool) -> bool:
  return standstill or v_ego < V_PARADO


def mismo_modelo(a: Candidato, b: Candidato) -> bool:
  return a.pkl == b.pkl and a.destino == b.destino


class Vigilante:
  def __init__(self, params, activo: Candidato, entrada: Entrada, estado: dict,
               leer_entrada: Callable[[], Entrada], objetivo: Callable[[Entrada], Candidato],
               ahora: Callable[[], float] = time.monotonic):
    """`leer_entrada()`: la Entrada de ahora. `objetivo(entrada)`: el primer candidato que daria
    la eleccion con esa entrada. `estado`: lo publicado en OrbitModeloActivo al cargar."""
    self.params = params
    self.leer_entrada = leer_entrada
    self.objetivo = objetivo
    self.ahora = ahora
    self.pendiente: Candidato | None = None
    self.cargado(activo, entrada, estado)

  def cargado(self, activo: Candidato, entrada: Entrada, estado: dict) -> None:
    """modeld acaba de cargar `activo` con `entrada`."""
    self.activo, self.entrada, self.estado = activo, entrada, estado
    self.pendiente = None
    self._t = self.ahora()

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
