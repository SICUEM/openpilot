"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

Subpanel SIMULACION del panel ORBIT: obstaculos ESTATICOS de la sim MetaDrive del PC.

Escribe el escenario en OrbitSimObstaculos y enseña lo que la sim dice en OrbitSimEstado. Siempre visible (sin
SIMULATION=1): en un comma real no hay sim que lo lea y la fila de estado lo dice.

Dos vistas en el mismo subpanel:
  * LISTA: interruptor, estado de la sim, una fila por obstaculo y los presets.
  * EDITOR: un obstaculo (nuevo o existente) con controles +/- y GUARDAR.

Las filas de obstaculo se crean todas al construir (MAX_OBSTACULOS) y se ocultan las que
sobran: el Scroller no sabe quitar widgets, y crear filas en caliente dentro del render es
justo el tipo de cosa que acaba en una excepcion que mata el proceso ui.
"""
import time
from collections.abc import Callable

import pyray as rl

from openpilot.orbit import sim_obstaculos as so
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes
from openpilot.selfdrive.ui.widgets import orbit_sim as sim
from openpilot.selfdrive.ui.widgets.orbit_section import SectionHeaderSP
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import ListItemSP, toggle_item_sp, button_item_sp, dual_button_item_sp
from openpilot.system.ui.sunnypilot.widgets.option_control import OptionControlSP, LABEL_WIDTH
from openpilot.system.ui.widgets import Widget, DialogResult
from openpilot.system.ui.widgets.button import ButtonStyle
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog, alert_dialog
from openpilot.system.ui.widgets.list_view import ItemAction
from openpilot.system.ui.widgets.network import NavButton
from openpilot.system.ui.widgets.scroller_tici import Scroller

REFRESH_SECONDS = 1.0


def _avisar_fallo(etiqueta: str) -> None:
  gui_app.push_widget(alert_dialog(tr("Fallo interno en:") + f" {etiqueta}\n" +
                                   tr("La accion no se ha completado. Revisa el log de la UI.")))


def _a_salvo(etiqueta: str, avisar: bool = False):
  """Una excepcion en un callback o en el refresco mata el proceso `ui` (ver orbit_panel._a_salvo)."""
  return ajustes.a_salvo(etiqueta, _avisar_fallo if avisar else None)


def _ahora_ms() -> int:
  return time.time_ns() // 1_000_000


class ValorSP(OptionControlSP):
  """El control +/- de sunnypilot sin Param detras: el editor guarda todo junto al pulsar
  GUARDAR, no valor a valor. OptionControlSP lee y escribe su Param en __init__ y en
  set_value, asi que no se llama a su __init__ y se rellena lo que usa su _render."""

  def __init__(self, min_value: int, max_value: int, label_callback: Callable[[int], str],
               step: int = 1, label_width: int = LABEL_WIDTH):
    ItemAction.__init__(self, enabled=True)
    self.param_key = None
    self.min_value, self.max_value = min_value, max_value
    self.value_change_step = step
    self._minus_enabled = self._plus_enabled = True
    self.on_value_changed = None
    self.value_map = None
    self.label_width = label_width
    self.use_float_scaling = False
    self.label_callback = label_callback
    self.current_value = min_value
    self._font = gui_app.font(FontWeight.MEDIUM)
    self.minus_btn_rect = rl.Rectangle(0, 0, 0, 0)
    self.plus_btn_rect = rl.Rectangle(0, 0, 0, 0)

  def set_value(self, value: int):
    if self.min_value <= value <= self.max_value:
      self.current_value = value


class SimulacionLayout(Widget):
  def __init__(self, back_btn_callback: Callable):
    super().__init__()
    self._back_to_main = back_btn_callback
    self._back_button = NavButton(tr("Back"))
    self._back_button.set_click_callback(self._on_back)

    # Cacheados en _refrescar (1 Hz): los lambdas de las filas se evaluan en cada frame.
    self._esc = so.escenario_vacio()
    self._estado = None
    self._ahora = 0
    self._ultimo_refresco = 0.0

    self._editando: int | None = None      # indice del obstaculo; None = nuevo
    self._en_editor = False

    self._lista = Scroller(self._items_lista(), line_separator=False, spacing=0)
    self._editor = Scroller(self._items_editor(), line_separator=False, spacing=0)

  # ------------------------------------------------------------------------- lista
  def _items_lista(self):
    self._activo_fila = toggle_item_sp(
      title=lambda: tr("Obstáculos al cargar el mapa"),
      description=lambda: tr("Coloca los obstáculos de la lista cada vez que la simulación carga " +
                             "o reinicia el mapa. Los cambios se aplican en un segundo."),
      initial_state=False,
      callback=self._on_activo,
    )
    self._estado_fila = ListItemSP(
      title=lambda: tr("Estado de la simulación"),
      description=lambda: sim.texto_estado(self._estado, self._esc, self._ahora),
      description_visible=True,
    )
    self._nuevo_fila = button_item_sp(
      title=lambda: tr("Añadir obstáculo"),
      button_text=lambda: tr("AÑADIR"),
      description=lambda: tr("Cono, barrera, triángulo o un coche parado, a la distancia y en el carril que elijas."),
      callback=lambda: self._abrir_editor(None),
      enabled=lambda: len(self._esc["obstaculos"]) < so.MAX_OBSTACULOS,
      # el estilo automatico va por palabras clave en ingles y "AÑADIR" saldria plano
      button_style=ButtonStyle.PRIMARY,
    )

    self._filas = []
    for i in range(so.MAX_OBSTACULOS):
      fila = button_item_sp(
        title=lambda i=i: self._titulo_fila(i),
        button_text=lambda: tr("EDITAR"),
        description=lambda i=i: sim.motivo_omitido(self._estado, self._esc, i, self._ahora),
        callback=lambda i=i: self._abrir_editor(i),
      )
      fila.set_visible(lambda i=i: i < len(self._esc["obstaculos"]))
      self._filas.append(fila)

    presets = [
      button_item_sp(
        title=lambda p=p: tr(so.PRESETS[p]["nombre"]),
        button_text=lambda p=p: tr("BORRAR") if p == "vacio" else tr("PONER"),
        callback=lambda p=p: self._confirmar_preset(p),
        button_style=ButtonStyle.DANGER if p == "vacio" else None,
      )
      for p in so.PRESETS
    ]

    return [
      SectionHeaderSP(tr("OBSTÁCULOS EN LA SIMULACIÓN"), seccion='ajustes'),
      self._activo_fila,
      self._estado_fila,
      SectionHeaderSP(tr("LISTA"), seccion='ajustes'),
      self._nuevo_fila,
      *self._filas,
      SectionHeaderSP(tr("ESCENARIOS RÁPIDOS"), seccion='ajustes'),
      *presets,
    ]

  def _titulo_fila(self, i: int) -> str:
    obst = self._esc["obstaculos"]
    return f"{i + 1}. {so.describir(obst[i])}" if i < len(obst) else ""

  # ------------------------------------------------------------------------ editor
  def _items_editor(self):
    self._ctl = {
      "tipo": ValorSP(0, len(so.ORDEN_TIPOS) - 1, sim.etiqueta_tipo),
      "dist": ValorSP(sim.DIST_MIN, sim.DIST_MAX, sim.etiqueta_distancia, step=sim.DIST_PASO),
      "carril": ValorSP(0, sim.CARRILES_EDITOR, sim.etiqueta_carril),
      "lateral": ValorSP(-sim.LATERAL_PASOS, sim.LATERAL_PASOS, sim.etiqueta_lateral),
      "giro": ValorSP(0, sim.GIRO_PASOS, sim.etiqueta_giro),
    }
    textos = {
      "tipo": (tr("Tipo"), tr("Los coches se quedan parados: ninguno se mueve.")),
      "dist": (tr("Distancia"), tr("Metros desde la salida, a lo largo de la ruta del coche.")),
      "carril": (tr("Carril"), tr("Mi carril = por el que sale el coche. Los números cuentan desde la derecha.")),
      "lateral": (tr("Desplazamiento lateral"), tr("Respecto al centro del carril.")),
      "giro": (tr("Giro"), tr("Sobre el sentido del carril. La barrera ya corta el carril con 0°.")),
    }
    filas = [ListItemSP(title=textos[k][0], description=textos[k][1], action_item=c, inline=False)
             for k, c in self._ctl.items()]
    self._botones_editor = dual_button_item_sp(
      left_text=lambda: tr("CANCELAR") if self._editando is None else tr("BORRAR"),
      right_text=lambda: tr("GUARDAR"),
      left_callback=self._on_izquierda_editor,
      right_callback=self._on_guardar,
    )
    # DualButtonAction pinta el derecho en rojo de peligro: aqui el peligroso es BORRAR.
    self._botones_editor.action_item.right_button.set_button_style(ButtonStyle.PRIMARY)
    return [
      SectionHeaderSP(tr("OBSTÁCULO"), seccion='ajustes'),
      *filas,
      self._botones_editor,
    ]

  @_a_salvo("abrir el editor de obstaculos", avisar=True)
  def _abrir_editor(self, indice: int | None):
    obst = self._esc["obstaculos"]
    if indice is not None and indice >= len(obst):
      return
    self._editando = indice
    self._botones_editor.action_item.left_button.set_button_style(
      ButtonStyle.NORMAL if indice is None else ButtonStyle.DANGER)
    for k, v in sim.valores_de(obst[indice] if indice is not None else None).items():
      self._ctl[k].current_value = v
    self._en_editor = True
    self._editor.show_event()

  def _cerrar_editor(self):
    self._en_editor = False
    self._editando = None
    self._ultimo_refresco = 0.0

  @_a_salvo("guardar el obstaculo", avisar=True)
  def _on_guardar(self):
    obst = sim.obstaculo_de({k: c.get_value() for k, c in self._ctl.items()})
    esc = sim.leer_escenario(ui_state.params)   # sin cache: es una escritura
    indice = self._editando if self._editando is not None and self._editando < len(esc["obstaculos"]) else None
    self._escribir(so.con_obstaculo(esc, obst, indice))
    self._cerrar_editor()

  @_a_salvo("borrar el obstaculo", avisar=True)
  def _on_izquierda_editor(self):
    if self._editando is not None:
      esc = sim.leer_escenario(ui_state.params)
      if self._editando < len(esc["obstaculos"]):
        self._escribir(so.sin_obstaculo(esc, self._editando))
    self._cerrar_editor()

  # ------------------------------------------------------------------------ acciones
  @_a_salvo("activar obstaculos", avisar=True)
  def _on_activo(self, activo: bool):
    self._escribir(so.con_activo(sim.leer_escenario(ui_state.params), activo))

  def _confirmar_preset(self, nombre: str):
    def on_result(result: DialogResult):
      if result == DialogResult.CONFIRM:
        self._aplicar_preset(nombre)

    if not self._esc["obstaculos"]:
      self._aplicar_preset(nombre)
      return
    msg = tr("Se sustituye la lista actual") + f" ({len(self._esc['obstaculos'])}) " + \
      tr("por:") + f" {tr(so.PRESETS[nombre]['nombre'])}."
    gui_app.push_widget(ConfirmDialog(msg, tr("SÍ, sustituir"), tr("Cancelar"), callback=on_result))

  @_a_salvo("escenario rapido", avisar=True)
  def _aplicar_preset(self, nombre: str):
    self._escribir(so.con_preset(sim.leer_escenario(ui_state.params), nombre))

  def _escribir(self, esc: dict):
    fallos = sim.guardar(ui_state.params, esc)
    if fallos:
      gui_app.push_widget(alert_dialog(tr("No se pudo guardar el escenario:") + "\n" + "\n".join(fallos)))
    self._ultimo_refresco = 0.0

  def _on_back(self):
    if self._en_editor:
      self._cerrar_editor()
    else:
      self._back_to_main()

  # ------------------------------------------------------------------------ estado vivo
  @_a_salvo("refresco de la simulacion")
  def _refrescar(self):
    self._ultimo_refresco = time.monotonic()
    params = ui_state.params
    self._esc = sim.leer_escenario(params)
    self._estado = sim.leer_estado(params)
    self._ahora = _ahora_ms()
    self._activo_fila.action_item.toggle.set_state(self._esc["activo"])
    # ListItem.show_event esconde las descripciones (se abren al tocar la fila). El estado y
    # el motivo de un obstaculo sin colocar tienen que verse sin tocar nada.
    self._estado_fila.show_description(True)
    for i, fila in enumerate(self._filas):
      fila.show_description(bool(sim.motivo_omitido(self._estado, self._esc, i, self._ahora)))

  def _update_state(self):
    super()._update_state()
    if time.monotonic() - self._ultimo_refresco >= REFRESH_SECONDS:
      self._refrescar()

  # ---------------------------------------------------------------------- lifecycle
  def _render(self, rect):
    self._back_button.set_position(self._rect.x, self._rect.y + 20)
    self._back_button.render()
    content_rect = rl.Rectangle(
      rect.x,
      rect.y + self._back_button.rect.height + 40,
      rect.width,
      rect.height - self._back_button.rect.height - 40,
    )
    (self._editor if self._en_editor else self._lista).render(content_rect)

  def show_event(self):
    self._en_editor = False
    self._editando = None
    self._lista.show_event()
    self._refrescar()
