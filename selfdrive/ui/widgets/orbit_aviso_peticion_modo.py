"""
Aviso a pantalla completa de la peticion remota de modo de volante, para la UI grande
(3X) y la mici (comma 4). Solo pinta y enruta los toques: leer, aceptar, rechazar y
caducar viven en orbit_peticion_modo.

Es la MISMA confirmacion que da el selector local de cada pantalla: el texto de
`confirmacion_modo(mode)` y, con Comma + Jetson en par directo, un segundo paso con
`texto_esquive_torque()`, igual que en local. Test max con el boton (3X) o el deslizador
(mici) en rojo, como en local. Una peticion remota no puede pedir menos que elegir el
modo a mano.

- 3X: este widget se empuja encima de todo mientras haya peticion vigente y se quita al
  resolverse. No es un NavWidget a proposito: solo se cierra con Aceptar o Rechazar.
- mici: la gramatica de `PaginaConfirmacion` (tarjetas en horizontal y deslizador), la
  misma del selector local. Rechazar es el gesto atras: deslizar la pagina hacia abajo.

Se instala con un tick del nav stack (`instalar()`), asi que aparece este donde este el
conductor, onroad u offroad. Una instancia por proceso.
"""
import pyray as rl

from openpilot.orbit.command_spec import ahora_mono
from openpilot.selfdrive.ui import orbit_theme as t
from openpilot.selfdrive.ui.ui_state import device, ui_state
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes
from openpilot.selfdrive.ui.widgets import orbit_peticion_modo as peticion
from openpilot.selfdrive.ui.widgets.orbit_ajustes import a_salvo
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.lib.wrap_text import wrap_text
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.button import Button, ButtonStyle
from openpilot.system.ui.widgets.label import gui_label

REFRESCO_S = 0.25   # Params.get es leer disco: no en cada frame
INTERLINEA = 1.15
CANCELAR = "Pulsa Rechazar para no cambiar nada."
CANCELAR_MICI = "Desliza hacia abajo para no cambiar nada."   # el mismo que el selector local mici

# (titulo, cuerpo maximo, cuerpo minimo, pie, botones, margen) en la 3X
_TAM = (100, 48, 24, 48, 60, 50)
AIRE_TITULO, AIRE_CUERPO, AIRE_BOTONES = 20, 50, 40   # px de respiro: sobre el titulo, bajo el titulo y sobre los botones


def pasos(pet: dict) -> int:
  """Comma + Jetson en par directo pide dos confirmaciones, como en local."""
  return 2 if pet["mode"] == 3 and pet["apply_target"] == "torque" else 1


def textos_confirmacion(pet: dict, paso: int = 1, cancelar: str = CANCELAR) -> tuple[str, str]:
  """(texto de aviso, boton de confirmar) del paso: los mismos que el selector local."""
  if paso == 2:
    return ajustes.texto_esquive_torque(cancelar)
  return ajustes.confirmacion_modo(pet["mode"])


def texto_caducidad(pet: dict) -> str:
  s = max(0, int(pet["deadline_mono"] - ahora_mono()))
  return f"Caduca en {s // 60}:{s % 60:02d}"


class AvisoPeticionModo(Widget):
  def __init__(self):
    super().__init__()
    self._big = gui_app.big_ui()
    self.tam_titulo = 0   # tamano real de la cabecera en el ultimo frame (lo mira el test)
    self._pet: dict | None = None
    self._paso = 1
    self._ultimo_id = ""
    self._ultimo_refresco = float("-inf")
    self._pagina = None   # mici: la pagina de confirmacion en pantalla
    # Cuerpo ya partido en lineas: (clave, tam de letra, lineas). Se recalcula solo si cambia.
    self._cuerpo: tuple = ((), 0, [])
    boton = _TAM[4]
    self._aceptar = self._child(Button("Aceptar", self._on_aceptar, font_size=boton, button_style=ButtonStyle.ACTION))
    self._aceptar.set_enabled(lambda: not ui_state.engaged)
    self._rechazar = self._child(Button("Rechazar", self._on_rechazar, font_size=boton, button_style=ButtonStyle.NORMAL))

  def tick(self) -> None:
    ahora = rl.get_time()
    if ahora - self._ultimo_refresco >= REFRESCO_S:
      self._ultimo_refresco = ahora
      try:
        self._pet = peticion.tick(ui_state.params)
      except Exception:
        self._pet = None
    if self._pet is not None and self._pet["id"] != self._ultimo_id:
      # Peticion nueva: desde el primer paso y con la pantalla encendida para que alguien la vea.
      self._ultimo_id = self._pet["id"]
      self._paso = 1
      device._reset_interactive_timeout()
      if gui_app.sunnypilot_ui():
        ui_state.reset_onroad_sleep_timer()
    # En cada frame: si alguien hizo pop_widgets_to (onroad, timeout), vuelve arriba ya.
    if self._big:
      self._sincronizar_pila()
    else:
      self._sincronizar_mici()

  def _sincronizar_pila(self) -> None:
    en_pila = gui_app.widget_in_stack(self)
    if self._pet is not None and not en_pila:
      gui_app.push_widget(self)
    elif self._pet is None and en_pila:
      gui_app.pop_widget(gui_app._nav_stack.index(self))

  def _on_aceptar(self) -> None:
    if self._pet is not None and self._paso < pasos(self._pet):
      self._paso += 1   # solo cambia lo que se pregunta; aceptar sigue siendo el ultimo paso
      return
    a_salvo("aceptar la peticion de modo")(peticion.aceptar)(ui_state.params, ui_state.engaged)
    self._ultimo_refresco = float("-inf")

  def _on_rechazar(self) -> None:
    a_salvo("rechazar la peticion de modo")(peticion.rechazar)(ui_state.params)
    self._ultimo_refresco = float("-inf")

  # ---------------------------------------------------------------- mici
  def _quitar_pagina(self) -> None:
    pila = gui_app._nav_stack
    if self._pagina in pila:
      # Con ella sale lo que tenga encima (el deslizador de confirmar).
      for _ in range(len(pila) - pila.index(self._pagina)):
        gui_app.pop_widget()
    self._pagina = None

  def _sincronizar_mici(self) -> None:
    pet = self._pet
    if pet is None:
      self._quitar_pagina()
      return
    clave = (pet["id"], self._paso)
    pag = self._pagina
    if pag is not None and pag.clave != clave:
      self._quitar_pagina()
      pag = None
    if pag is None:
      self._pagina = pag = _crear_pagina(self, pet, self._paso)
      gui_app.push_widget(pag)
    elif not gui_app.widget_in_stack(pag):
      if pag.atras:
        self._pagina = None
        self._on_rechazar()   # la persona deslizo la pagina hacia abajo
        return
      # La quito otro (onroad, timeout) o fallo aceptar: vuelve arriba. Tras aceptar bien ya
      # no hay peticion: _on_aceptar fuerza el refresco y no se llega aqui.
      gui_app.push_widget(pag)
    pag.actualizar(pet)

  # ---------------------------------------------------------------- 3X
  def _partir(self, texto: str, ancho: float, alto: float) -> tuple[int, list[str]]:
    """El tamano mas grande al que el texto entero cabe en la caja, y sus lineas."""
    _, maximo, minimo, *_ = _TAM
    fuente = gui_app.font(FontWeight.NORMAL)
    for tam in range(maximo, minimo - 1, -1):
      lineas = wrap_text(fuente, texto, tam, int(ancho))
      if len(lineas) * tam * INTERLINEA <= alto:
        return tam, lineas
    return minimo, lineas

  def _render(self, rect: rl.Rectangle) -> None:
    rl.draw_rectangle_rec(rect, t.FONDO)
    if self._pet is None:
      return
    titulo, _, _, pie, boton, m = _TAM
    peligro = self._pet["mode"] == 2
    texto, confirmar = textos_confirmacion(self._pet, self._paso)
    self._aceptar.set_text(confirmar)
    self._aceptar.set_button_style(ButtonStyle.DANGER if peligro else ButtonStyle.ACTION)

    centro = rl.GuiTextAlignment.TEXT_ALIGN_CENTER
    x, w = rect.x + m, rect.width - 2 * m
    y = rect.y + m + AIRE_TITULO
    cabecera = peticion.texto(self._pet)
    negrita = gui_app.font(FontWeight.BOLD)
    while titulo > 8 and measure_text_cached(negrita, cabecera, titulo).x > w:
      titulo -= 2   # sin elidir: el modo se tiene que leer entero
    self.tam_titulo = titulo
    gui_label(rl.Rectangle(x, y, w, titulo * 1.25), cabecera, titulo,
              t.PELIGRO if peligro else t.AVISO, FontWeight.BOLD, alignment=centro, elide_right=False)
    y += titulo * 1.25 + AIRE_CUERPO

    alto_botones = boton * 2.2
    y_botones = rect.y + rect.height - m - alto_botones
    y_pie = y_botones - AIRE_BOTONES - pie * 1.3
    # El cuerpo se reparte en lo que queda entre el titulo y la caducidad, con aire arriba y abajo.
    alto_caja = y_pie - AIRE_CUERPO - y
    clave = (texto, w, alto_caja)
    if self._cuerpo[0] != clave:
      self._cuerpo = (clave, *self._partir(texto, w, alto_caja))
    _, tam, lineas = self._cuerpo
    fuente = gui_app.font(FontWeight.NORMAL)
    y += max(0.0, alto_caja - len(lineas) * tam * INTERLINEA) / 3
    for linea in lineas:
      rl.draw_text_ex(fuente, linea, rl.Vector2(x, y), tam, 0, t.TEXTO1)
      y += tam * INTERLINEA

    if ui_state.engaged:
      linea, color = "Desengancha para aceptar", t.PELIGRO
    else:
      linea, color = texto_caducidad(self._pet), t.TEXTO2
    gui_label(rl.Rectangle(x, y_pie, w, pie * 1.3), linea, pie, color, alignment=centro)

    ancho = (w - m) / 2
    self._rechazar.render(rl.Rectangle(x, y_botones, ancho, alto_botones))
    self._aceptar.render(rl.Rectangle(x + m + ancho, y_botones, ancho, alto_botones))


def _crear_pagina(aviso: AvisoPeticionModo, pet: dict, paso: int):
  """Pagina mici del paso: la PaginaConfirmacion del selector local con su mismo texto y
  deslizador, mas una tarjeta final con la caducidad.

  ponytail: una pagina por peticion y paso, como el selector local crea una por toque.
  Imports tardios: son widgets de la mici y la 3X no los carga.
  """
  from openpilot.selfdrive.ui.mici.widgets.dialog import BigConfirmationCircleButton
  from openpilot.selfdrive.ui.sunnypilot.mici.layouts.orbit_volante import DESLIZAR, DESLIZAR_TORQUE
  from openpilot.selfdrive.ui.sunnypilot.mici.widgets.orbit_widgets import PaginaConfirmacion, TarjetaTexto

  class PaginaPeticion(PaginaConfirmacion):
    def __init__(self):
      texto, _ = textos_confirmacion(pet, paso, CANCELAR_MICI)
      titulo = peticion.texto(pet).lower() if paso == 1 else "par directo"
      deslizar = DESLIZAR_TORQUE if paso == 2 else DESLIZAR[pet["mode"]]
      super().__init__(titulo, texto, deslizar, aviso._on_aceptar, rojo=pet["mode"] == 2)
      self.clave = (pet["id"], paso)
      self.atras = False   # la persona la deslizo hacia abajo (rechazar)
      items = self._scroller._items
      if pet["mode"] == 2:
        items[0]._sub_label.set_text_color(t.PELIGRO)
      for item in items:
        if isinstance(item, BigConfirmationCircleButton):
          item.set_enabled(lambda: not ui_state.engaged)
      self._caducidad = TarjetaTexto("", "desliza para aceptar")
      self._scroller.add_widget(self._caducidad)

    def actualizar(self, pet: dict) -> None:
      if ui_state.engaged:
        self._caducidad.set_value("desengancha para aceptar")
        self._caducidad._sub_label.set_text_color(t.PELIGRO)
      else:
        self._caducidad.set_value(texto_caducidad(pet).lower())
        self._caducidad._sub_label.set_text_color(t.TEXTO2)

    def _handle_mouse_event(self, mouse_event) -> None:
      # NavWidget no distingue el gesto atras de un dismiss() programatico (pop_widgets_to):
      # solo el gesto de la persona rechaza.
      antes = self._playing_dismiss_animation
      super()._handle_mouse_event(mouse_event)
      if self._playing_dismiss_animation and not antes:
        self.atras = True

    def show_event(self):
      super().show_event()
      self.atras = False

  return PaginaPeticion()


_aviso: AvisoPeticionModo | None = None


def instalar() -> AvisoPeticionModo:
  """Crea el aviso (una vez) y lo engancha al tick del nav stack."""
  global _aviso
  if _aviso is None:
    _aviso = AvisoPeticionModo()
    gui_app.add_nav_stack_tick(_aviso.tick)
  return _aviso
