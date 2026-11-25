"""Humo de render del aviso de peticion remota de modo de volante, en la mici y en la grande.

Cada UI en su proceso: `BIG` se lee al importar application.py y gui_app es un singleton
con una ventana. Comprueba la paridad con el selector local (mismo texto, mismo boton o
deslizador, test max en rojo, par directo en dos pasos), que enganchado no se puede
aceptar, que aceptar aplica, rechazar (boton o gesto atras) y caducar cierran, y guarda
capturas en ORBIT_CAPTURA si esta definida.
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

  BIG = gui_app.big_ui()
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
    assert len(lineas) * tam * aviso_mod.INTERLINEA <= clave[2] and tam >= aviso_mod._TAM[2], (tam, len(lineas))
    fuente = gui_app.font()
    assert all(measure_text_cached(fuente, l, tam).x <= clave[1] + 1 for l in lineas)
    assert aviso._aceptar._label._text == confirmar
    cab = measure_text_cached(gui_app.font(aviso_mod.FontWeight.BOLD), peticion_mod.texto(aviso._pet), aviso.tam_titulo).x
    assert cab <= clave[1], (cab, clave[1])
    ancho_txt = measure_text_cached(gui_app.font(aviso_mod.FontWeight.MEDIUM), confirmar, aviso_mod._TAM[4]).x
    assert ancho_txt + 40 <= aviso._aceptar.rect.width, (confirmar, ancho_txt, aviso._aceptar.rect.width)
    assert aviso._aceptar.rect.height >= 100

  def comprueba_pagina(titulo, esperado, rojo):
    # mici: la PaginaConfirmacion del selector local con el mismo texto, el deslizador y la caducidad.
    from openpilot.selfdrive.ui.mici.widgets.dialog import BigConfirmationCircleButton
    pag = aviso._pagina
    assert pila[-1] is pag, pila
    items = pag._scroller._items
    assert items[0]._label.text == titulo, items[0]._label.text
    textos = [it.value for it in items[1:] if not isinstance(it, BigConfirmationCircleButton)][:-1]
    from openpilot.selfdrive.ui.sunnypilot.mici.widgets import orbit_widgets
    assert textos == orbit_widgets.trozos_mici(esperado), textos
    circulo = [it for it in items if isinstance(it, BigConfirmationCircleButton)]
    assert len(circulo) == 1 and circulo[0]._red == rojo
    assert items[-1].value.startswith("caduca en 0:"), items[-1].value
    return pag, circulo[0]

  def slide(pag):
    # Lo que hace el deslizador al confirmar: cierra la pagina y luego corre el callback.
    pag.dismiss(aviso._on_aceptar)
    frames(120)

  def desliza_abajo(pag):
    pag.atras = True
    gui_app.pop_widget(pila.index(pag))
    frames()

  frames(3)
  assert pila[-1] is not aviso

  texto2, confirmar2 = aj.confirmacion_modo(2)
  texto3, confirmar3 = aj.confirmacion_modo(3)
  if BIG:
    pide("tm", 2)
    frames()
    assert pila[-1] is aviso and aviso._aceptar.enabled
    comprueba_confirmacion(texto2, confirmar2)
    assert aviso._aceptar._button_style == ButtonStyle.DANGER
    captura()

    # Par directo: dos pasos como en local; el primero no aplica nada.
    pide("tq", 3, "torque")
    frames()
    comprueba_confirmacion(texto3, confirmar3)
    assert aviso._aceptar._button_style == ButtonStyle.ACTION
    captura("_torque_1")
    aviso._on_aceptar()
    frames()
    assert pila[-1] is aviso and p.get("SteerTorqueMode", return_default=True) == 0
    torque, confirmar_t = aj.texto_esquive_torque(aviso_mod.CANCELAR)
    comprueba_confirmacion(torque, confirmar_t)
    captura("_torque_2")
    aviso._on_rechazar()
    frames()
    assert pila[-1] is not aviso and json.loads(p.get("OrbitCmdResult"))["phase"] == "rejected"
    assert p.get("SteerTorqueMode", return_default=True) == 0
    p.remove("OrbitCmdResult")

    pide("a", 3, "curvature")
    frames()
    assert pila[-1] is aviso and aviso._aceptar.enabled
    comprueba_confirmacion(texto3, confirmar3)

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
  else:
    base = pila[0]
    pide("tm", 2)
    frames()
    pag, _ = comprueba_pagina("la app pide test max", texto2, True)
    captura()
    # Otro la saca de la pila (onroad, timeout): vuelve sin rechazar.
    gui_app.pop_widgets_to(base, instant=True)
    frames()
    assert pila[-1] is pag and p.get("OrbitSteerModeRequest")
    desliza_abajo(pag)
    assert aviso._pagina is None and pila[-1] is base
    assert json.loads(p.get("OrbitCmdResult"))["phase"] == "rejected"
    p.remove("OrbitCmdResult")

    # Par directo: dos paginas con deslizador, como en local; la primera no aplica nada.
    pide("tq", 3, "torque")
    frames()
    pag, _ = comprueba_pagina("la app pide comma + jetson", texto3, False)
    captura("_torque_1")
    slide(pag)
    torque, _ = aj.texto_esquive_torque(aviso_mod.CANCELAR_MICI)
    pag2, _ = comprueba_pagina("par directo", torque, False)
    assert p.get("SteerTorqueMode", return_default=True) == 0
    captura("_torque_2")

    # Enganchado: el deslizador no se puede usar y la ultima tarjeta lo dice.
    clase = type(ui_state)
    original = clase.engaged
    clase.engaged = property(lambda s: True)
    frames()
    circulo = [it for it in pag2._scroller._items if hasattr(it, "_red")][0]
    assert not circulo.enabled and pag2._scroller._items[-1].value == "desengancha para aceptar"
    clase.engaged = original
    frames()
    assert circulo.enabled

    slide(pag2)
    assert aviso._pagina is None and pila[-1] is base
    assert p.get("SteerTorqueMode") == 3 and p.get("JetsonObstacleApplyTarget") == "torque"
    assert json.loads(p.get("OrbitCmdResult"))["phase"] == "applied"
    p.remove("OrbitCmdResult")

    # Caduca con la pagina en pantalla: se va sola.
    pide("c", 1)
    frames()
    comprueba_pagina("la app pide jetson", aj.confirmacion_modo(1)[0], False)
    p.put("OrbitSteerModeRequest", json.dumps({"v": 1, "id": "c", "mode": 1, "apply_target": None,
                                              "deadline_mono": ahora_mono() - 1}), True)
    frames()
    assert aviso._pagina is None and pila[-1] is base
    assert json.loads(p.get("OrbitCmdResult"))["phase"] == "expired"
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
