"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

OrbitLayout - panel ORBIT de los ajustes.

Reparto de interfaz de la seccion 9 del diseno: aqui SOLO queda lo que necesita ojos en
el coche o lo que tiene que funcionar con la red caida.

  * estado del MANDO REMOTO (modo, salud del enlace, ultimo comando y su resultado),
  * ARMADO DE BANCO con confirmacion, TTL de 300 s y cuenta atras,
  * DESARMAR TODO, anclado abajo y fuera del scroll: es el unico control que nunca
    se bloquea y nunca puede quedar fuera de alcance,
  * selector de modo de volante con confirmacion,
  * interruptor maestro LOCAL de privacidad,
  * QR de enrolamiento e IP del broker,
  * submenu Telemetria: que grupos de datos manda el dispositivo a la app,
  * "Restablecer valores seguros".

Se fue a la app: la configuracion de camara. Los canales de telemetria sueltos (8 toggles)
tambien se fueron; vuelven agrupados (posicion, vehiculo...) en el submenu Telemetria.
Se borro: la seccion PRUEBAS (modo_debug) junto con el overlay que consumia modo_debug.

EL ESTADO DEL MANDO SE LEE DE CEREAL, NO DE PARAMS. `ui_state.orbit_command` es la
vista del mensaje `orbitCommandState` (10 Hz) que refresca UIStateSP en cada frame. Los
unicos Params que se leen aqui son los de la cuenta atras del armado, y a 1 Hz.
"""
import time
from enum import IntEnum

import pyray as rl

from openpilot.selfdrive.ui.layouts.settings import settings as OP
from openpilot.selfdrive.ui import orbit_theme as t
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.widgets import orbit_mando as mando
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes
from openpilot.selfdrive.ui.widgets.orbit_enroll_dialog import OrbitEnrollDialog
from openpilot.selfdrive.ui.widgets.orbit_registro_remoto import OrbitRegistroRemoto
from openpilot.selfdrive.ui.widgets.orbit_section import SectionHeaderSP
from openpilot.selfdrive.ui.widgets.orbit_server import ServerMonitor
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.sunnypilot.widgets.list_view import toggle_item_sp, button_item_sp
from openpilot.system.ui.widgets import Widget, DialogResult
from openpilot.system.ui.widgets.button import Button, ButtonStyle
from openpilot.system.ui.widgets.scroller_tici import Scroller
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.orbit_sub_layouts.advanced_settings import AdvancedSettingsLayout
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.orbit_sub_layouts.server_settings import ServerRows
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.orbit_sub_layouts.steer_mode import SteerModeRows
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.orbit_sub_layouts.telemetry_settings import TelemetrySettingsLayout

_REFRESH_SECONDS = 1.0

# Barra anclada de DESARMAR TODO.
_DISARM_BAR_HEIGHT = 132
_DISARM_BAR_GAP = 20
_DISARM_FEEDBACK_S = 2.5

# Tinta de error/aviso: solo texto (nunca relleno), tokens de orbit_theme.
_RED = t.PELIGRO
_AMBER = t.AVISO


def _a_salvo(etiqueta: str, avisar: bool = False):
  """Decorador: la funcion NUNCA deja salir una excepcion al bucle de la UI.

  POR QUE. El bucle de render (system/ui/lib/application.py, `render`) no envuelve
  `widget.render` en ningun try, y los callbacks de los botones se ejecutan dentro de
  ese mismo render. Cualquier excepcion en un `_render`, en un refresco o en un callback
  mata el proceso `ui` ENTERO; manager lo resucita (restart_if_crash) y el usuario ve el
  splash de ORBIT como si el comma se hubiera reiniciado. Y como el armado de banco vive
  en Params y sobrevive al reinicio de la UI, un fallo que dependa del estado "armado"
  vuelve a matarla en cuanto se abre este panel: bucle de reinicios. Es exactamente lo
  que paso al pulsar ARMAR con una referencia a una constante que ya no existia
  (mando.ARM_REASON_STEER) dentro de `_refresh_status`.

  Con `avisar=True` (acciones del usuario: armar, desarmar, restablecer) ademas se lo
  cuenta con un dialogo: una accion que falla muda es peor que una que no existe. Los
  refrescos de pintado solo lo dejan en el log (van a 1 Hz, no inundan).
  """
  return ajustes.a_salvo(etiqueta, _avisar_fallo if avisar else None)


def _aviso(msg: str):
  """Aviso de un solo boton «Entendido» (neutro): el OK verde de alert_dialog se lee como exito."""
  return ajustes.dialogo_orbit(msg, tr("Entendido"), ButtonStyle.NORMAL, cancelar="")


def _avisar_fallo(etiqueta: str) -> None:
  gui_app.push_widget(_aviso(tr("Fallo interno en:") + f" {etiqueta}\n" +
                            tr("La acción no se ha completado. Revisa el log de la UI.")))


# Tinta de cada tono de ajustes.lineas_mando.
_TONOS = {"ok": OP.ORBIT_GREEN, "aviso": _AMBER, "peligro": _RED, "normal": OP.ORBIT_INK}


def ayuda_html() -> str:
  """Definiciones de la terminologia que menos se explica sola (HTML <h2>/<p>).

  Funcion de modulo: la usa este panel y la pagina de ayuda del comma 4
  (sunnypilot/mici/layouts/orbit.py), asi que las dos pantallas dicen lo mismo.
  """
  return (
    "<h2>" + tr("Modo taller") + "</h2><p>" +
    tr("Durante 5 minutos la app podrá mover el volante. Se arma solo desde esta pantalla, " +
       "con el coche parado. Se desarma a los 5 minutos, al pasar de 5 km/h o al " +
       "apagar el coche.") + "</p>" +
    "<h2>" + tr("Desarmar todo") + "</h2><p>" +
    tr("Cancela cualquier orden en curso y te devuelve el control. Funciona siempre, " +
       "aunque falle la conexión.") + "</p>" +
    "<h2>" + tr("Modo (observador / copiloto / maniobra)") + "</h2><p>" +
    tr("El nivel de autoridad que la app tiene sobre el coche. El coche arranca " +
       "siempre en observador. Subir de modo desde la app dura poco: copiloto 15 min, " +
       "maniobra 2 min.") + "</p>" +
    "<h2>" + tr("Enlace") + "</h2><p>" +
    tr("Salud de la conexión de mando con el servidor. Si está caído, las órdenes " +
       "remotas no llegan.") + "</p>" +
    "<h2>" + tr("Taller armado") + "</h2><p>" +
    tr("El modo taller está activo y quedan los segundos que se muestran. Mientras " +
       "esté armado, la app puede mover el volante.") + "</p>"
  )


class PanelType(IntEnum):
  MAIN = 0
  ADVANCED = 1
  TELEMETRY = 2
  REGISTRO = 3


class _MandoCard(Widget):
  """La tarjeta de cabecera del panel: identidad ORBIT + estado del MANDO REMOTO.

  Absorbe el hero anterior (una tarjeta de 312 px que solo llevaba logo, wordmark y
  chips) porque el panel tenia ~2.950 px de scroll y la seccion 9 pide adelgazarlo. La
  informacion no se pierde: los chips SERVIDOR / ENLACE / CUENTA siguen aqui, en la
  franja superior, y debajo van las tres lineas que exige el punto 1 del encargo:

    MODO            modo vigente del mando (y el chip de BANCO ARMADO con su cuenta atras)
    ENLACE          salud del enlace de mando
    ULTIMO COMANDO  verbo + fase del ACK + motivo

  Los tres salen del mensaje cereal `orbitCommandState` a traves de
  `ui_state.orbit_command`, que UIStateSP refresca en cada frame. Si el plano no publica
  NO se pinta verde ni se conserva el ultimo valor conocido: se pinta "Mando no
  disponible: reinicia el comma". Un panel de mando que miente sobre el estado del mando es peor que no
  tenerlo.

  Lo que se lee de Params (chips y cuenta atras) esta limitado a _REFRESH_SECONDS; por
  frame no se lee nada.
  """

  HEIGHT = 340
  LINEA_BLOQUEO = 56   # alto extra de la linea «Mando remoto bloqueado»

  def __init__(self, monitor: ServerMonitor):
    super().__init__()
    self._rect = rl.Rectangle(0, 0, 0, self.HEIGHT)
    self._monitor = monitor
    self._font_bold = gui_app.font(FontWeight.BOLD)
    self._font = gui_app.font(FontWeight.NORMAL)
    try:
      self._logo = gui_app.texture("img_orbit_logo.png", 56, 56)
    except Exception:
      self._logo = None

    self._last_refresh = 0.0
    # (texto, falla): una sola linea de estado; el punto de color solo marca lo que falla.
    self._estado: list[tuple[str, bool]] = []
    self._bench_restante = 0.0
    self._remoto_off = False

  def set_parent_rect(self, parent_rect: rl.Rectangle) -> None:
    super().set_parent_rect(parent_rect)
    self._rect.width = parent_rect.width

  @_a_salvo("refresco de la tarjeta de mando")
  def _refresh(self):
    now = time.monotonic()
    if now - self._last_refresh < _REFRESH_SECONDS:
      return
    self._last_refresh = now

    # Cuenta atras del armado: se refresca a 1 Hz, que es justo lo que necesita un
    # contador en segundos, y no en cada frame (serian 60 lecturas de Params).
    _, self._bench_restante = mando.bench_snapshot()

    params = ui_state.params
    # Mando remoto bloqueado desde este comma: la tarjeta crece una linea para explicarlo.
    self._remoto_off = ajustes.remoto_apagado(params)
    self._rect.height = self.HEIGHT + (self.LINEA_BLOQUEO if self._remoto_off else 0)
    connected = ajustes.enlace_orbit(params)
    # Dueno + rol ("ADRIAN • SUPERADMIN"): el rol lo escribe mqtt_comandos desde el
    # enroll_ack del backend (contrato C2).
    cuenta = ajustes.etiqueta_cuenta(params.get(mando.PARAM_OWNER), params.get(mando.PARAM_OWNER_ROLE))

    server_ok = self._monitor.broker_ok and self._monitor.backend_ok

    self._estado = [
      (tr("Servidor conectado") if server_ok else tr("Servidor caído"), not server_ok),
      (tr("Enlace conectado") if connected else tr("Enlace caído"), not connected),
      (tr("Cuenta:") + f" {cuenta}" if cuenta else tr("Sin vincular"), False),
    ]
    # Desvinculo esperando al servidor: lo mismo que la fila gris de Dispositivo y el comma 4.
    # Sustituye a la cuenta (que se va) para que la linea siga cabiendo.
    if cuenta and ajustes.estado_desvinculo(params, connected):
      # Tres puntos ASCII: la fuente bold de la cabecera no tiene «…» (salia «?»).
      self._estado[-1] = (tr("Desvinculando..."), False)

  # --------------------------------------------------------------------- pintado
  def _draw_identity(self, card: rl.Rectangle, pad: float) -> float:
    """Franja superior: logo + wordmark a la izquierda, chips a la derecha."""
    y = card.y + 20
    strip_h = 56
    x = card.x + pad
    if self._logo is not None:
      rl.draw_texture_pro(
        self._logo,
        rl.Rectangle(0, 0, self._logo.width, self._logo.height),
        rl.Rectangle(x, y, 56, 56),
        rl.Vector2(0, 0), 0, rl.WHITE,
      )
      x += 56 + 18

    wm = measure_text_cached(self._font_bold, "ORBIT", 36, 3)
    titulo_y = y + (strip_h - wm.y) / 2
    rl.draw_text_ex(self._font_bold, "ORBIT", rl.Vector2(x, titulo_y), 36, 3, OP.ORBIT_INK)
    sep_y = y + strip_h + 16
    rl.draw_line_ex(rl.Vector2(card.x + pad, sep_y), rl.Vector2(card.x + card.width - pad, sep_y),
                    2, OP.ORBIT_HAIRLINE)
    return sep_y + 18

  def _draw_estado(self, x: float, y: float, ancho: float) -> float:
    """Linea de estado de una sola linea a 36 px: «Servidor conectado. Enlace caído. Sin vincular»."""
    cx = x
    for i, (texto, falla) in enumerate(self._estado):
      if falla:
        rl.draw_circle(int(cx + 10), int(y + 20), 8, _RED)
        cx += 28
      suf = "." if i < len(self._estado) - 1 else ""
      rl.draw_text_ex(self._font_bold, texto + suf, rl.Vector2(cx, y), 36, 0, OP.ORBIT_INK)
      cx += measure_text_cached(self._font_bold, texto + suf, 36, 0).x + 18
      if cx > x + ancho:
        break
    return y + 62

  # Columna de valores: "ULTIMO COMANDO" a 26 px mide ~300, asi que el valor arranca
  # despues o se solapa con su propia etiqueta.
  VALUE_X = 340

  def _line(self, y: float, x: float, etiqueta: str, valor: str, color: rl.Color, size: int = 34) -> None:
    rl.draw_text_ex(self._font, etiqueta, rl.Vector2(x, y + 6), 26, 1, OP.ORBIT_MUTED)
    rl.draw_text_ex(self._font_bold, valor, rl.Vector2(x + self.VALUE_X, y), size, 0, color)

  def _render(self, _):
    self._refresh()
    card = rl.Rectangle(self._rect.x, self._rect.y + 8, self._rect.width, self._rect.height - 16)
    rl.draw_rectangle_rounded(card, 0.12, 12, OP.ORBIT_NAVY)
    # El borde nunca lleva color de seccion (regla de la spec): BORDE liso.
    # El acento de "mando" queda solo en el filete corto bajo el titulo (_draw_identity).
    rl.draw_rectangle_rounded_lines_ex(card, 0.12, 12, 2, t.BORDE)

    pad = 28
    x = card.x + pad
    y = self._draw_identity(card, pad)
    y = self._draw_estado(x, y, card.width - 2 * pad)

    # Un bloqueo se explica junto a lo que bloquea; en ambar (restrictivo, no «todo bien») y
    # con prioridad sobre «reinicia el comma».
    if self._remoto_off:
      rl.draw_text_ex(self._font_bold, tr("Mando remoto bloqueado desde este comma"), rl.Vector2(x, y), 34, 0, _AMBER)
      y += self.LINEA_BLOQUEO

    st = getattr(ui_state, "orbit_command", None)
    if st is None or not st.available:
      if self._remoto_off:
        return
      rl.draw_text_ex(self._font_bold, tr("Mando no disponible: reinicia el comma"), rl.Vector2(x, y), 36, 0, _RED)
      return

    # Modo / enlace / ultimo comando: el texto y el tono salen de ajustes.lineas_mando
    # (el comma 4 pinta lo mismo); aqui solo se pone la tinta y la geometria.
    (modo_et, modo_val, modo_tono), (enl_et, enl_val, enl_tono), (ult_et, texto, ult_tono) = ajustes.lineas_mando(st)

    # 1) modo vigente + chip de armado con cuenta atras
    self._line(y, x, modo_et, modo_val, _TONOS[modo_tono])
    if st.bench_armed:
      etiqueta = tr("Taller armado") + f"  {int(self._bench_restante)} s"
      size = measure_text_cached(self._font_bold, etiqueta, 24, 1)
      chip = rl.Rectangle(card.x + card.width - pad - size.x - 36, y - 2, size.x + 36, 42)
      rl.draw_rectangle_rounded(chip, 1.0, 10, _AMBER)
      rl.draw_text_ex(self._font_bold, etiqueta, rl.Vector2(chip.x + 18, chip.y + (42 - size.y) / 2),
                      24, 1, t.FONDO)

    # 2) salud del enlace de mando
    y += 62
    self._line(y, x, enl_et, enl_val, _TONOS[enl_tono])

    # 3) ultimo comando y como acabo
    y += 62
    # El motivo puede ser largo: se recorta al ancho de la tarjeta en vez de desbordarla.
    max_w = card.width - (x - card.x) - self.VALUE_X - pad
    while texto and measure_text_cached(self._font_bold, texto, 30, 0).x > max_w:
      texto = texto[:-1]
    self._line(y, x, ult_et, texto, _TONOS[ult_tono], size=30)


class OrbitLayout(Widget):
  def __init__(self):
    super().__init__()

    self._current_panel = PanelType.MAIN
    self._advanced_layout = AdvancedSettingsLayout(lambda: self._set_current_panel(PanelType.MAIN))
    self._telemetry_layout = TelemetrySettingsLayout(lambda: self._set_current_panel(PanelType.MAIN))
    self._registro_layout = OrbitRegistroRemoto(lambda: self._set_current_panel(PanelType.MAIN))

    self._monitor = ServerMonitor()
    self._server_rows = ServerRows()
    self._steer_rows = SteerModeRows()

    self._last_refresh = 0.0
    self._fallo_desvinculo_t = 0.0
    self._bench_status = ""
    # Cacheados en _refresh_status (1 Hz): los lambdas de las filas se evaluan en cada
    # frame y leer Params ahi es abrir ficheros 60 veces por segundo.
    self._bench_armed = False
    self._disarm_feedback_until = 0.0

    # DESARMAR TODO vive FUERA del Scroller: anclado abajo, siempre a la vista. Un boton
    # de panico al que hay que llegar haciendo scroll no es un boton de panico.
    self._disarm_button = Button(
      lambda: tr("Desarmado, ninguna orden en curso") if self._desarmado_ahora() else tr("Desarmar todo"),
      click_callback=self._do_disarm_all,
      font_size=52,
      font_weight=FontWeight.BOLD,
      button_style=ButtonStyle.DANGER,
      border_radius=16,
    )

    items = self._initialize_items()
    self._scroller = Scroller(items, line_separator=False, spacing=0)

  @staticmethod
  def _vinculado() -> bool:
    try:
      return bool(ui_state.params.get_bool("OrbitClaimed"))
    except Exception:
      return False

  def _desarmado_ahora(self) -> bool:
    return time.monotonic() < self._disarm_feedback_until

  # ------------------------------------------------------------------------- items
  def _initialize_items(self):
    self._mando_card = _MandoCard(self._monitor)

    self._bench_button = button_item_sp(
      title=lambda: tr("Modo taller"),
      button_text=lambda: tr("Desarmar") if self._bench_armed else tr("Armar"),
      description=lambda: self._bench_status,
      callback=self._toggle_bench,
    )

    self._help_button = button_item_sp(
      title=lambda: tr("Qué significa cada cosa"),
      button_text=lambda: tr("Abrir"),
      description=lambda: tr("Definiciones de armar, desarmar, los modos y el enlace."),
      callback=self._show_help,
    )

    self._privacy_toggle = toggle_item_sp(
      title=lambda: tr("No enviar posición ni cámara"),
      description=lambda: tr("Interruptor maestro local. Corta el envío de posición y de imagen " +
                             "desde el propio coche: funciona sin red y con el móvil apagado."),
      initial_state=mando.privacy_muted(),
      callback=self._on_privacy,
    )

    self._remote_off_toggle = toggle_item_sp(
      title=lambda: tr("Bloquear mando remoto"),
      description=ajustes.texto_remoto_off,
      initial_state=ajustes.remoto_apagado(ui_state.params),
      callback=self._on_remote_off,
    )

    self._remote_log_button = button_item_sp(
      title=lambda: tr("Órdenes remotas"),
      button_text=lambda: tr("Abrir"),
      description=lambda: tr("Las últimas 50 órdenes que llegaron de la app o el servidor y qué se hizo con ellas."),
      callback=lambda: self._set_current_panel(PanelType.REGISTRO),
      enabled=lambda: ui_state.is_offroad(),
    )

    self._enroll_button = button_item_sp(
      title=lambda: tr("Vincular con la app"),
      button_text=lambda: tr("Mostrar"),
      description=lambda: tr("Muestra en esta pantalla el código QR para vincular el comma."),
      callback=lambda: gui_app.push_widget(OrbitEnrollDialog()),
    )
    # Ya vinculado no hace falta: la cuenta sale en la linea de estado de la cabecera.
    self._enroll_button.set_visible(lambda: not self._vinculado())

    self._telemetry_button = button_item_sp(
      title=lambda: tr("Telemetría"),
      button_text=lambda: tr("Abrir"),
      description=lambda: tr("Qué datos manda el dispositivo a la app: posición, vehículo, percepción... " +
                             "y el ahorro automático en red móvil."),
      callback=lambda: self._set_current_panel(PanelType.TELEMETRY),
    )

    self._advanced_button = button_item_sp(
      title=lambda: tr("Ajustes avanzados"),
      button_text=lambda: tr("Abrir"),
      description=lambda: tr("Avisos en pantalla (ángulo muerto, cambio de carril) y enlace con la " +
                             "Jetson (IPs, puertos, calidad de imagen)."),
      callback=lambda: self._set_current_panel(PanelType.ADVANCED),
    )

    self._safe_reset_button = button_item_sp(
      title=lambda: tr("Valores seguros"),
      button_text=lambda: tr("Restablecer"),
      description=lambda: tr("Devuelve los ajustes de conducción de ORBIT a su estado " +
                             "seguro (volante Comma, sin órdenes remotas pendientes, alertas visibles)."),
      callback=self._confirm_safe_reset,
    )

    # Tres cabeceras, no seis: cada SectionHeaderSP son 96 px de scroll.
    return [
      self._mando_card,
      self._bench_button,
      self._help_button,
      SectionHeaderSP(tr("Volante"), seccion='mando'),
      *self._steer_rows.items,
      SectionHeaderSP(tr("Conexión"), seccion='ajustes'),
      self._enroll_button,
      # Solo la fila del broker: "Probar conexion" sigue en el modal SERVIDOR de la home.
      self._server_rows.items[0],
      SectionHeaderSP(tr("Dispositivo"), seccion='mando'),
      self._privacy_toggle,
      self._remote_off_toggle,
      self._remote_log_button,
      self._telemetry_button,
      self._advanced_button,
      self._safe_reset_button,
    ]

  # --------------------------------------------------------------- armado de banco
  @_a_salvo("modo taller", avisar=True)
  def _toggle_bench(self):
    if mando.bench_armed():   # sin cache: es una accion, no un pintado
      self._apply_bench_disarm()
      return

    msg = ajustes.texto_armar_banco()

    def on_result(result: DialogResult):
      if result != DialogResult.CONFIRM:
        return
      self._apply_bench_arm()

    gui_app.push_widget(ajustes.dialogo_orbit(msg, tr("Armar 5 minutos"), ButtonStyle.ACTION, tr("Cancelar"), callback=on_result))

  @_a_salvo("armar el modo taller", avisar=True)
  def _apply_bench_arm(self):
    """Corre como callback del ConfirmDialog, o sea dentro del render: a salvo."""
    fallos = mando.arm_bench()
    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_local_arm(mando.ARM_REASON_BENCH)
    self._last_refresh = 0.0
    if fallos:
      gui_app.push_widget(_aviso(tr("No se pudo armar el modo taller:") + "\n" + "\n".join(fallos)))

  @_a_salvo("desarmar el modo taller", avisar=True)
  def _apply_bench_disarm(self):
    fallos = mando.disarm_bench()
    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_disarm()
    self._last_refresh = 0.0
    if fallos:
      gui_app.push_widget(_aviso(tr("No se pudo desarmar el modo taller:") + "\n" + "\n".join(fallos)))

  # ------------------------------------------------------------------ definiciones
  @_a_salvo("definiciones del panel", avisar=True)
  def _show_help(self):
    """Dialogo con las definiciones de la terminologia que menos se explica sola.

    El usuario pidio un boton en el menu que diga que son ARMAR y DESARMAR y el resto
    de conceptos que no quedan claros. Es un dialogo informativo (sin confirmacion):
    no toca ningun param, asi que no puede romper nada.

    Se usa rich=True (HTML + Scroller) a proposito: el texto es largo y el modo
    plano (rich=False) recorta con scissor lo que no cabe en el area fija del modal.
    Con rich el contenido se desplaza y nada se pierde.
    """
    msg = ayuda_html()
    gui_app.push_widget(ajustes.dialogo_orbit(msg, tr("Entendido"), ButtonStyle.ACTION, cancelar="", rich=True))

  # ------------------------------------------------------------------ desarmar todo
  @_a_salvo("desarmar todo", avisar=True)
  def _do_disarm_all(self):
    fallos = mando.disarm_all()
    self._steer_rows.sync()
    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_disarm()
    self._last_refresh = 0.0
    if fallos:
      gui_app.push_widget(_aviso(tr("Desarme incompleto. Han fallado:") + "\n" + "\n".join(fallos)))
    else:
      self._disarm_feedback_until = time.monotonic() + _DISARM_FEEDBACK_S

  # ---------------------------------------------------------------------- privacidad
  @_a_salvo("interruptor de privacidad", avisar=True)
  def _on_privacy(self, enabled: bool):
    fallos = mando.set_privacy_mute(bool(enabled))
    if fallos:
      gui_app.push_widget(_aviso(tr("El corte de envío falló en:") + "\n" + "\n".join(fallos)))

  # -------------------------------------------------- bloqueo del mando remoto
  @_a_salvo("bloquear mando remoto", avisar=True)
  def _on_remote_off(self, apagar: bool):
    """Activar no pide confirmacion; quitarlo si (vuelve a dar autoridad a la app)."""
    if apagar:
      self._aplicar_remote_off(True)
      return

    def on_result(result: DialogResult):
      if result == DialogResult.CONFIRM:
        self._aplicar_remote_off(False)
      else:
        self._remote_off_toggle.action_item.toggle.set_state(ajustes.remoto_apagado(ui_state.params))

    gui_app.push_widget(ajustes.dialogo_orbit(tr("¿Volver a aceptar órdenes remotas?"), tr("Aceptar órdenes"),
                                              ButtonStyle.ACTION, tr("Cancelar"), callback=on_result))

  @_a_salvo("bloquear mando remoto", avisar=True)
  def _aplicar_remote_off(self, apagar: bool):
    fallos = ajustes.cambiar_remoto(ui_state.params, apagar)
    self._remote_off_toggle.action_item.toggle.set_state(ajustes.remoto_apagado(ui_state.params))
    if fallos:
      gui_app.push_widget(_aviso(tr("El bloqueo del mando remoto falló en:") + "\n" + "\n".join(fallos)))

  # -------------------------------------------------- restablecer valores seguros
  def _confirm_safe_reset(self):
    msg = ajustes.texto_valores_seguros()

    def on_result(result: DialogResult):
      if result != DialogResult.CONFIRM:
        return
      self._apply_safe_reset()

    gui_app.push_widget(ajustes.dialogo_orbit(msg, tr("Restablecer"), ButtonStyle.ACTION, tr("Cancelar"), callback=on_result))

  @_a_salvo("restablecer valores seguros", avisar=True)
  def _apply_safe_reset(self):
    """Siete grupos de escrituras independientes: ver ajustes.aplicar_valores_seguros."""
    fallos = ajustes.aplicar_valores_seguros(ui_state.params)

    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_disarm()
    self._steer_rows.sync()
    self._last_refresh = 0.0  # repintar el estado vivo de inmediato

    if fallos:
      gui_app.push_widget(_aviso(tr("Restablecimiento incompleto. Han fallado:") +
                                       "\n" + "\n".join(fallos)))

  # ------------------------------------------------------------------ estado vivo
  @_a_salvo("refresco del estado del armado")
  def _refresh_status(self):
    now = time.monotonic()
    if now - self._last_refresh < _REFRESH_SECONDS:
      return
    self._last_refresh = now

    armado, restante_s = mando.bench_snapshot()
    self._bench_armed = armado
    # Solo existe UN motivo de armado (ARM_REASON_BENCH, el boton de esta pantalla): el
    # selector de volante no arma el banco, va por OrbitSteerModeLocal (ver steer_mode.py).
    # Aqui se comparaba con `mando.ARM_REASON_STEER`, una constante que se retiro con ese
    # cambio, y como solo se ejecutaba con el banco ARMADO nadie lo vio hasta que alguien
    # pulso ARMAR en el coche: AttributeError en cada frame, muerte del proceso ui y bucle
    # de reinicios (ver _a_salvo).
    self._bench_status = ajustes.texto_estado_banco(armado, restante_s)

  # -------------------------------------------------------------------- lifecycle
  def _set_current_panel(self, panel: PanelType):
    self._current_panel = panel
    if panel == PanelType.TELEMETRY:
      # Relee los toggles al abrir: la app o el interruptor de privacidad pudieron cambiarlos.
      self._telemetry_layout.show_event()
    if panel == PanelType.REGISTRO:
      self._registro_layout.show_event()

  @_a_salvo("aviso de desvinculo fallido")
  def _avisar_fallo_desvinculo(self):
    """Como Dispositivo: un desvinculo fallido se cuenta UNA vez (lo consume), aunque la
    persona este en este panel. A 1 Hz: por frame no se lee nada."""
    now = time.monotonic()
    if now - self._fallo_desvinculo_t < _REFRESH_SECONDS:
      return
    self._fallo_desvinculo_t = now
    if fallo := ajustes.fallo_desvinculo_pendiente(ui_state.params):
      gui_app.push_widget(_aviso(fallo))   # el texto ya empieza por «No se pudo desvincular»

  def _render(self, rect):
    self._avisar_fallo_desvinculo()
    if self._current_panel == PanelType.ADVANCED:
      self._advanced_layout.render(rect)
      return
    if self._current_panel == PanelType.TELEMETRY:
      self._telemetry_layout.render(rect)
      return
    if self._current_panel == PanelType.REGISTRO:
      self._registro_layout.render(rect)
      return

    self._refresh_status()
    self._server_rows.poll()
    self._steer_rows.poll()

    # El scroller cede la franja inferior a la barra de desarme para que no se solapen:
    # si compartieran rect, un toque en el boton contaria tambien como arrastre.
    bar_h = _DISARM_BAR_HEIGHT + _DISARM_BAR_GAP
    self._scroller.render(rl.Rectangle(rect.x, rect.y, rect.width, max(0.0, rect.height - bar_h)))
    barra = rl.Rectangle(rect.x, rect.y + rect.height - _DISARM_BAR_HEIGHT, rect.width, _DISARM_BAR_HEIGHT)
    # Confirmacion neutra sobre baldosa SUP3: el rojo tras un exito se lee como fallo (guia visual 5.4).
    # El boton se queda sin relleno propio y la baldosa se pinta debajo.
    if self._desarmado_ahora():
      rl.draw_rectangle_rounded(barra, 16 / (barra.height / 2), 10, t.SUP3)
      self._disarm_button.set_button_style(ButtonStyle.TRANSPARENT_WHITE_TEXT)
    else:
      self._disarm_button.set_button_style(ButtonStyle.DANGER)
    self._disarm_button.render(barra)

  def show_event(self):
    self._set_current_panel(PanelType.MAIN)
    self._last_refresh = 0.0
    self._steer_rows.sync()
    self._privacy_toggle.action_item.toggle.set_state(mando.privacy_muted())
    self._remote_off_toggle.action_item.toggle.set_state(ajustes.remoto_apagado(ui_state.params))
    self._scroller.show_event()
