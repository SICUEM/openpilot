"""
Aviso a pantalla completa de la peticion remota de modo de volante, para la UI grande
(3X) y la mici (comma 4). Solo pinta y enruta los toques: leer, aceptar, rechazar y
caducar viven en orbit_peticion_modo.

Es la MISMA confirmacion que da el selector local, en un solo paso: el texto de
`confirmacion_modo(mode)` (y el de `texto_esquive_torque()` con COMMA+JETSON en TORQUE) y
su boton de confirmar, con TEST MAX en rojo como en local. Una peticion remota no puede
pedir menos lectura que elegir el modo a mano.

Se instala con un tick del nav stack (`instalar()`), asi que aparece este donde este el
conductor, onroad u offroad: se empuja encima de todo mientras haya peticion vigente y
se quita al resolverse. No es un NavWidget a proposito: no se puede cerrar deslizando
(en la mici un NavWidget hace pop por su cuenta), solo con Aceptar o Rechazar. Una
instancia por proceso (gc desactivado en la UI: nada de crear widgets por peticion).
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

# (titulo, cuerpo maximo, cuerpo minimo, pie, botones, margen) por pantalla
_TAM_GRANDE = (100, 48, 24, 48, 60, 50)
_TAM_MICI = (26, 14, 8, 14, 16, 8)


def textos_confirmacion(pet: dict) -> tuple[str, str]:
  """(texto de aviso, boton de confirmar): los mismos que el selector local."""
  texto, confirmar = ajustes.confirmacion_modo(pet["mode"])
  if pet["mode"] == 3 and pet["apply_target"] == "torque":
    torque, confirmar = ajustes.texto_esquive_torque(CANCELAR)
    texto = f"{texto}\n\n{torque}"
  return texto, confirmar


class AvisoPeticionModo(Widget):
  def __init__(self):
    super().__init__()
    self._big = gui_app.big_ui()
    self.tam_titulo = 0   # tamano real de la cabecera en el ultimo frame (lo mira el test)
    self._tam = _TAM_GRANDE if self._big else _TAM_MICI
    self._pet: dict | None = None
    self._ultimo_id = ""
    self._ultimo_refresco = float("-inf")
    # Cuerpo ya partido en lineas: (clave, tam de letra, lineas). Se recalcula solo si cambia.
    self._cuerpo: tuple = ((), 0, [])
    boton = self._tam[4]
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
    # En cada frame: si alguien hizo pop_widgets_to (onroad, timeout), vuelve arriba ya.
    self._sincronizar_pila()

  def _sincronizar_pila(self) -> None:
    en_pila = gui_app.widget_in_stack(self)
    if self._pet is not None and not en_pila:
      gui_app.push_widget(self)
      if self._pet["id"] != self._ultimo_id:
        # Peticion nueva: la pantalla tiene que estar encendida para que alguien la vea.
        self._ultimo_id = self._pet["id"]
        device._reset_interactive_timeout()
        if gui_app.sunnypilot_ui():
          ui_state.reset_onroad_sleep_timer()
    elif self._pet is None and en_pila:
      gui_app.pop_widget(gui_app._nav_stack.index(self))

  def _on_aceptar(self) -> None:
    a_salvo("aceptar la peticion de modo")(peticion.aceptar)(ui_state.params, ui_state.engaged)
    self._ultimo_refresco = float("-inf")

  def _on_rechazar(self) -> None:
    a_salvo("rechazar la peticion de modo")(peticion.rechazar)(ui_state.params)
    self._ultimo_refresco = float("-inf")

  def _partir(self, texto: str, ancho: float, alto: float) -> tuple[int, list[str]]:
    """El tamano mas grande al que el texto entero cabe en la caja, y sus lineas."""
    _, maximo, minimo, *_ = self._tam
    if not self._big:
      texto = texto.replace("\n\n", "\n")   # en la mici el aire entre parrafos no cabe
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
    titulo, _, _, pie, boton, m = self._tam
    peligro = self._pet["mode"] == 2
    texto, confirmar = textos_confirmacion(self._pet)
    self._aceptar.set_text(confirmar)
    self._aceptar.set_button_style(ButtonStyle.DANGER if peligro else ButtonStyle.ACTION)

    centro = rl.GuiTextAlignment.TEXT_ALIGN_CENTER
    x, w = rect.x + m, rect.width - 2 * m
    y = rect.y + m
    cabecera = peticion.texto(self._pet)
    negrita = gui_app.font(FontWeight.BOLD)
    while titulo > 8 and measure_text_cached(negrita, cabecera, titulo).x > w:
      titulo -= 2   # sin elidir: el modo y el esquive se tienen que leer enteros
    self.tam_titulo = titulo
    gui_label(rl.Rectangle(x, y, w, titulo * 1.25), cabecera, titulo,
              t.PELIGRO if peligro else t.AVISO, FontWeight.BOLD, alignment=centro, elide_right=False)
    y += titulo * 1.25

    alto_botones = boton * 2.2
    y_botones = rect.y + rect.height - m - alto_botones
    y_pie = y_botones - pie * 1.3
    clave = (texto, w, y_pie - y)
    if self._cuerpo[0] != clave:
      self._cuerpo = (clave, *self._partir(texto, w, y_pie - y))
    _, tam, lineas = self._cuerpo
    fuente = gui_app.font(FontWeight.NORMAL)
    for linea in lineas:
      rl.draw_text_ex(fuente, linea, rl.Vector2(x, y), tam, 0, t.TEXTO1)
      y += tam * INTERLINEA

    if ui_state.engaged:
      linea, color = "Desengancha para aceptar", t.PELIGRO
    else:
      linea, color = f"Caduca en {max(0, int(self._pet['deadline_mono'] - ahora_mono()))} s", t.TEXTO3
    gui_label(rl.Rectangle(x, y_pie, w, pie * 1.3), linea, pie, color, alignment=centro)

    ancho = (w - m) / 2
    self._rechazar.render(rl.Rectangle(x, y_botones, ancho, alto_botones))
    self._aceptar.render(rl.Rectangle(x + m + ancho, y_botones, ancho, alto_botones))


_aviso: AvisoPeticionModo | None = None


def instalar() -> AvisoPeticionModo:
  """Crea el aviso (una vez) y lo engancha al tick del nav stack."""
  global _aviso
  if _aviso is None:
    _aviso = AvisoPeticionModo()
    gui_app.add_nav_stack_tick(_aviso.tick)
  return _aviso
