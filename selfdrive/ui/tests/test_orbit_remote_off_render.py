"""Humo de render del bloqueo del mando remoto (OrbitRemoteOff), en la mici y en la grande.

Cada UI en su proceso (`BIG` se lee al importar application.py). Comprueba: activar escribe
el Param y DESPUES desarma todo, quitarlo pide confirmacion y no escribe hasta confirmar,
y el registro de ordenes remotas se abre y pinta (vacio y con filas) sin excepciones.
"""
import os
import subprocess
import sys

import pytest

from openpilot.common.basedir import BASEDIR

GUION = r'''
import json
import os
import pyray as rl
rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)

from openpilot.common.params import Params
from openpilot.common.prefix import OpenpilotPrefix
from openpilot.system.ui.lib.application import gui_app

BIG = bool(os.environ.get("BIG"))

with OpenpilotPrefix():
  p = Params()
  from openpilot.selfdrive.ui.ui_state import ui_state
  from openpilot.selfdrive.ui.widgets import orbit_ajustes as aj
  from openpilot.selfdrive.ui.widgets import orbit_mando

  gui_app.init_window("test remote off")
  ui_state.update_params()
  rt = rl.load_render_texture(gui_app.width, gui_app.height)
  pila = gui_app._nav_stack

  def frames(n=10):
    for _ in range(n):
      ui_state.update()
      rl.begin_drawing()
      rl.begin_texture_mode(rt)
      rl.clear_background(rl.BLACK)
      for w in pila[-gui_app._nav_stack_widgets_to_render:]:
        w.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
      rl.end_texture_mode()
      rl.end_drawing()

  # Orden de escritura: al desarmar, el Param ya tiene que estar puesto.
  vistos = []
  original = orbit_mando.disarm_all
  def disarm_espia():
    vistos.append(p.get_bool("OrbitRemoteOff"))
    return original()
  orbit_mando.disarm_all = disarm_espia

  if BIG:
    from openpilot.selfdrive.ui.sunnypilot.layouts.settings import orbit_panel as op
    panel = op.OrbitLayout()
    activar, quitar = panel._on_remote_off, panel._on_remote_off
    abrir_registro = lambda: panel._set_current_panel(op.PanelType.REGISTRO)
    cerrar_registro = lambda: panel._set_current_panel(op.PanelType.MAIN)
    from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog as confirmacion
    def confirma():
      d = pila[-1]
      assert isinstance(d, confirmacion)
      d._callback(op.DialogResult.CONFIRM)
      gui_app.pop_widget()
    def cancela():
      d = pila[-1]
      assert isinstance(d, confirmacion)
      d._callback(op.DialogResult.CANCEL)
      gui_app.pop_widget()
    assert panel._remote_off_toggle in panel._scroller._items and panel._remote_log_button in panel._scroller._items
  else:
    from openpilot.selfdrive.ui.sunnypilot.mici.layouts import orbit as op
    from openpilot.selfdrive.ui.sunnypilot.mici.widgets.orbit_widgets import PaginaConfirmacion
    panel = op.OrbitLayoutMici()
    activar = quitar = panel._on_remoto
    def abrir_registro():
      panel._btn_registro._click_callback()
    def cerrar_registro():
      gui_app.pop_widget()
    def confirma():
      assert isinstance(pila[-1], PaginaConfirmacion)
      gui_app.pop_widget()
      panel._aplicar_remoto(False)
    def cancela():
      assert isinstance(pila[-1], PaginaConfirmacion)
      gui_app.pop_widget()
    assert panel._btn_registro.is_visible and panel._tgl_remoto in panel._scroller._items

  gui_app.push_widget(panel)
  frames()

  # --- registro vacio
  p.remove("OrbitRemoteLog")
  n = len(pila)
  abrir_registro()
  frames()
  if not BIG:
    assert len(pila) == n + 1
  cerrar_registro()
  frames(3)

  # --- con filas, incluida una rota
  p.put("OrbitRemoteLog", json.dumps([
    {"t": 1764000000, "o": "v2", "v": "lane_change", "f": "rejected", "r": "REMOTE_OFF", "n": 3},
    {"t": 1763999990, "o": "cfg", "v": "cfg", "f": "applied", "r": "", "n": 1},
    {"roto": True}]), True)
  abrir_registro()
  frames()
  cerrar_registro()
  frames(3)

  # --- activar: Param y despues desarmar
  p.put("SteerTorqueMode", 2, True)
  assert not p.get_bool("OrbitRemoteOff")
  activar(True)
  frames(3)
  assert p.get_bool("OrbitRemoteOff") and vistos == [True], vistos
  assert p.get("SteerTorqueMode") == 0 and p.get_bool("OrbitDisarmAll")

  # --- quitar: pide confirmacion; cancelar no escribe
  n = len(pila)
  quitar(False)
  frames(3)
  assert len(pila) == n + 1, [type(w).__name__ for w in pila]
  assert p.get_bool("OrbitRemoteOff")
  cancela()
  frames(3)
  assert p.get_bool("OrbitRemoteOff")
  quitar(False)
  frames(3)
  confirma()
  frames(3)
  assert not p.get_bool("OrbitRemoteOff") and vistos == [True]

  if BIG:
    # --- desvinculo: «Desvinculando…» en la cabecera y el fallo salta tambien en este panel.
    p.put_bool("OrbitClaimed", True, True)
    p.put(orbit_mando.PARAM_OWNER, "Ana", True)
    p.put_bool("OrbitUnlinkRequest", True, True)
    panel._mando_card._last_refresh = 0.0
    frames(3)
    assert ("Desvinculando...", False) in panel._mando_card._estado, panel._mando_card._estado
    p.put_bool("OrbitUnlinkRequest", False, True)
    p.put("OrbitUnlinkResult", json.dumps({"ok": False, "reason": "no_nonce"}), True)
    n = len(pila)
    panel._fallo_desvinculo_t = 0.0
    frames(3)
    assert len(pila) == n + 1, [type(w).__name__ for w in pila]
    assert p.get("OrbitUnlinkResult") is None, "se consume: una sola vez"
    gui_app.pop_widget()
print("RENDER_OK")
'''


@pytest.mark.parametrize("big", [False, True], ids=["mici", "big"])
def test_remote_off_renderiza(big):
  env = dict(os.environ, OFFSCREEN="1", SCALE="1.0")
  env.pop("BIG", None)
  if big:
    env["BIG"] = "1"
  r = subprocess.run([sys.executable, "-c", GUION], cwd=BASEDIR, env=env, capture_output=True, text=True, timeout=300)
  assert r.returncode == 0 and "RENDER_OK" in r.stdout, (r.stdout[-3000:] + r.stderr[-6000:])
