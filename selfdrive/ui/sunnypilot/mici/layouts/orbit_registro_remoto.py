"""
Registro de las ultimas ordenes remotas (OrbitRemoteLog) en el comma 4 (536x240).

Lista desplazable de solo lectura; las lineas salen de orbit_ajustes.lineas_registro_remoto,
las mismas que pinta la UI grande.
"""
import pyray as rl

from openpilot.selfdrive.ui.mici.widgets.button import LABEL_COLOR, COMPLICATION_GREY
from openpilot.selfdrive.ui.sunnypilot.mici.widgets.orbit_widgets import recortar
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets.scroller import NavRawScrollPanel

ALTO_FILA = 58
TAM = 24
TAM_DETALLE = 20


class OrbitRegistroRemotoMici(NavRawScrollPanel):
  def __init__(self):
    super().__init__()
    self._lineas: list[str] = []
    self._fuente = gui_app.font(FontWeight.ROMAN)

  def show_event(self):
    super().show_event()
    try:
      self._lineas = ajustes.lineas_registro_remoto(ui_state.params.get(ajustes.PARAM_REMOTE_LOG))
    except Exception:
      self._lineas = []

  def _render(self, rect):
    if not self._lineas:
      rl.draw_text_ex(self._fuente, "sin órdenes remotas registradas", rl.Vector2(rect.x + 20, rect.y + 20), TAM, 0,
                      COMPLICATION_GREY)
      return
    alto = len(self._lineas) * ALTO_FILA + 40
    desp = round(self._scroll_panel.update(rect, alto))
    ancho = rect.width - 40
    for i, linea in enumerate(self._lineas):
      y = rect.y + 20 + desp + i * ALTO_FILA
      # Linea 1: hora (gris) y orden (blanco). Linea 2: que paso, en gris: el motivo no se recorta.
      hora, _, resto = linea.partition("  ")
      orden, _, detalle = resto.partition("  ")
      rl.draw_text_ex(self._fuente, hora, rl.Vector2(rect.x + 20, y), TAM, 0, COMPLICATION_GREY)
      x = rect.x + 20 + measure_text_cached(self._fuente, hora + "  ", TAM).x
      rl.draw_text_ex(self._fuente, recortar(self._fuente, orden, TAM, rect.x + 20 + ancho - x), rl.Vector2(x, y), TAM, 0, LABEL_COLOR)
      rl.draw_text_ex(self._fuente, recortar(self._fuente, detalle, TAM_DETALLE, ancho), rl.Vector2(rect.x + 20, y + TAM + 2),
                      TAM_DETALLE, 0, COMPLICATION_GREY)
