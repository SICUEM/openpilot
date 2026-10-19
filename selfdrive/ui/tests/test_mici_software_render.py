"""Humo de render de la pantalla "software" del comma 4 (mici) y su selector de rama.

Proceso aparte (gui_app es singleton con ventana). Con GitBranch=orbit-master y tres ramas
disponibles: pinta la pantalla y la pagina de ramas sin excepciones y comprueba que elegir
una rama escribe UpdaterTargetBranch.
"""
import os
import subprocess
import sys

from openpilot.common.basedir import BASEDIR

SCRATCH = "/tmp/claude-1000/-home-drago-Desktop-openpilot/3d8ad441-1669-4539-ba85-2c5318c293fa/scratchpad"

GUION = r'''
import os
import pyray as rl
rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)

from openpilot.common.params import Params
from openpilot.common.prefix import OpenpilotPrefix
from openpilot.system.ui.lib.application import gui_app

with OpenpilotPrefix():
  p = Params()
  p.put("GitBranch", "orbit-master")
  p.put("UpdaterAvailableBranches", "orbit-master,release-mici,staging")

  from openpilot.selfdrive.ui.ui_state import ui_state
  gui_app.init_window("test software mici")
  assert (gui_app.width, gui_app.height) == (536, 240)

  from openpilot.selfdrive.ui.mici.layouts.settings import software as sw
  pantalla = sw.SoftwareLayoutMici()
  ui_state.update_params()
  rt = rl.load_render_texture(gui_app.width, gui_app.height)
  pila = gui_app._nav_stack

  def frames(n, captura=None):
    for _ in range(n):
      ui_state.update()
      rl.begin_drawing()
      rl.begin_texture_mode(rt)
      rl.clear_background(rl.BLACK)
      for w in pila[-gui_app._nav_stack_widgets_to_render:]:
        w.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
      rl.end_texture_mode()
      rl.end_drawing()
    if captura:
      img = rl.load_image_from_texture(rt.texture)
      rl.image_flip_vertical(img)
      rl.export_image(img, captura)

  gui_app.push_widget(pantalla)
  frames(120, os.environ["CAPTURA"])

  boton = next(i for i in pantalla._scroller._items if isinstance(i, sw.TargetBranchButton))
  boton._click_callback()
  frames(120)
  assert isinstance(pila[-1], sw.BranchSelectPage), type(pila[-1]).__name__
  assert [b.text for b in pila[-1]._scroller._items] == ["orbit-master", "release-mici", "staging"]

  # Callback de seleccion: escribe la rama (el aviso al updater es un pkill, inocuo sin updater).
  boton._on_select("release-mici")
  assert p.get("UpdaterTargetBranch") == "release-mici"
  frames(5)

  print("RENDER_OK", flush=True)
  rl.close_window()
  os._exit(0)
'''


def test_software_mici_renderiza():
  env = dict(os.environ, OFFSCREEN="1", SCALE="1.0", CAPTURA=os.path.join(SCRATCH, "mici_software.png"))
  env.pop("BIG", None)
  r = subprocess.run([sys.executable, "-c", GUION], cwd=BASEDIR, env=env, capture_output=True, text=True, timeout=300)
  assert r.returncode == 0 and "RENDER_OK" in r.stdout, (r.stdout[-3000:] + r.stderr[-6000:])
