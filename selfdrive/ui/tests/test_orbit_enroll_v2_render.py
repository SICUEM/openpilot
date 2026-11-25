"""Humo de render del QR de vinculacion v2, en la mici y en la grande.

Cada UI en su proceso (`BIG` se lee al importar application.py). Comprueba: el QR lleva
`&v=2` con un token de 26 caracteres, el codigo legible en grupos de 4 cabe sin recortar, y
sin codigo (reloj sin sincronizar) no se pinta QR sino "Sincronizando la hora del comma...".
"""
import os
import subprocess
import sys

import pytest

from openpilot.common.basedir import BASEDIR

GUION = r'''
import os
from types import SimpleNamespace
import pyray as rl
rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)

from openpilot.common.params import Params
from openpilot.common.prefix import OpenpilotPrefix
from openpilot.orbit.enroll_v2 import codigo_legible
from openpilot.system.ui.lib.application import gui_app

BIG = bool(os.environ.get("BIG"))
TOKEN = "ABCDEFGHJKLMNPQRSTUVWXYZ23"

with OpenpilotPrefix():
  p = Params()
  p.put("DongleId", "0123456789abcdef", True)
  p.put_bool("OrbitClaimed", False, True)
  from openpilot.selfdrive.ui.ui_state import ui_state
  from openpilot.selfdrive.ui.widgets import orbit_ajustes as aj
  from openpilot.selfdrive.ui.widgets import orbit_enroll_dialog as grande
  from openpilot.system.ui.lib.text_measure import measure_text_cached

  gui_app.init_window("test enroll v2")
  ui_state.update_params()
  rt = rl.load_render_texture(gui_app.width, gui_app.height)

  urls = []
  original = grande.generar_textura_qr
  def espia(url, previa=None):
    urls.append(url)
    return original(url, previa)
  grande.generar_textura_qr = espia

  if BIG:
    dlg = grande.OrbitEnrollDialog()
  else:
    from openpilot.selfdrive.ui.sunnypilot.mici.widgets import orbit_enroll_dialog as mici
    mici.generar_textura_qr = espia
    mici.OrbitEnrollDialogMici.POLL_S = 0.0
    dlg = mici.OrbitEnrollDialogMici()
  gui_app.push_widget(dlg)

  def frames(n=5):
    for _ in range(n):
      ui_state.update()
      rl.begin_drawing()
      rl.begin_texture_mode(rt)
      rl.clear_background(rl.BLACK)
      for w in gui_app._nav_stack[-gui_app._nav_stack_widgets_to_render:]:
        w.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
      rl.end_texture_mode()
      rl.end_drawing()

  def vista(sincronizado):
    return SimpleNamespace(available=True, clock_synced=sincronizado, update=lambda sm: None)

  # Sin codigo y sin reloj: ni QR ni token.
  ui_state.orbit_command = vista(False)
  assert not aj.reloj_sincronizado(ui_state.orbit_command)
  assert aj.texto_sin_codigo(False) == "Sincronizando la hora del comma..."
  p.remove("OrbitPairingCode")
  frames()
  assert urls == [], urls
  ui_state.orbit_command = vista(True)
  frames()

  # Con token v2.
  p.put("OrbitPairingCode", TOKEN, True)
  frames()
  assert urls and urls[-1] == f"orbit://enroll?d=0123456789abcdef&c={TOKEN}&v=2", urls
  assert codigo_legible(TOKEN) == "ABCD EFGH JKLM NPQR STUV WXYZ 23"

  # El codigo legible cabe sin recortar.
  fuente = gui_app.font(grande.FontWeight.DISPLAY if not BIG else grande.FontWeight.BOLD)
  if not BIG:
    x = 8 + gui_app.height + 18
    ancho = gui_app.width - 14 - x
    for linea in ("ABCD EFGH JKLM NPQR", "STUV WXYZ 23"):
      assert measure_text_cached(fuente, linea, 22).x <= ancho, (linea, ancho)
  else:
    assert measure_text_cached(fuente, codigo_legible(TOKEN), 40).x < gui_app.width / 2

  # Legacy (pc, 8 caracteres): sin &v=2.
  p.put("OrbitPairingCode", "K7QX4MPA", True)
  frames()
  assert urls[-1] == "orbit://enroll?d=0123456789abcdef&c=K7QX4MPA", urls[-1]
print("RENDER_OK")
'''


@pytest.mark.parametrize("big", [False, True], ids=["mici", "big"])
def test_enroll_v2_renderiza(big):
  env = dict(os.environ, OFFSCREEN="1", SCALE="1.0")
  env.pop("BIG", None)
  if big:
    env["BIG"] = "1"
  r = subprocess.run([sys.executable, "-c", GUION], cwd=BASEDIR, env=env, capture_output=True, text=True, timeout=300)
  assert r.returncode == 0 and "RENDER_OK" in r.stdout, (r.stdout[-3000:] + r.stderr[-6000:])
