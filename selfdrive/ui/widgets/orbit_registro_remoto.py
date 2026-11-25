"""Registro de las ultimas ordenes remotas (OrbitRemoteLog) en la UI grande (comma 3X).

Lista desplazable de SOLO LECTURA. El formato de cada linea sale de
orbit_ajustes.lineas_registro_remoto, compartido con el comma 4.
"""
from collections.abc import Callable

import pyray as rl

from openpilot.selfdrive.ui import orbit_theme as t
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.scroll_panel import GuiScrollPanel
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.network import NavButton

ALTO_FILA = 64
TAM_TEXTO = 38


class OrbitRegistroRemoto(Widget):
  def __init__(self, back_btn_callback: Callable):
    super().__init__()
    self._back_button = NavButton(tr("Back"))
    self._back_button.set_click_callback(back_btn_callback)
    self._scroll = GuiScrollPanel()
    self._lineas: list[str] = []
    self._fuente = gui_app.font(FontWeight.NORMAL)
    self._titulo = gui_app.font(FontWeight.BOLD)

  def _leer(self) -> None:
    try:
      self._lineas = ajustes.lineas_registro_remoto(ui_state.params.get(ajustes.PARAM_REMOTE_LOG))
    except Exception:
      self._lineas = []

  def show_event(self):
    super().show_event()
    self._scroll.set_offset(0)
    self._leer()

  def _render(self, rect):
    self._back_button.set_position(rect.x, rect.y + 20)
    self._back_button.render()
    # Titulo de la pantalla (sentence case) y, bajo el, que es esta lista.
    ty = rect.y + self._back_button.rect.height + 30
    rl.draw_text_ex(self._titulo, tr("Órdenes remotas"), rl.Vector2(rect.x + 20, ty), 56, 0.0, t.TEXTO1)
    y0 = ty + 56 + 24
    zona = rl.Rectangle(rect.x, y0, rect.width, rect.height - (y0 - rect.y))

    if not self._lineas:
      rl.draw_text_ex(self._fuente, tr("Todavía no ha llegado ninguna orden de la app o el servidor."), rl.Vector2(zona.x + 20, zona.y + 20),
                      TAM_TEXTO, 0.0, t.TEXTO2)
      return

    desp = self._scroll.update(zona, rl.Rectangle(0, 0, zona.width, len(self._lineas) * ALTO_FILA))
    rl.begin_scissor_mode(int(zona.x), int(zona.y), int(zona.width), int(zona.height))
    for i, linea in enumerate(self._lineas):
      y = zona.y + i * ALTO_FILA + desp
      if y + ALTO_FILA < zona.y or y > zona.y + zona.height:
        continue
      rl.draw_text_ex(self._fuente, linea, rl.Vector2(zona.x + 20, y + 10), TAM_TEXTO, 0.0, t.TEXTO1)
      rl.draw_line_ex(rl.Vector2(zona.x + 20, y + ALTO_FILA - 2), rl.Vector2(zona.x + zona.width - 20, y + ALTO_FILA - 2), 1, t.BORDE)
    rl.end_scissor_mode()
