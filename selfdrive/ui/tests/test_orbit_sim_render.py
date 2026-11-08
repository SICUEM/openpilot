"""Humo de render del subpanel SIMULACION del panel ORBIT (obstaculos de la sim MetaDrive).

En su propio proceso (gui_app es un singleton con una ventana). Abre el subpanel desde el
panel ORBIT, comprueba que hay una fila por obstaculo, edita, anade, borra, aplica un
preset y desactiva, mirando lo que queda en OrbitSimObstaculos. Si ORBIT_CAPTURAS apunta
a una carpeta, guarda alli capturas de la lista y del editor.
"""
import os
import subprocess
import sys

from openpilot.common.basedir import BASEDIR

GUION = r'''
import os
import time
import pyray as rl
rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)

from openpilot.common.params import Params
from openpilot.common.prefix import OpenpilotPrefix
from openpilot.system.ui.lib.application import gui_app

with OpenpilotPrefix():
  p = Params()
  from openpilot.orbit import sim_obstaculos as so
  from openpilot.selfdrive.ui.ui_state import ui_state
  from openpilot.selfdrive.ui.sunnypilot.layouts.settings.orbit_panel import OrbitLayout, PanelType

  gui_app.init_window("test simulacion")
  esc = {"v": 1, "rev": 5, "activo": True, "obstaculos": [
    {"tipo": "cono", "s": 30.0, "carril": "ego", "lateral": 0.0, "giro": 0.0},
    {"tipo": "coche", "s": 900.0, "carril": 1, "lateral": -0.5, "giro": 0.0},
  ]}
  p.put(so.PARAM_ESCENARIO, esc, True)
  p.put(so.PARAM_ESTADO, {"v": 1, "ts_ms": time.time_ns() // 1_000_000, "rev": 5, "activo": True,
                          "mapa": "highway", "ruta_m": 307.2, "carriles": 3, "carril_ego": 3, "colocados": 1,
                          "omitidos": [{"i": 1, "motivo": "fuera de la ruta"}], "descartados": [],
                          "faltan_modelos": []}, True)

  panel = OrbitLayout()
  gui_app.push_widget(panel)
  ui_state.update_params()
  rt = rl.load_render_texture(gui_app.width, gui_app.height)

  def frames(n=6):
    for _ in range(n):
      ui_state.update()
      rl.begin_drawing()
      rl.begin_texture_mode(rt)
      rl.clear_background(rl.BLACK)
      for w in gui_app._nav_stack[-gui_app._nav_stack_widgets_to_render:]:
        w.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
      rl.end_texture_mode()
      rl.end_drawing()

  def captura(nombre):
    carpeta = os.environ.get("ORBIT_CAPTURAS")
    if carpeta:
      img = rl.load_image_from_texture(rt.texture)
      rl.image_flip_vertical(img)
      rl.export_image(img, os.path.join(carpeta, f"orbit_sim_{nombre}.png"))
      rl.unload_image(img)

  def obstaculos():
    return so.normalizar(p.get(so.PARAM_ESCENARIO))[0]["obstaculos"]

  panel.show_event()
  frames(3)
  assert panel._simulacion_button.is_visible        # siempre visible, sin SIMULATION=1
  panel._set_current_panel(PanelType.SIMULACION)
  sim = panel._simulacion_layout
  frames()
  assert [f.is_visible for f in sim._filas[:3]] == [True, True, False]
  assert sim._activo_fila.action_item.toggle.get_state() is True
  assert "No colocado: fuera de la ruta" in sim._filas[1].description
  assert sim._estado_fila.description_visible and sim._filas[1].description_visible
  assert not sim._filas[0].description_visible        # colocado: sin motivo que enseñar
  captura("lista")
  sim._lista.scroll_panel.set_offset(-700)
  frames()
  captura("lista_abajo")

  # editar el 2: camion a 120 m en mi carril
  sim._abrir_editor(1)
  frames()
  assert sim._en_editor and sim._ctl["tipo"].get_value() == so.ORDEN_TIPOS.index("coche")
  sim._ctl["tipo"].set_value(so.ORDEN_TIPOS.index("camion"))
  sim._ctl["dist"].set_value(120)
  sim._ctl["carril"].set_value(0)
  frames()
  captura("editor")
  sim._editor.scroll_panel.set_offset(-900)
  frames()
  captura("editor_abajo")
  sim._on_guardar()
  frames()
  assert not sim._en_editor
  assert obstaculos()[1] == {"tipo": "camion", "s": 120.0, "carril": "ego", "lateral": -0.5, "giro": 0.0}

  # anadir uno nuevo con los valores por defecto
  sim._abrir_editor(None)
  sim._on_guardar()
  frames()
  assert len(obstaculos()) == 3 and sim._filas[2].is_visible

  # borrar el primero
  sim._abrir_editor(0)
  sim._on_izquierda_editor()
  frames()
  assert [o["tipo"] for o in obstaculos()] == ["camion", "cono"] and not sim._filas[2].is_visible

  # desactivar y preset sobre lista vacia (sin dialogo)
  sim._on_activo(False)
  assert so.normalizar(p.get(so.PARAM_ESCENARIO))[0]["activo"] is False
  p.put(so.PARAM_ESCENARIO, so.escenario_vacio(), True)
  sim._ultimo_refresco = 0.0
  frames()
  sim._confirmar_preset("slalom")
  esc_final = so.normalizar(p.get(so.PARAM_ESCENARIO))[0]
  assert esc_final["activo"] is True and len(esc_final["obstaculos"]) == 5

  # sin estado de la sim: lo dice
  p.remove(so.PARAM_ESTADO)
  sim._ultimo_refresco = 0.0
  frames()
  assert sim._estado_fila.description.startswith("Simulación no conectada")
  captura("lista_sin_sim")

  sim._on_back()
  frames()
  assert panel._current_panel == PanelType.MAIN
print("RENDER_OK")
'''


def test_subpanel_simulacion_renderiza():
  env = dict(os.environ, OFFSCREEN="1", SCALE="1.0", BIG="1")
  r = subprocess.run([sys.executable, "-c", GUION], cwd=BASEDIR, env=env, capture_output=True, text=True, timeout=300)
  assert r.returncode == 0 and "RENDER_OK" in r.stdout, (r.stdout[-3000:] + r.stderr[-6000:])
