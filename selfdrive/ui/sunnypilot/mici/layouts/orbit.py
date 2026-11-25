"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

Panel ORBIT de los ajustes del comma 4 (536x240): lo mismo que el panel ORBIT de la UI
grande (sunnypilot/layouts/settings/orbit_panel.py), en baldosas mici.

  * desarmar todo, la primera baldosa y en rojo: se ve nada mas abrir el panel, sin
    arrastrar. Un boton de panico al que hay que llegar haciendo scroll no lo es.
  * estado del MANDO (de cereal via ui_state.orbit_command, nunca rancio) y de la
    CONEXION (servidor, enlace, cuenta con su rol),
  * modo taller, "que significa esto", selector de volante,
  * vincular con la app (QR) / cuenta + desvincular (orden por estado: ver _reordenar), IP del servidor y prueba,
  * interruptor maestro de privacidad, telemetria (que grupos de datos se envian a la app),
    ajustes avanzados y valores seguros.

La logica (textos, validaciones, escrituras) es la de orbit_ajustes / orbit_mando /
orbit_server: la misma que usa el comma 3X. Aqui solo hay baldosas. Params se leen a
2 Hz como mucho; todo callback va envuelto en a_salvo (una excepcion no puede matar el
proceso ui).
"""
import re
import threading
import time

from openpilot.orbit import config_broker
from openpilot.selfdrive.ui import orbit_theme as t
from openpilot.selfdrive.ui.mici.widgets.button import LABEL_COLOR, BigToggle
from openpilot.selfdrive.ui.sunnypilot.mici.layouts.orbit_avanzado import AvanzadoLayoutMici
from openpilot.selfdrive.ui.sunnypilot.mici.layouts.orbit_registro_remoto import OrbitRegistroRemotoMici
from openpilot.selfdrive.ui.sunnypilot.mici.layouts.orbit_telemetria import TelemetriaLayoutMici
from openpilot.selfdrive.ui.sunnypilot.mici.layouts.orbit_volante import VolanteLayoutMici, estado_volante, nombre_modo
from openpilot.selfdrive.ui.sunnypilot.mici.widgets.orbit_enroll_dialog import OrbitEnrollDialogMici
from openpilot.selfdrive.ui.sunnypilot.mici.widgets.orbit_widgets import (
  GRIS, TONOS, Baldosa, BotonRojo, PaginaConfirmacion, TarjetaEstado, TarjetaTexto, a_salvo, aviso, dialogo_numerico, minuscula,
  trozos_mici,
)
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.widgets import orbit_ajustes as ajustes
from openpilot.selfdrive.ui.widgets import orbit_mando as mando
from openpilot.selfdrive.ui.widgets.orbit_server import ServerMonitor, probar_servidor, read_broker
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets.scroller import NavScroller

REFRESH_S = 0.5            # Params y config a 2 Hz como mucho
DESARMADO_FEEDBACK_S = 2.5
TXT_DESARMAR = "cancela órdenes"


class AyudaOrbitMici(NavScroller):
  """"Que significa esto": las mismas definiciones que el dialogo de la UI grande, en tarjetas."""

  def __init__(self):
    super().__init__()
    # Import perezoso: orbit_panel arrastra la UI grande entera; solo se paga al abrir.
    from openpilot.selfdrive.ui.sunnypilot.layouts.settings.orbit_panel import ayuda_html
    tarjetas: list[TarjetaTexto] = []
    for titulo, cuerpo in re.findall(r"<h2>(.*?)</h2><p>(.*?)</p>", ayuda_html(), re.S):
      for i, trozo in enumerate(trozos_mici(cuerpo)):
        tarjetas.append(TarjetaTexto(trozo, minuscula(titulo) if i == 0 else ""))
    self._scroller.add_widgets(tarjetas)


class OrbitLayoutMici(NavScroller):
  def __init__(self):
    super().__init__()
    self._monitor: ServerMonitor | None = None
    self._ultimo_refresco = float("-inf")
    self._desarmado_hasta = 0.0
    self._resultado_prueba: tuple[str, int, bool, bool] | None = None
    self._probando = False
    self._claimed = False
    self._cuenta = ""
    self._enlace = False
    self._banco_restante = 0.0
    self._orden_clave: tuple[bool, bool] | None = None
    self._desvinculando = False

    self._btn_desarmar = BotonRojo("desarmar todo", TXT_DESARMAR)
    self._btn_desarmar.set_click_callback(self._desarmar_todo)

    self._tarjeta_mando = TarjetaEstado("mando")
    self._tarjeta_ultimo = TarjetaEstado("última orden")
    self._tarjeta_conexion = TarjetaEstado("conexión")

    self._btn_banco = Baldosa("modo taller", "")
    self._btn_banco.set_click_callback(self._pulsar_banco)

    self._volante = VolanteLayoutMici()
    self._btn_volante = Baldosa("volante", "")
    self._btn_volante.set_click_callback(lambda: gui_app.push_widget(self._volante))

    self._ayuda: AyudaOrbitMici | None = None
    self._btn_ayuda = Baldosa("qué significa cada cosa", "definiciones")
    self._btn_ayuda.set_click_callback(self._abrir_ayuda)

    self._qr: OrbitEnrollDialogMici | None = None
    self._btn_vincular = Baldosa("vincular con la app", "muestra el qr")
    self._btn_vincular.set_click_callback(self._abrir_qr)
    self._btn_vincular.set_visible(lambda: not self._claimed)
    self._btn_desvincular = Baldosa("desvincular", "quitar la cuenta")
    self._btn_desvincular.set_click_callback(self._pedir_desvincular)
    self._btn_desvincular.set_visible(lambda: self._claimed)

    self._btn_servidor = Baldosa("servidor orbit", "")
    self._btn_servidor.set_click_callback(lambda: self._editar_broker())
    self._btn_probar = Baldosa("probar conexión", "broker y api")
    self._btn_probar.set_click_callback(self._probar)

    self._tgl_privacidad = BigToggle("no enviar", "posición ni cámara", initial_state=mando.privacy_muted(),
                                     toggle_callback=self._on_privacidad)

    self._tgl_remoto = BigToggle("bloquear mando remoto", "ignora la app", initial_state=ajustes.remoto_apagado(ui_state.params),
                                 toggle_callback=self._on_remoto)
    self._registro = OrbitRegistroRemotoMici()
    self._btn_registro = Baldosa("órdenes remotas", "últimas 50")
    self._btn_registro.set_click_callback(lambda: gui_app.push_widget(self._registro))
    self._btn_registro.set_visible(lambda: ui_state.is_offroad())

    self._telemetria = TelemetriaLayoutMici()
    self._btn_telemetria = Baldosa("telemetría", "qué se envía a la app")
    self._btn_telemetria.set_click_callback(lambda: gui_app.push_widget(self._telemetria))

    self._avanzado = AvanzadoLayoutMici()
    self._btn_avanzado = Baldosa("ajustes avanzados", "hud y jetson")
    self._btn_avanzado.set_click_callback(lambda: gui_app.push_widget(self._avanzado))

    self._btn_seguros = Baldosa("valores seguros", "restablecer")
    self._btn_seguros.set_click_callback(self._pedir_valores_seguros)

    self._reordenar()

  def _reordenar(self) -> None:
    """Orden por estado: lo que toca hacer ahora, arriba. Solo se rehace si cambia el estado."""
    clave = (self._claimed, self._desvinculando)
    if clave == self._orden_clave:
      return
    self._orden_clave = clave
    resto = [self._btn_ayuda, self._btn_servidor, self._btn_probar, self._tgl_privacidad, self._tgl_remoto,
             self._btn_registro, self._btn_telemetria, self._btn_avanzado, self._btn_seguros]
    if not self._claimed:
      orden = [self._btn_desarmar, self._btn_vincular, self._tarjeta_conexion, self._tarjeta_mando, self._tarjeta_ultimo,
               self._btn_volante, self._btn_banco, *resto]
    else:
      orden = [self._btn_desarmar, *([self._btn_desvincular] if self._desvinculando else []), self._tarjeta_mando,
               self._tarjeta_conexion, self._tarjeta_ultimo, self._btn_volante, self._btn_banco,
               *([] if self._desvinculando else [self._btn_desvincular]), *resto]
    self._scroller.items[:] = orden

  # ================================================================ estado vivo
  @a_salvo("refresco del panel ORBIT")
  def _refrescar(self) -> None:
    p = ui_state.params
    self._claimed = bool(p.get_bool("OrbitClaimed"))
    self._cuenta = ajustes.etiqueta_cuenta(p.get(mando.PARAM_OWNER), p.get(mando.PARAM_OWNER_ROLE))
    self._enlace = ajustes.enlace_orbit(p)

    armado, self._banco_restante = mando.bench_snapshot()
    # El valor dice que hace el toque: armado, un toque desarma SIN confirmacion.
    self._btn_banco.set_value(f"armado {int(self._banco_restante)} s\ntoca para desarmar" if armado
                              else "desarmado\ntoca para armar")

    modo, estado = estado_volante()
    self._btn_volante.set_value(f"{nombre_modo(modo)}\n{estado.lower()}")

    # Desvinculo en curso: la baldosa dice en que punto va; un fallo sale UNA vez.
    estado = ajustes.estado_desvinculo(p, self._enlace)
    self._desvinculando = bool(estado)
    self._btn_desvincular.set_value(estado or "quitar la cuenta")
    self._reordenar()
    if fallo := ajustes.fallo_desvinculo_pendiente(p):
      # "No se pudo desvincular. <que hacer>": el titulo y la salida, sin truncar.
      titulo, _, salida = fallo.partition(". ")
      aviso(titulo.lower(), salida.lower())
    ip, _ = read_broker()
    self._btn_servidor.set_value(ip or "sin configurar")

  @a_salvo("tarjetas del panel ORBIT")
  def _pintar_tarjetas(self) -> None:
    """Cada frame, pero solo RAM: el mando es la vista cereal que UIStateSP refresca."""
    st = getattr(ui_state, "orbit_command", None)
    tm, tu = self._tarjeta_mando, self._tarjeta_ultimo
    tu.set_visible(False)
    if st is None or not st.available:
      # Un plano muerto no se pinta en verde ni con el ultimo valor conocido.
      tm.filas = [("", "no disponible", t.PELIGRO),   # el titulo de la tarjeta ya dice «mando»
                  ("", "la app no puede mandar órdenes. reinicia el comma si sigue así", GRIS)]
      tm.chip = None
    else:
      (_, modo, tono_m), (_, enlace, tono_e), (_, ultimo, tono_u) = ajustes.lineas_mando(st)
      tm.filas = [("modo", modo.lower(), TONOS[tono_m]), ("enlace", enlace.lower(), TONOS[tono_e])]
      tm.chip = (f"taller {int(self._banco_restante)}s", t.AVISO) if st.bench_armed else None
      # La tarjeta de la ultima orden solo existe si hay una.
      if st.last_ack_phase != "none":
        tu.filas = [("", ultimo.lower(), TONOS[tono_u])]
        tu.set_visible(True)

    mon = self._monitor
    if mon is None:
      servidor, color = "comprobando...", GRIS
    elif mon.broker_ok and mon.backend_ok:
      servidor, color = "ok", LABEL_COLOR
    elif mon.broker_ok:
      servidor, color = "broker ok, sin api", GRIS
    else:
      servidor, color = "sin respuesta", t.PELIGRO
    self._tarjeta_conexion.filas = [
      ("servidor", servidor, color),
      ("enlace", "ok" if self._enlace else "caído", LABEL_COLOR if self._enlace else t.PELIGRO),
      ("cuenta", self._cuenta or "sin vincular", LABEL_COLOR if self._cuenta else GRIS),
    ]
    # La regla bajo "enlace": continua si vive, discontinua si no (la unica marca grafica del panel).
    self._tarjeta_conexion.pulso = ("enlace", self._enlace)

  def _update_state(self):
    super()._update_state()
    ahora = time.monotonic()
    if ahora - self._ultimo_refresco >= REFRESH_S:
      self._ultimo_refresco = ahora
      self._refrescar()
    self._pintar_tarjetas()

    hecho = ahora < self._desarmado_hasta
    texto = "desarmado" if hecho else "desarmar todo"
    if self._btn_desarmar.text != texto:
      self._btn_desarmar.set_text(texto)
      # El exito es gris: el rojo despues de un exito se lee como fallo.
      self._btn_desarmar.set_value("ninguna orden en curso" if hecho else TXT_DESARMAR)
      self._btn_desarmar.gris = hecho

    if self._resultado_prueba is not None:
      ip, puerto, broker_ok, api_ok = self._resultado_prueba
      self._resultado_prueba = None
      self._probando = False
      self._btn_probar.set_value("broker y api")
      aviso(f"{ip}:{puerto}", f"broker {'ok' if broker_ok else 'sin respuesta'}\napi {'ok' if api_ok else 'sin respuesta'}")

  def _forzar_refresco(self) -> None:
    self._ultimo_refresco = float("-inf")

  # ================================================================ desarmar todo
  @a_salvo("desarmar todo", avisar=True)
  def _desarmar_todo(self) -> None:
    # Funciona con el hilo ORBIT caido: ademas del disparo baja la autoridad en Params.
    fallos = mando.disarm_all()
    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_disarm()
    self._volante.sync()
    self._forzar_refresco()
    if fallos:
      aviso("desarme incompleto", "han fallado:\n" + "\n".join(fallos))
    else:
      self._desarmado_hasta = time.monotonic() + DESARMADO_FEEDBACK_S

  # ================================================================ modo banco
  @a_salvo("modo taller", avisar=True)
  def _pulsar_banco(self) -> None:
    if mando.bench_armed():  # sin cache: es una accion, no un pintado
      self._desarmar_banco()
      return
    gui_app.push_widget(PaginaConfirmacion("modo taller", ajustes.texto_armar_banco(), "desliza para\narmar 5 min",
                                           self._armar_banco))

  @a_salvo("armar el banco", avisar=True)
  def _armar_banco(self) -> None:
    fallos = mando.arm_bench()
    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_local_arm(mando.ARM_REASON_BENCH)
    self._forzar_refresco()
    if fallos:
      aviso("no se pudo armar", "\n".join(fallos))

  @a_salvo("desarmar el banco", avisar=True)
  def _desarmar_banco(self) -> None:
    fallos = mando.disarm_bench()
    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_disarm()
    self._forzar_refresco()
    if fallos:
      aviso("no se pudo desarmar", "\n".join(fallos))

  # ================================================================ ayuda
  @a_salvo("definiciones del panel", avisar=True)
  def _abrir_ayuda(self) -> None:
    if self._ayuda is None:
      self._ayuda = AyudaOrbitMici()
    gui_app.push_widget(self._ayuda)

  # ================================================================ vinculacion
  @a_salvo("QR de vinculacion", avisar=True)
  def _abrir_qr(self) -> None:
    # UNA instancia para toda la vida del proceso: el proceso ui corre con gc.disable()
    # (config_realtime_process) y el dialogo tiene ciclos, asi que uno nuevo por toque
    # dejaba su textura del QR en la GPU para siempre. show_event reinicia su estado.
    if self._qr is None:
      self._qr = OrbitEnrollDialogMici()
    gui_app.push_widget(self._qr)

  @a_salvo("desvincular", avisar=True)
  def _pedir_desvincular(self) -> None:
    texto = ajustes.texto_desvincular(ui_state.params.get(mando.PARAM_OWNER))
    gui_app.push_widget(PaginaConfirmacion("desvincular", texto, "desliza para\ndesvincular", self._desvincular, rojo=True))

  @a_salvo("desvincular", avisar=True)
  def _desvincular(self) -> None:
    # Solo pide el desvinculo al servidor; el estado local lo limpia su respuesta.
    fallos = ajustes.pedir_desvinculo(ui_state.params)
    self._forzar_refresco()
    if fallos:
      aviso("desvínculo incompleto", "\n".join(fallos))

  # ================================================================ servidor
  @a_salvo("editar la IP del servidor", avisar=True)
  def _editar_broker(self, texto: str | None = None) -> None:
    actual = texto if texto is not None else read_broker()[0]

    @a_salvo("guardar la IP del servidor", avisar=True)
    def al_confirmar(escrito: str) -> None:
      escrito = escrito.strip()
      error = ajustes.validar_host(escrito)
      if error:
        # Se reabre con lo escrito y el motivo encima: al cerrar el aviso se corrige.
        self._editar_broker(escrito)
        aviso("ip no válida", error)
        return
      # Solo la clave "broker": puerto, backend y credenciales se conservan.
      if not config_broker.escribir_config({"broker": escrito}):
        aviso("", "no se pudo guardar la ip del servidor")
      self._forzar_refresco()

    dialogo_numerico("ip del servidor orbit...", actual, al_confirmar)

  @a_salvo("probar la conexion", avisar=True)
  def _probar(self) -> None:
    ip, puerto = read_broker()
    if not ip:
      aviso("", "no hay ip configurada")
      return
    if self._probando:
      return
    self._probando = True
    self._btn_probar.set_value("probando...")

    def _correr():
      try:
        broker_ok, api_ok = probar_servidor(ip, puerto, timeout=3.0)
      except Exception:
        broker_ok = api_ok = False
      # Se entrega al hilo de UI: el dialogo solo puede abrirse desde el render.
      self._resultado_prueba = (ip, puerto, broker_ok, api_ok)

    threading.Thread(target=_correr, name="orbit_probe", daemon=True).start()

  # ================================================================ privacidad
  @a_salvo("interruptor de privacidad", avisar=True)
  def _on_privacidad(self, activo: bool) -> None:
    fallos = mando.set_privacy_mute(bool(activo))
    self._tgl_privacidad.set_checked(mando.privacy_muted())
    if fallos:
      aviso("el corte de emisión falló en", "\n".join(fallos))

  # ================================================================ bloqueo del mando remoto
  @a_salvo("bloquear mando remoto", avisar=True)
  def _on_remoto(self, activo: bool) -> None:
    """Activar no pide confirmacion; quitarlo si (vuelve a dar autoridad a la app)."""
    if activo:
      self._aplicar_remoto(True)
      return
    # El toggle ya cambio de posicion: se devuelve a su sitio hasta que se confirme.
    self._tgl_remoto.set_checked(True)
    gui_app.push_widget(PaginaConfirmacion("mando remoto", "¿Volver a aceptar órdenes remotas?", "desliza para\naceptar órdenes",
                                           lambda: self._aplicar_remoto(False)))

  @a_salvo("bloquear mando remoto", avisar=True)
  def _aplicar_remoto(self, apagar: bool) -> None:
    fallos = ajustes.cambiar_remoto(ui_state.params, apagar)
    self._tgl_remoto.set_checked(ajustes.remoto_apagado(ui_state.params))
    self._forzar_refresco()
    if fallos:
      aviso("el bloqueo falló en", "\n".join(fallos))

  # ================================================================ valores seguros
  @a_salvo("restablecer valores seguros", avisar=True)
  def _pedir_valores_seguros(self) -> None:
    gui_app.push_widget(PaginaConfirmacion("valores seguros", ajustes.texto_valores_seguros(), "desliza para\nrestablecer",
                                           self._valores_seguros))

  @a_salvo("restablecer valores seguros", avisar=True)
  def _valores_seguros(self) -> None:
    fallos = ajustes.aplicar_valores_seguros(ui_state.params)
    guard = getattr(ui_state, "orbit_bench_guard", None)
    if guard is not None:
      guard.note_disarm()
    self._volante.sync()
    self._forzar_refresco()
    if fallos:
      aviso("restablecimiento incompleto", "\n".join(fallos))

  # ================================================================ ciclo de vida
  def show_event(self):
    super().show_event()
    self._forzar_refresco()
    self._tgl_privacidad.set_checked(mando.privacy_muted())
    self._tgl_remoto.set_checked(ajustes.remoto_apagado(ui_state.params))
    # El sondeo del servidor (TCP + HTTP cada 5 s) solo corre con el panel abierto.
    if self._monitor is None:
      self._monitor = ServerMonitor()

  def hide_event(self):
    super().hide_event()
    if self._monitor is not None:
      self._monitor.stop()
      self._monitor = None
