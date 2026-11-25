"""
Selector de FUENTE DE TORQUE DEL VOLANTE (param SteerTorqueMode), con confirmacion.

Vive en el panel ORBIT principal y no en un subpanel a proposito: la seccion 9 del
diseno lo deja en el comma porque necesita ojos en el coche, y enterrarlo tras dos
navegaciones es lo contrario de eso.

DOS AUTORIZACIONES DISTINTAS, Y NO SE PUEDEN MEZCLAR
---------------------------------------------------
El catalogo clasifica `torque_mode` 1 y 2 como modo BANCO, y controlsd exige autorizacion
antes de dejar que el override de torque toque el volante. Pero "armar el banco" y "elegir
el modo delante del coche" NO son lo mismo:

  OrbitBenchArmed     habilita los verbos FISICOS POR MQTT (torque_mode, steering_pulse,
                      physical_control) a cualquiera que publique en el broker.
  OrbitSteerModeLocal dice que alguien ha elegido el modo EN ESTA PANTALLA, estando
                      delante. No habilita nada remoto.

Una version anterior de este fichero armaba el BANCO para devolverle la funcion al
selector, y renovaba ese armado indefinidamente mientras el modo siguiera elegido. La
consecuencia, que no se declaro: con el conductor en modo JETSON, cualquiera que conociera
el dongle_id podia mandar `torque_mode {mode: 2}` y poner el volante al tope. El "motivo en
RAM" no protegia de nada, porque solo gobernaba el acto de armar y no el gate del router,
que solo mira el param.

Ahora la seleccion presencial escribe su propio flag. El camino MQTT sigue encontrandose el
banco desarmado y sigue mandando el modelo Comma.

El vigilante (`BenchGuard`, selfdrive/ui/widgets/orbit_mando.py) retira el flag al volver a
COMMA, al pasar a offroad, y -- en TEST MAX -- al superar los 5 km/h, devolviendo ademas el
selector a COMMA.
"""
import time

import pyray as rl

from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.widgets import orbit_mando as mando
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes
# Las constantes del selector viven en orbit_ajustes (las comparte la UI del comma 4); se
# reexportan aqui para quien las importe desde este modulo (advanced_settings).
from openpilot.selfdrive.ui.widgets.orbit_ajustes import (  # noqa: F401
  MODE_BUTTONS, INDEX_TO_MODE, MODE_TO_INDEX, MODE_NAMES, MODES_REQUIRING_BENCH, TORQUE_STALE_SECONDS,
)
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.lib.styles import style
from openpilot.system.ui.sunnypilot.widgets.list_view import MultipleButtonActionSP, multiple_button_item_sp, button_item_sp
from openpilot.system.ui.widgets import DialogResult
from openpilot.selfdrive.ui import orbit_theme as t
from openpilot.system.ui.widgets.button import Button, ButtonStyle

POLL_INTERVAL_S = 0.5

# Selector de tres (Comma, Comma + Jetson, Jetson); TEST MAX va en una fila aparte, con tinta
# de peligro (guia visual 5.4). MODE_BUTTONS (4 botones) lo siguen usando el comma 4 y el aviso
# de peticion de modo: aqui no se toca.
BOTONES = ["Comma", "Comma + Jetson", "Jetson"]
INDICE_A_MODO = {0: 0, 1: 3, 2: 1}
MODO_A_INDICE = {v: k for k, v in INDICE_A_MODO.items()}
MODO_TEST_MAX = 2


class _BotonTintaPeligro(Button):
  """Boton plano (sin relleno) con la accion en tinta PELIGRO: un solo relleno por pantalla.

  Button._update_state repone el color de texto del estilo en cada frame, asi que la tinta se
  impone despues de ella. Deshabilitado se queda con el gris de siempre."""

  def _update_state(self):
    super()._update_state()
    if self.enabled:
      self._label.set_text_color(t.PELIGRO)


class SegmentadoMarcado(MultipleButtonActionSP):
  """Marca la opcion activa del segmentado sin verde ni rojo: borde de tinta y fondo mas claro.

  El resaltado de upstream es un escalon de azul marino que a 60 cm no se distingue. Se pinta
  encima (sin tocar system/ui): solo cuando hay una opcion marcada (Test max no marca ninguna)."""

  def _render(self, rect):
    super()._render(rect)
    if not self.enabled or not 0 <= self.selected_button < len(self.buttons):
      return
    x = self._anim_x if self._anim_x is not None else rect.x + self.selected_button * self.button_width
    seg = rl.Rectangle(x, rect.y + (rect.height - style.BUTTON_HEIGHT) / 2, self.button_width, style.BUTTON_HEIGHT)
    rl.draw_rectangle_rounded(seg, 0.2, 20, rl.Color(255, 255, 255, 36))
    rl.draw_rectangle_rounded_lines_ex(seg, 0.2, 20, 4, t.TEXTO1)


def read_mode() -> int:
  return mando.read_steer_mode()


class SteerModeRows:
  """Filas del selector de volante, para incrustar en un Scroller ajeno.

  El contenedor llama a `poll()` desde su `_render` (hilo de UI) para resincronizar el
  selector con el valor real del param: el modo tambien lo puede cambiar la app.
  """

  def __init__(self):
    self._last_poll = 0.0
    # Texto de estado cacheado. El lambda del titulo lo llama el render (y la medida de
    # texto) en CADA frame: recalcularlo ahi seria abrir Params 60 veces por segundo.
    self._status_cached = ""

    # El estado vivo va en el TITULO del selector y no en una fila aparte: son 188 px de
    # scroll menos y el dato queda pegado al control que lo produce.
    self._selector = multiple_button_item_sp(
      title=lambda: tr("Control del volante") + ": " + self._status_cached,
      description=lambda: tr("De dónde sale el par que se aplica al volante cuando el control " +
                             "lateral está activo. Elegir Jetson aquí es una autorización " +
                             "presencial: no arma el modo taller y dura hasta volver a Comma o pasar a offroad."),
      buttons=[tr(b) for b in BOTONES],
      button_width=320,
      selected_index=MODO_A_INDICE.get(read_mode(), 0),
      callback=self._on_mode_button,
    )
    self._selector.action_item.__class__ = SegmentadoMarcado   # misma disposicion: solo cambia el pintado
    self._test_max = button_item_sp(
      title=lambda: tr("Test max"),
      button_text=lambda: tr("Desactivar") if read_mode() == MODO_TEST_MAX else tr("Activar"),
      description=lambda: tr("Prueba de banco: el volante gira con toda su fuerza. Solo en circuito."),
      callback=self._on_test_max,
      button_style=ButtonStyle.LIST_ACTION,
    )
    # Mismo boton plano que "Abrir", pero con la accion en tinta PELIGRO (guia visual 5.4).
    self._test_max.action_item._button.__class__ = _BotonTintaPeligro

  @property
  def items(self) -> list:
    return [self._selector, self._test_max]

  def poll(self):
    now = time.monotonic()
    if now - self._last_poll < POLL_INTERVAL_S:
      return
    self._last_poll = now
    self.sync()

  def sync(self):
    """Resincroniza el boton marcado y el texto de estado con los Params reales."""
    # En Test max no hay botón marcado en el selector de tres: el estado va en el título.
    self._selector.action_item.selected_button = MODO_A_INDICE.get(read_mode(), -1)
    self._status_cached = self._status_text()

  # ------------------------------------------------------------------- estado
  def _status_text(self) -> str:
    """Estado REAL, no el boton pulsado (ver ajustes.texto_estado_volante)."""
    mode = read_mode()
    tgt = ui_state.params.get(ajustes.PARAM_APPLY_TARGET) if mode == 3 else None
    necesita = mode in MODES_REQUIRING_BENCH
    armado, restante = mando.bench_snapshot() if necesita else (False, 0.0)
    local = necesita and mando.steer_local_activo()
    return ajustes.texto_estado_volante(mode, tgt, armado, restante, local)

  # -------------------------------------------------------------------- accion
  def _on_mode_button(self, index: int):
    self._pedir_modo(INDICE_A_MODO.get(index, 0))

  def _on_test_max(self):
    # Activo: desactivar es volver a Comma, sin confirmar (es el camino seguro).
    self._pedir_modo(0 if read_mode() == MODO_TEST_MAX else MODO_TEST_MAX)

  def _pedir_modo(self, target_mode: int):
    current = read_mode()

    # COMMA+JETSON siempre vuelve a preguntar el sub-objetivo (igual que el Qt viejo),
    # asi que no se hace early-return con el.
    if target_mode == current and target_mode != 3:
      return

    if target_mode == 3 and current == 3:
      self._ask_obstacle_apply_target()
      return
    msg, confirm_text = ajustes.confirmacion_modo(target_mode)

    def on_result(result: DialogResult):
      # Siempre resincronizar con el estado real (cubre el cancelar).
      self.sync()
      if result != DialogResult.CONFIRM:
        return
      if target_mode == 3:
        self._ask_obstacle_apply_target()
      else:
        self._commit_mode(target_mode)

    estilo = ButtonStyle.DANGER if target_mode == MODO_TEST_MAX else ButtonStyle.ACTION
    gui_app.push_widget(ajustes.dialogo_orbit(msg, confirm_text, estilo, tr("Cancelar"), callback=on_result))

  def _ask_obstacle_apply_target(self):
    """Como debe esquivar la Jetson: 'curvature' (recomendado) o 'torque' (beta).

    ConfirmDialog solo ofrece dos botones, asi que es un flujo en dos pasos:
      paso 1: "esquive en CURVATURA?"  CONFIRM -> curvature ; CANCEL -> paso 2
      paso 2: "usar TORQUE (beta)?"    CONFIRM -> torque    ; CANCEL -> abortar
    """
    def commit_target(target: str):
      ajustes.fijar_objetivo_esquive(ui_state.params, target)
      self._commit_mode(3)

    def ask_torque():
      msg, confirm_text = ajustes.texto_esquive_torque()

      def on_torque(result: DialogResult):
        self.sync()
        if result == DialogResult.CONFIRM:
          commit_target("torque")

      gui_app.push_widget(ajustes.dialogo_orbit(msg, confirm_text, ButtonStyle.ACTION, tr("Cancelar"), callback=on_torque))

    msg, curvatura, otra = ajustes.texto_esquive_curvatura()

    def on_curvature(result: DialogResult):
      self.sync()
      if result == DialogResult.CONFIRM:
        commit_target("curvature")
      elif result == DialogResult.CANCEL:
        ask_torque()

    gui_app.push_widget(ajustes.dialogo_orbit(msg, curvatura, ButtonStyle.ACTION, otra, callback=on_curvature))

  def _commit_mode(self, mode: int):
    # Modo (INT, bloqueante) + autorizacion presencial + buzon MQTT: ver
    # ajustes.aplicar_modo_volante, que es lo que llama tambien el comma 4.
    ajustes.aplicar_modo_volante(ui_state.params, mode)
    self.sync()
