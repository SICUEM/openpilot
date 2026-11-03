"""Humo de render del aviso de peticion remota de modo de volante, en la mici y en la grande.

Cada UI en su proceso: `BIG` se lee al importar application.py y gui_app es un singleton
con una ventana. Pinta el aviso, comprueba que con openpilot enganchado Aceptar queda
deshabilitado y dice "Desengancha para aceptar", que Aceptar aplica el modo y quita el
aviso, y guarda una captura en ORBIT_CAPTURA si esta definida.
"""
import os
import subprocess
import sys

import pytest

from openpilot.common.basedir import BASEDIR

CAPTURAS = "/tmp/claude-1000/-home-drago-Desktop-openpilot/3d8ad441-1669-4539-ba85-2c5318c293fa/scratchpad"

GUION = r'''
import json
import os
import pyray as rl
rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)

from openpilot.common.params import Params
from openpilot.common.prefix import OpenpilotPrefix
from openpilot.orbit.command_spec import ahora_mono
from openpilot.system.ui.lib.application import gui_app

with OpenpilotPrefix():
  p = Params()
  from openpilot.selfdrive.ui.ui_state import ui_state
  from openpilot.selfdrive.ui.widgets import orbit_aviso_peticion_modo as aviso_mod
  from openpilot.system.ui.widgets import Widget

  gui_app.init_window("test peticion modo")

  class _Base(Widget):
    def _render(self, rect):
      rl.draw_rectangle_rec(rect, rl.DARKGRAY)

  gui_app.push_widget(_Base())
  aviso = aviso_mod.instalar()
  aviso_mod.REFRESCO_S = 0.0
  ui_state.update_params()
  rt = rl.load_render_texture(gui_app.width, gui_app.height)
  pila = gui_app._nav_stack

  def frames(n=10):
    for _ in range(n):
      ui_state.update()
      for tick in gui_app._nav_stack_ticks:
        tick()
      rl.begin_drawing()
      rl.begin_texture_mode(rt)
      rl.clear_background(rl.BLACK)
      for w in pila[-gui_app._nav_stack_widgets_to_render:]:
        w.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
      rl.end_texture_mode()
      rl.end_drawing()

  def pide(cid, modo, objetivo=None):
    p.put("OrbitSteerModeRequest", json.dumps({"v": 1, "id": cid, "mode": modo, "apply_target": objetivo,
                                              "deadline_mono": ahora_mono() + 30}), True)

  from openpilot.selfdrive.ui.widgets import orbit_ajustes as aj
  from openpilot.selfdrive.ui.widgets import orbit_peticion_modo as peticion_mod
  from openpilot.system.ui.lib.text_measure import measure_text_cached
  from openpilot.system.ui.widgets.button import ButtonStyle

  def captura(sufijo=""):
    salida = os.environ.get("ORBIT_CAPTURA")
    if salida:
      img = rl.load_image_from_texture(rt.texture)
      rl.image_flip_vertical(img)
      rl.export_image(img, salida.replace(".png", f"{sufijo}.png"))
      rl.unload_image(img)

  def comprueba_confirmacion(esperado, confirmar):
    # El texto entero del selector local, sin cortar, dentro de su caja, y el boton con su texto.
    clave, tam, lineas = aviso._cuerpo
    assert " ".join(" ".join(lineas).split()) == " ".join(esperado.split()), lineas
    assert len(lineas) * tam * aviso_mod.INTERLINEA <= clave[2] and tam >= aviso._tam[2], (tam, len(lineas))
    fuente = gui_app.font()
    assert all(measure_text_cached(fuente, l, tam).x <= clave[1] + 1 for l in lineas)
    assert aviso._aceptar._label._text == confirmar
    cab = measure_text_cached(gui_app.font(aviso_mod.FontWeight.BOLD), peticion_mod.texto(aviso._pet), aviso.tam_titulo).x
    assert cab <= clave[1], (cab, clave[1])
    ancho_txt = measure_text_cached(gui_app.font(aviso_mod.FontWeight.MEDIUM), confirmar, aviso._tam[4]).x
    assert ancho_txt + 40 <= aviso._aceptar.rect.width, (confirmar, ancho_txt, aviso._aceptar.rect.width)

  frames(3)
  assert pila[-1] is not aviso

  pide("tm", 2)
  frames()
  assert pila[-1] is aviso and aviso._aceptar.enabled
  texto2, confirmar2 = aj.confirmacion_modo(2)
  comprueba_confirmacion(texto2, confirmar2)
  assert aviso._aceptar._button_style == ButtonStyle.DANGER
  captura()

  pide("tq", 3, "torque")
  frames()
  texto3, _ = aj.confirmacion_modo(3)
  torque, confirmar3 = aj.texto_esquive_torque(aviso_mod.CANCELAR)
  comprueba_confirmacion(texto3 + "\n\n" + torque, confirmar3)
  assert aviso._aceptar._button_style == ButtonStyle.ACTION
  captura("_torque")

  pide("a", 3, "curvature")
  frames()
  assert pila[-1] is aviso and aviso._aceptar.enabled
  comprueba_confirmacion(*aj.confirmacion_modo(3))

  # Enganchado: Aceptar deshabilitado y no aplica nada.
  clase = type(ui_state)
  original = clase.engaged
  clase.engaged = property(lambda s: True)
  frames()
  assert not aviso._aceptar.enabled
  aviso._on_aceptar()
  frames()
  assert pila[-1] is aviso and p.get("SteerTorqueMode", return_default=True) == 0
  clase.engaged = original

  aviso._on_aceptar()
  frames()
  assert pila[-1] is not aviso
  assert p.get("SteerTorqueMode") == 3 and p.get("JetsonObstacleApplyTarget") == "curvature"
  assert json.loads(p.get("OrbitCmdResult"))["phase"] == "applied"
  p.remove("OrbitCmdResult")

  pide("b", 1)
  frames()
  assert pila[-1] is aviso
  aviso._on_rechazar()
  frames()
  assert pila[-1] is not aviso and json.loads(p.get("OrbitCmdResult"))["phase"] == "rejected"
  assert p.get("SteerTorqueMode") == 3
print("RENDER_OK")
'''


@pytest.mark.parametrize("big", [False, True], ids=["mici", "big"])
def test_aviso_peticion_modo_renderiza(big):
  env = dict(os.environ, OFFSCREEN="1", SCALE="1.0")
  env.pop("BIG", None)
  if big:
    env["BIG"] = "1"
  if os.path.isdir(CAPTURAS):
    env["ORBIT_CAPTURA"] = os.path.join(CAPTURAS, f"peticion_modo_{'big' if big else 'mici'}.png")
  r = subprocess.run([sys.executable, "-c", GUION], cwd=BASEDIR, env=env, capture_output=True, text=True, timeout=300)
  assert r.returncode == 0 and "RENDER_OK" in r.stdout, (r.stdout[-3000:] + r.stderr[-6000:])
