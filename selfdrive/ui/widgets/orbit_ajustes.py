"""
Logica PURA de los ajustes ORBIT, compartida por las dos pantallas del comma:

  * UI grande (comma 3 / 3X): sunnypilot/layouts/settings/orbit_panel.py y
    orbit_sub_layouts/ (steer_mode, server_settings, advanced_settings),
    widgets/orbit_enroll_dialog.py.
  * UI mici (comma 4, 536x240): sunnypilot/mici/layouts/orbit*.py y
    sunnypilot/mici/widgets/orbit_*.py.

Aqui no se pinta nada (no se importa pyray): textos, validaciones y escrituras de Params
viven en UN sitio para que las dos pantallas hagan exactamente lo mismo, y para que los
tests corran sin ventana ni build (selfdrive/ui/tests/test_orbit_mici_ajustes.py).

Las funciones que escriben reciben `params` como argumento (la UI pasa ui_state.params)
para poder probarlas con un Params falso.
"""
import functools
import json
import os
import re
import tempfile
import time
from collections.abc import Callable

from openpilot.common.basedir import BASEDIR
from openpilot.common.swaglog import cloudlog
from openpilot.orbit import enroll_v2
from openpilot.orbit import mando_local
from openpilot.orbit import telemetria_grupos as grupos
from openpilot.selfdrive.ui.widgets import orbit_mando as mando
from openpilot.system.ui.lib.multilang import tr


def _ahora_ms() -> int:
  # Reloj de PARED: OrbitLastPublish, OrbitEnrollExpiry y los payloads MQTT viajan en
  # epoch. time_ns y no time(): `time.time` esta prohibido por ruff en este arbol.
  return time.time_ns() // 1_000_000


# ======================================================================== a salvo
def a_salvo(etiqueta: str, aviso: Callable[[str], None] | None = None):
  """Decorador: la funcion NUNCA deja salir una excepcion al bucle de la UI.

  El bucle de render no envuelve `widget.render` en ningun try y los callbacks de los
  botones corren dentro de el: una excepcion mata el proceso `ui` entero (bucle de
  reinicios si depende de un estado que sobrevive en Params, como el armado). Ver la
  historia completa en orbit_panel._a_salvo.

  `aviso(etiqueta)` se llama tras el fallo en las acciones del usuario: cada pantalla
  lo cuenta con su propio dialogo. Los refrescos van sin aviso (solo log).
  """
  def decorador(fn):
    @functools.wraps(fn)
    def envoltura(*args, **kwargs):
      try:
        return fn(*args, **kwargs)
      except Exception:
        cloudlog.exception(f"[Orbit/UI] {etiqueta}: excepcion no controlada")
        if aviso is not None:
          try:
            aviso(etiqueta)
          except Exception:
            cloudlog.exception("[Orbit/UI] no se pudo mostrar el aviso de fallo")
        return None
    return envoltura
  return decorador


# ======================================================================== servidor
_ETIQUETA_HOST = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def validar_host(texto: str) -> str:
  """'' si `texto` vale como direccion del broker; si no, el motivo para la pantalla.

  Solo rechaza lo CLARAMENTE invalido: una IPv4 con 4 numeros de 0 a 255, o un nombre
  de maquina de etiquetas [A-Za-z0-9-] separadas por puntos (max. 253). Ni esquema ni
  puerto: config_broker guarda el host y el puerto va en su propia clave, asi que
  "1.2.3.4:1883" se guardaba entero como host y el broker nunca conectaba.
  """
  host = (texto or "").strip()
  if not host:
    return tr("la dirección está vacía")
  if "://" in host:
    return tr("sin http:// ni otro esquema")
  if any(c.isspace() for c in host):
    return tr("sin espacios")
  if ":" in host or "/" in host:
    return tr("sin puerto ni ruta")
  if len(host) > 253:
    return tr("máximo 253 caracteres")
  etiquetas = host.split(".")
  if all(e.isascii() and e.isdigit() for e in etiquetas):
    if len(etiquetas) != 4 or any(int(e) > 255 for e in etiquetas):
      return tr("escribe 4 números del 0 al 255, p. ej. 192.168.1.20")
    return ""
  if not all(_ETIQUETA_HOST.match(e) for e in etiquetas):
    return tr("solo letras, números, '-' y '.'")
  return ""


# ======================================================================== enlace / cuenta
LINK_STALE_SECONDS = 30.0


def edad_publicacion(raw, ahora_s: float) -> float:
  """Segundos desde el ultimo publish MQTT (OrbitLastPublish, epoch s); inf si no hay dato."""
  try:
    if raw:
      return max(0.0, ahora_s - float(raw))
  except (TypeError, ValueError):
    pass
  return float("inf")


def enlace_orbit(params) -> bool:
  """ENLACE: OrbitConnected y un publish de menos de 30 s.

  El heartbeat MQTT escribe OrbitLastPublish cada ~3 s; sin dato fresco el enlace se da
  por caido aunque OrbitConnected quedara en True (el proceso pudo morir sin escribir el
  False de despedida).
  """
  try:
    conectado = bool(params.get_bool("OrbitConnected"))
    return conectado and edad_publicacion(params.get("OrbitLastPublish"), time.time_ns() / 1e9) <= LINK_STALE_SECONDS
  except Exception:
    return False


def etiqueta_cuenta(owner, rol) -> str:
  """'Adrian, superadmin' (primer nombre, 12 car. max, y el rol si se conoce); '' sin dueno."""
  owner = owner.strip() if isinstance(owner, str) else ""
  if not owner:
    return ""
  nombre = owner.split()[0][:12]
  rol_txt = mando.rol_etiqueta(rol)
  return f"{nombre}, {rol_txt}" if rol_txt else nombre


def url_enrolamiento(dongle_id, codigo) -> str:
  """Carga del QR de vinculacion. El backend y la app parsean exactamente este formato."""
  return enroll_v2.url_enrolamiento(dongle_id or "", codigo or "")


def reloj_sincronizado(st) -> bool:
  """Vista del mando (ui_state.orbit_command): solo se acusa al reloj si el plano esta vivo y lo dice."""
  return st is None or not st.available or bool(st.clock_synced)


def texto_sin_codigo(reloj_sincronizado: bool) -> str:
  """Lo que se pinta en lugar del QR cuando no hay codigo: sin reloj valido el firmware
  no anuncia (ni genera token), y decirlo evita un 'no pasa nada' sin explicacion."""
  return tr("esperando código...") if reloj_sincronizado else tr("Sincronizando la hora del comma...")


# ======================================================================== mando remoto
PARAM_REMOTE_OFF = mando_local.PARAM_REMOTE_OFF
PARAM_REMOTE_LOG = mando_local.PARAM_REMOTE_LOG

_FASES_TXT = {
  "applied": "aplicada", "rejected": "rechazada", "failed": "falló", "expired": "caducada",
  "superseded": "sustituida", "held": "retenida", "ignored": "ignorada",
}


def remoto_apagado(params) -> bool:
  return mando_local.remoto_apagado(params)


def cambiar_remoto(params, apagar: bool) -> list[str]:
  """Escribe OrbitRemoteOff y DESPUES, al apagar, desarma todo (orden que importa: con el
  Param ya puesto, nada nuevo se acepta mientras se desarma). Devuelve los fallos."""
  fallos: list[str] = []
  try:
    params.put_bool(PARAM_REMOTE_OFF, bool(apagar), True)   # bloqueante: el Param ya esta antes de desarmar
  except Exception:
    cloudlog.exception(f"[Orbit/UI] cambiar_remoto: fallo {PARAM_REMOTE_OFF}")
    fallos.append(PARAM_REMOTE_OFF)
  if apagar:
    fallos += mando.disarm_all()
    # Una peticion de modo de volante ya pendiente se cierra ahora como REMOTE_OFF: la
    # pantalla no puede seguir mostrando 'la app pide...' con el mando bloqueado.
    from openpilot.selfdrive.ui.widgets import orbit_peticion_modo as peticion   # import circular
    try:
      peticion.tick(params)
    except Exception:
      cloudlog.exception("[Orbit/UI] cambiar_remoto: fallo al cerrar la peticion de modo")
      fallos.append(peticion.PARAM)
  return fallos


def texto_remoto_off() -> str:
  return tr("Mientras esté activo, el coche ignora las órdenes y ajustes que lleguen desde la app o el servidor. " +
            "«Desarmar todo» sigue funcionando. Solo se puede quitar desde esta pantalla.")


# Nombres de persona para el registro: el conductor no ve identificadores internos (verbos,
# codigos de motivo, origenes). Lo desconocido cae en un texto neutro, nunca en el codigo crudo.
_VERBOS_TXT = {
  "disarm_all": "Desarmar todo", "set_mode": "Cambio de modo", "bookmark": "Marcador",
  "healthcheck": "Comprobación", "location_now": "Posición", "cruise_delta": "Ajuste de crucero",
  "cruise_button": "Botón de crucero", "follow_distance": "Distancia de seguimiento",
  "mads": "Dirección asistida", "experimental": "Modo experimental", "dec": "Modo experimental dinámico",
  "nnlc": "Dirección neuronal", "openpilot_enable": "Activar openpilot", "device_admin": "Gestión del comma",
  "steer_mode_request": "Modo de volante", "lane_change": "Cambio de carril",
  "assisted_decel": "Frenada asistida", "torque_mode": "Modo de volante", "steering_pulse": "Pulso de dirección",
  "physical_control": "Control directo", "cfg": "Configuración", "cam": "Cámara", "roundabout": "Rotondas",
  "speed_increment": "Paso de velocidad",
}
_MOTIVOS_TXT = {
  "TYPE": "orden mal formada", "RANGE": "valor fuera de rango", "MODE": "modo insuficiente",
  "DUPLICATE": "repetida", "EXPIRED": "llegó tarde", "CLOCK": "hora sin sincronizar",
  "UNSUPPORTED_PLATFORM": "no vale para este coche", "UNSUPPORTED_VERB": "no disponible",
  "BUSY": "había otra en curso", "SUPERSEDED": "sustituida por otra", "LINK": "enlace caído",
  "INTERNAL": "fallo del comma", "REMOTE_OFF": "mando remoto bloqueado", "OFFROAD": "coche apagado",
  "NO_KEY": "sin clave de seguridad",
  "GATE_ENGAGED": "openpilot no activo", "GATE_LAT_ACTIVE": "dirección no activa",
  "GATE_LONG_ACTIVE": "aceleración no activa", "GATE_SPEED_RANGE": "velocidad no permitida",
  "GATE_DRIVER_IDLE": "el conductor intervino", "GATE_DRIVER_PRESENT": "conductor no listo",
  "GATE_CALIBRATED": "calibración pendiente", "GATE_NOT_DEGRADED": "sistema degradado",
  "GATE_LINK_FRESH": "enlace sin datos recientes", "GATE_CLOCK_SYNCED": "hora sin sincronizar",
}


def lineas_registro_remoto(raw) -> list[str]:
  """Una linea por orden, la mas nueva primero: '14:03:22  Cambio de carril  rechazada (mando remoto bloqueado)'.

  Nunca lanza: un registro roto o ausente da lista vacia y una fila rota se salta.
  """
  try:
    if isinstance(raw, bytes):
      raw = raw.decode("utf-8", "replace")
    datos = json.loads(raw) if raw else []
  except Exception:
    return []
  if not isinstance(datos, list):
    return []
  lineas = []
  for d in datos[:mando_local.REGISTRO_MAX]:
    try:
      hora = time.strftime("%H:%M:%S", time.localtime(int(d["t"])))
      fase = _FASES_TXT.get(d["f"], str(d["f"]))
      verbo = _VERBOS_TXT.get(d["v"], "Orden desconocida")
      motivo = f" ({_MOTIVOS_TXT[d['r']]})" if d.get("r") in _MOTIVOS_TXT else ""
      veces = f"  x{d['n']}" if int(d.get("n", 1)) > 1 else ""
      lineas.append(f"{hora}  {verbo}  {fase}{motivo}{veces}")
    except Exception:
      continue
  return lineas


def texto_caducidad(expiry_raw, ahora_ms: int) -> str:
  """'caduca en M:SS' a partir de OrbitEnrollExpiry (epoch ms); '' si no hay caducidad."""
  try:
    expiry_ms = int(expiry_raw or 0)
  except (TypeError, ValueError):
    expiry_ms = 0
  if expiry_ms <= 0:
    return ""
  restante = max(0, int(expiry_ms / 1000 - ahora_ms / 1000))
  minutos, segundos = divmod(restante, 60)
  return f"caduca en {minutos}:{segundos:02d}"


PARAM_UNLINK_REQUEST = "OrbitUnlinkRequest"
PARAM_UNLINK_RESULT = "OrbitUnlinkResult"

# Por que fallo el desvinculo, en lenguaje de persona (codigos de contrato C4/C5).
_NO_RECONOCE = "No se pudo desvincular. El servidor no reconoce este comma. Desvincúlalo desde la app, en Cuenta, Coches."
_MOTIVOS_DESVINCULO = {
  "no_key": "No se pudo desvincular. Este comma se vinculó sin clave de dispositivo. Desvincúlalo desde la app, en Cuenta, Coches.",
  "no_nonce": "No se pudo desvincular. Conecta el comma a internet y vuelve a intentarlo.",
  "bad_signature": _NO_RECONOCE,
  "bad_nonce": _NO_RECONOCE,
  "bad_request": _NO_RECONOCE,
}


def texto_desvincular(owner) -> str:
  """Texto de la confirmacion de las dos pantallas: a quien esta vinculado y que pasa."""
  owner = owner.strip() if isinstance(owner, str) else ""
  quien = owner or "una cuenta ORBIT"
  # Frases de <= 72 caracteres: en el comma 4 cada tarjeta lleva frases enteras (guia 5.3).
  return (f"Este comma está vinculado a {quien}. Si lo desvinculas, dejará de salir en la app ORBIT de " +
          "esa cuenta. Para volver a usarlo, vincúlalo otra vez con el QR.")


def pedir_desvinculo(params) -> list[str]:
  """Pide al comma que se desvincule en el SERVIDOR (contrato C5). Devuelve los fallos.

  NO borra el estado local (OrbitClaimed, OrbitOwner...): si se borrara, el anuncio de
  enroll haria que el backend, que aun ve la vinculacion, la restaurara solo. El estado
  local lo limpia el enroll_ack claimed:false cuando el servidor la libera de verdad. El
  resultado anterior se limpia ANTES de poner la peticion para no leer uno rancio.
  """
  fallos: list[str] = []
  for clave, paso in (
    (PARAM_UNLINK_RESULT, lambda: params.remove(PARAM_UNLINK_RESULT)),
    (PARAM_UNLINK_REQUEST, lambda: params.put_bool(PARAM_UNLINK_REQUEST, True, True)),
  ):
    try:
      paso()
    except Exception:
      cloudlog.exception(f"[Orbit/UI] desvincular: fallo {clave}")
      fallos.append(clave)
  return fallos


def estado_desvinculo(params, enlace: bool) -> str:
  """Texto para la baldosa/boton mientras hay peticion en curso; '' si no la hay."""
  try:
    if not params.get_bool(PARAM_UNLINK_REQUEST):
      return ""
  except Exception:
    return ""
  # Sin enlace la peticion espera igual: se dice lo mismo, en gris, no como un aviso (guia visual §5.5).
  return "desvinculando..."


def texto_fallo_desvinculo(resultado) -> str:
  """Texto del fallo de un OrbitUnlinkResult (JSON, bytes o dict); '' si no fallo o no se lee."""
  try:
    if isinstance(resultado, (bytes, str)):
      resultado = json.loads(resultado)
    if not isinstance(resultado, dict) or resultado.get("ok") is not False:
      return ""
    motivo = resultado.get("reason")
  except (ValueError, TypeError):
    return ""
  return _MOTIVOS_DESVINCULO.get(motivo, "No se pudo desvincular. Desvincúlalo desde la app, en Cuenta, Coches.")


def fallo_desvinculo_pendiente(params) -> str:
  """Si el ultimo desvinculo fallo, devuelve su texto UNA sola vez (borra el resultado)."""
  try:
    texto = texto_fallo_desvinculo(params.get(PARAM_UNLINK_RESULT))
    if texto:
      params.remove(PARAM_UNLINK_RESULT)
    return texto
  except Exception:
    cloudlog.exception("[Orbit/UI] no se pudo leer OrbitUnlinkResult")
    return ""


# ======================================================================== mando
def lineas_mando(st) -> list[tuple[str, str, str]]:
  """Las tres lineas del estado del mando (solo con el plano vivo: `st.available`).

  (etiqueta, valor, tono) con tono 'ok' | 'aviso' | 'peligro' | 'normal'. Cada pantalla
  pone el color. Mismo criterio que la tarjeta de mando de la UI grande: nada rancio en
  verde, el enlace caido en rojo, la ultima orden en rojo si acabo mal.
  """
  modo = (tr("Modo"), st.mode_label, "ok" if st.mode == "observer" else "aviso")

  if not st.link_ok:
    enlace = (tr("Enlace"), tr("Caído"), "peligro")
  elif not st.clock_synced:
    # Sin reloj sincronizado el router rechaza todo verbo de taller: decirlo evita el
    # "el coche no responde y no se por que".
    enlace = (tr("Enlace"), tr("OK, reloj sin sincronizar"), "aviso")
  else:
    enlace = (tr("Enlace"), tr("OK"), "ok")

  if st.last_ack_phase != "none":
    texto = f"{st.active_verb or '-'}: {st.phase_label}"
    if st.last_reason:
      texto += f"  ({st.last_reason})"
  else:
    texto = tr("ninguna")
  ultimo = (tr("Última orden"), texto, "peligro" if st.phase_is_bad else "normal")
  return [modo, enlace, ultimo]


# ======================================================================== banco
def texto_armar_banco() -> str:
  # El texto dice que habilita mandos REMOTOS porque es exactamente lo que hace, y es el
  # dato que decide si armar o no. Elegir el modo de volante en la pantalla no necesita
  # esto: eso va por OrbitSteerModeLocal y no abre nada por MQTT.
  # Sin «5 minutos» en la pregunta: en el comma 4 la tarjeta partia el numero de su unidad
  # (el espacio duro no lo respeta el troceo de lineas). La frase siguiente ya dice cuanto dura.
  return tr("¿Armar el modo taller?\n\n" +
            "Durante 5 minutos la app podrá mover el volante. Ármalo solo con el coche parado " +
            "y contigo delante.\n\n" +
            "Se desarma a los 5 minutos, al pasar de 5 km/h o al apagar el coche.")


def texto_estado_banco(armado: bool, restante_s: float) -> str:
  if armado:
    return tr("Armado") + f", quedan {int(restante_s)} s"
  return tr("Desarmado. Las órdenes de taller se rechazan.")


# ======================================================================== volante
# Indice del boton -> valor de SteerTorqueMode. El orden replica el Qt original:
#   ['COMMA', 'COMMA+JETSON', 'JETSON', 'TEST MAX'] -> 0, 3, 1, 2
# (etiquetas cortas: 'MODELO COMMA' desbordaba los 320 px del boton de la UI grande)
# ponytail: siguen en mayusculas porque orbit_peticion_modo.NOMBRES (FW-C) y sus tests de
# orbit/test dependen de ellas; pasan a sentence case con el selector de 3 + «Test max» (FW-B).
MODE_BUTTONS = ["COMMA", "COMMA+JETSON", "JETSON", "TEST MAX"]
INDEX_TO_MODE = {0: 0, 1: 3, 2: 1, 3: 2}
MODE_TO_INDEX = {v: k for k, v in INDEX_TO_MODE.items()}
MODE_NAMES = {0: "MODELO COMMA", 1: "JETSON", 2: "TEST MAX", 3: "COMMA + JETSON"}

# Modos cuyo override de torque controlsd solo aplica con autorizacion vigente.
MODES_REQUIRING_BENCH = (1, 2)

TORQUE_STALE_SECONDS = 3.0

PARAM_APPLY_TARGET = "JetsonObstacleApplyTarget"


def texto_estado_volante(modo: int, objetivo, armado: bool, restante_s: float, local: bool) -> str:
  """Estado REAL del volante, no el boton pulsado.

  Sin esto el selector se queda marcando JETSON, el volante lo lleva el modelo Comma
  porque no hay autorizacion, y nada en pantalla lo explica. Para los modos 1 y 2
  controlsd acepta CUALQUIERA de las dos: el banco armado u OrbitSteerModeLocal (`local`,
  lo que escribe el selector de esta pantalla). Mirar solo el banco decia "sin efecto"
  justo despues de elegir JETSON aqui, con la Jetson llevando el volante.
  """
  if modo == 0:
    return tr("par del modelo interno")
  if modo == 3:
    tgt_label = tr("par directo") if objetivo == "torque" else tr("curvatura")
    return tr("esquive con") + f" {tgt_label}"
  if local:
    return tr("activo, elegido en pantalla")
  if armado:
    return tr("activo, taller armado") + f" ({int(restante_s)}s)"
  return tr("sin efecto: taller sin armar, manda Comma")


def confirmacion_modo(modo: int) -> tuple[str, str]:
  """(texto, boton de confirmar) del cambio al modo `modo`.

  Guia 5.5: como mucho tres frases, sin repetir el titulo (lo pone cada pantalla) ni
  «¿Continuar?» (lo dice el boton). Lo comparten el selector local y el aviso remoto.
  """
  if modo == 0:
    return (tr("El volante usará el modelo interno de openpilot.\n\n" +
               "Es la opción más segura y probada."),
            tr("Cambiar a modelo Comma"))
  if modo == 1:
    return (tr("El volante obedecerá al par directo que calcule la Jetson.\n\n" +
               "Comprueba que la Jetson envía par directo y ten las manos en el volante.\n\n" +
               "Dura hasta volver a Comma o apagar el coche."),
            tr("Usar Jetson"))
  if modo == 2:
    return (tr("El volante girará con toda su fuerza a la derecha hasta pasar de 5 km/h.\n\n" +
               "Solo en circuito y con las manos en el volante.\n\n" +
               "También se retira al apagar el coche."),
            tr("Activar test max"))
  return (tr("El volante usa el modelo Comma y esquiva si la Jetson ve un obstáculo.\n\n" +
             "Necesita la Jetson conectada y su detector de obstáculos en marcha.\n\n" +
             "No hace falta armar el modo taller."),
          tr("Activar Comma + Jetson"))


def texto_esquive_curvatura() -> tuple[str, str, str]:
  """Paso 1 de COMMA+JETSON: (texto, curvatura, otra opcion)."""
  return (tr("Comma + Jetson: ¿cómo debe esquivar la Jetson?\n\n" +
             "Curvatura suma un desvío a la curvatura deseada. Es más suave y predecible " +
             "(recomendado).\n\n" +
             "Otra opción esquiva con par directo (en pruebas)."),
          tr("Curvatura (recomendado)"), tr("Otra opción (par directo)"))


def texto_esquive_torque(cancelar: str = "Pulsa Cancelar para no cambiar nada.") -> tuple[str, str]:
  """Paso 2 de COMMA+JETSON: (texto, confirmar par directo).

  `cancelar` dice como se cancela en cada pantalla: el comma 4 no tiene boton Cancelar,
  se desliza hacia abajo.
  """
  return (tr("¿Esquivar con par directo?\n\n" +
             "Reacciona más fuerte y más rápido. En pruebas.\n\n") + tr(cancelar),
          tr("Usar par directo"))


def _dongle(params) -> str | None:
  dongle = params.get("DongleId")
  return dongle if dongle else None


def aplicar_modo_volante(params, modo: int) -> None:
  """Commit del selector de volante: modo, autorizacion presencial y buzon MQTT.

  SteerTorqueMode es INT: put(str) lanza TypeError. block=True: la autorizacion de la
  linea siguiente y el texto de estado leen este valor de inmediato.

  AUTORIZACION PRESENCIAL, no armado de banco: OrbitBenchArmed es lo que el router mira
  para dejar pasar los verbos FISICOS por MQTT, asi que elegir JETSON delante del coche
  no puede armarlo (ver la cabecera de steer_mode.py). OrbitSteerModeLocal lo acepta
  controlsd para los modos 1 y 2 y NO habilita ningun verbo remoto. Va DESPUES del modo.
  """
  params.put(mando.PARAM_STEER_MODE, modo, True)
  mando.set_steer_local(modo in MODES_REQUIRING_BENCH)

  dongle = _dongle(params)
  if dongle:
    payload = {
      "dongle_id": dongle,
      "steer_torque_mode": modo,
      "source": "comma_ui",
      "timestamp": str(_ahora_ms()),
    }
    params.put("SteerTorqueModeMqttPayload", json.dumps(payload))


def fijar_objetivo_esquive(params, objetivo: str) -> None:
  """Como esquiva la Jetson en COMMA+JETSON: 'curvature' (recomendado) o 'torque' (beta)."""
  params.put(PARAM_APPLY_TARGET, objetivo)
  dongle = _dongle(params)
  if dongle:
    payload = {
      "dongle_id": dongle,
      "apply_target": objetivo,
      "source": "comma_ui",
      "ts": str(_ahora_ms()),
    }
    params.put("JetsonObstacleApplyTargetMqttPayload", json.dumps(payload))


# ======================================================================== telemetria
# Submenu ORBIT > Telemetria: que grupos de datos manda el dispositivo a la app (modelo en
# orbit/telemetria_grupos.py). `silenciado` es `mando.privacy_muted()`: lo lee la pantalla
# una vez por refresco y se pasa a mano para que estos helpers no abran ficheros.

def grupo_bloqueado(grupo, silenciado: bool) -> bool:
  """La posicion no se toca con el interruptor de privacidad puesto: ya la esta cortando el."""
  return bool(grupo.posicion and silenciado)


def encendido_grupo(params, grupo, silenciado: bool) -> bool:
  """Estado del interruptor del grupo. NUNCA `get_bool`: lee "sin configurar" como OFF.

  Con la privacidad puesta la posicion se pinta OFF aunque su toggle diga otra cosa: el
  interruptor de privacidad es quien manda y pintarla ON seria mentir."""
  return grupos.grupo_activo(params, grupo) and not grupo_bloqueado(grupo, silenciado)


def descripcion_grupo(grupo, silenciado: bool) -> str:
  if grupo_bloqueado(grupo, silenciado):
    return tr("Apagada por el interruptor de privacidad. Quítalo para activarla.")
  return tr(grupo.descripcion)


def cambiar_grupo(params, grupo, encendido: bool, silenciado: bool) -> list[str]:
  """Escribe el grupo entero (v1 y v2). Devuelve los params que fallaron.

  La posicion con la privacidad puesta no se escribe: la fila ya sale deshabilitada, esto
  es el cinturon (encenderla aqui dejaria gpsLocation_toggle a True bajo el mute)."""
  if grupo_bloqueado(grupo, silenciado):
    return []
  return grupos.fijar_grupo(params, grupo, encendido)


def texto_ahorro_movil() -> str:
  return tr("Si la red móvil está marcada como de pago, baja al perfil de ahorro y deja de enviar " +
            "percepción, alertas, marcha y pedales. Apagado por defecto.")


def cambiar_ahorro_movil(params, encendido: bool) -> list[str]:
  """Escribe OrbitAhorroRedMovil (bloqueante: la pantalla relee justo despues). Devuelve los fallos."""
  try:
    params.put_bool(grupos.PARAM_AHORRO_MOVIL, bool(encendido), True)
  except Exception:
    cloudlog.exception("[Orbit/UI] telemetria: fallo el ahorro en red movil")
    return [grupos.PARAM_AHORRO_MOVIL]
  return []


# ======================================================================== valores seguros
def texto_valores_seguros() -> str:
  return tr("¿Volver a los valores seguros de conducción?\n\n" +
            "- Modo de volante: Comma\n" +
            "- Modo taller y modo del mando: desarmados\n" +
            "- Frenado de emergencia remoto: apagado\n" +
            "- Cambios de carril forzados pendientes: borrados\n" +
            "- Pulso de dirección remoto: borrado\n" +
            "- Alertas de comunicación: visibles\n\n" +
            "No toca el servidor, la telemetría ni la Jetson. Tampoco el interruptor de privacidad.")


def aplicar_valores_seguros(params) -> list[str]:
  """Siete grupos de escrituras INDEPENDIENTES, cada una con su try y su log.

  Antes era un unico try/except global: si la primera fallaba (`put("SteerTorqueMode", 0)`,
  la mas propensa: un put con el tipo equivocado lanza TypeError) las demas ni se
  intentaban y el usuario no se enteraba. Un boton de panico que falla mudo es peor que
  no tener boton. Devuelve las claves que fallaron, ordenadas y sin repetir.
  """
  fallos: list[str] = []

  def _paso(clave, fn):
    try:
      fn()
    except Exception:
      cloudlog.exception(f"[Orbit/UI] valores seguros: fallo {clave}")
      fallos.append(clave)

  # block=True: la escritura por defecto es asincrona y el resultado que se pinta justo
  # despues seria el valor viejo (ver la nota de orbit_mando._BLOQUEANTE).
  # 1. fuente de torque del volante (INT: put exige int nativo)
  _paso(mando.PARAM_STEER_MODE, lambda: params.put(mando.PARAM_STEER_MODE, 0, True))
  # 2. frenado remoto
  _paso("brutebreak_active", lambda: params.put_bool("brutebreak_active", False, True))
  # 3. cambios de carril forzados pendientes
  _paso("ForceLaneChangeLeft", lambda: params.put_bool("ForceLaneChangeLeft", False, True))
  _paso("ForceLaneChangeRight", lambda: params.put_bool("ForceLaneChangeRight", False, True))
  # 4. pulso de direccion remoto
  _paso("orbit_steering_pulse", lambda: params.remove("orbit_steering_pulse"))
  # 5. autoridad del mando: armado de banco y modo, por si el hilo ORBIT esta caido
  fallos.extend(mando.disarm_bench())
  _paso(mando.PARAM_COMMAND_MODE, lambda: params.put(mando.PARAM_COMMAND_MODE, 0, True))
  # 6. HUD de adelantamiento: sic_adelantar es PERSISTENT y su overlay ya no existe;
  #    apagarlo aqui evita dejar un flag encendido que nadie puede volver a apagar.
  _paso("sic_adelantar", lambda: params.put_bool("sic_adelantar", False, True))
  # 7. volcado de mensajes MQTT a /tmp (era PERSISTENT|BACKUP y sobrevivia a reinicios)
  _paso("modo_debug", lambda: params.put_bool("modo_debug", False, True))
  return sorted(set(fallos))


# ======================================================================== jetson
# Valores por defecto, los del Qt viejo.
CONFIG_DEFAULTS = {
  "jetson_enabled": False,
  "jetson_ip": "192.168.1.50",
  "comma_ip": "127.0.0.1",
  "jetson_img_port": 5555,
  "jetson_torque_port": 5556,
  "jpeg_quality": 80,
}

# Campos de red editables en pantalla: (clave, es_entero, (min, max) | None, paso | None).
CAMPOS_JETSON = (
  ("jetson_ip", False, None, None),
  ("comma_ip", False, None, None),
  ("jetson_img_port", True, None, None),
  ("jetson_torque_port", True, None, None),
  ("jpeg_quality", True, (10, 95), 10),
)


def ruta_config_jetson() -> str:
  """orbit/config_jetson.json en BASEDIR, con /data/openpilot de respaldo."""
  candidatas = (os.path.join(BASEDIR, "orbit", "config_jetson.json"),
                "/data/openpilot/orbit/config_jetson.json")
  for ruta in candidatas:
    if os.path.exists(ruta):
      return ruta
  return candidatas[0]  # se crea al guardar


def cargar_config_jetson(ruta: str) -> dict:
  config = dict(CONFIG_DEFAULTS)
  try:
    with open(ruta) as f:
      data = json.load(f)
    if isinstance(data, dict):
      config.update(data)
  except (OSError, ValueError):
    pass
  return config


def guardar_config_jetson(ruta: str, config: dict, params) -> bool:
  """Escritura atomica (tempfile + os.replace) con `_version`, JetsonConfigChanged y payload MQTT.

  Modifica `config` (anade `_version`). False si no se pudo escribir el fichero; en ese
  caso no se levanta el flag ni se publica nada.
  """
  version_ms = _ahora_ms()
  config["_version"] = str(version_ms)
  directorio = os.path.dirname(ruta)
  try:
    os.makedirs(directorio, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directorio, suffix=".tmp")
    try:
      with os.fdopen(fd, "w") as f:
        json.dump(config, f, indent=4, sort_keys=True)
      os.replace(tmp, ruta)
    except Exception:
      if os.path.exists(tmp):
        os.remove(tmp)
      raise
  except OSError:
    return False

  params.put_bool("JetsonConfigChanged", True)
  dongle = _dongle(params)
  if dongle:
    payload = {
      "dongle_id": dongle,
      "jetson_enabled": bool(config.get("jetson_enabled", False)),
      "jetson_ip": str(config.get("jetson_ip", "")),
      "comma_ip": str(config.get("comma_ip", "")),
      "jetson_img_port": int(config.get("jetson_img_port", 5555)),
      "jetson_torque_port": int(config.get("jetson_torque_port", 5556)),
      "jpeg_quality": int(config.get("jpeg_quality", 80)),
      "source": "comma_ui",
      "timestamp": str(_ahora_ms()),
      "_version": str(version_ms),
    }
    params.put("JetsonConfigMqttPayload", json.dumps(payload))
  return True


def parsear_campo(texto: str, es_entero: bool, rango: tuple[int, int] | None = None, paso: int | None = None):
  """Valor a guardar, o None si la entrada se ignora (vacia o no numerica)."""
  texto = (texto or "").strip()
  if not texto:
    return None
  if not es_entero:
    return texto
  try:
    valor = int(texto)
  except ValueError:
    return None
  if paso:
    valor = int(round(valor / paso) * paso)
  if rango:
    valor = max(rango[0], min(rango[1], valor))
  return valor


def texto_torque(torque_raw, ts_raw, ahora_s: float) -> str:
  """JetsonTorque con signo, o '-' si no hay dato o tiene mas de 3 s (sello de pared)."""
  if not torque_raw:
    return "-"
  try:
    if not ts_raw or ahora_s - float(ts_raw) > TORQUE_STALE_SECONDS:
      return "-"
    return f"{float(torque_raw):+.2f}"
  except (TypeError, ValueError):
    return "-"


def texto_obstaculo(raw) -> str:
  """SI/NO a partir del JSON {"obstacle": bool, ...} de JetsonObstaclePulse."""
  if raw:
    try:
      payload = json.loads(raw)
      if isinstance(payload, dict) and payload.get("obstacle"):
        return tr("SI")
    except (TypeError, ValueError):
      pass
  return tr("NO")


# ======================================================================== dialogos
def html_dialogo(mensaje: str) -> str:
  """«Pregunta\n\ncuerpo» -> HTML: la pregunta en <h2>, los parrafos en <p> y las lineas «- x» en <ul>."""
  pregunta, *resto = [p.strip() for p in mensaje.split("\n\n") if p.strip()]
  html = f"<h2>{pregunta}</h2>"
  for parrafo in resto:
    lineas = parrafo.split("\n")
    if all(ln.startswith("- ") for ln in lineas):
      html += "<ul>" + "".join(f"<li>{ln[2:]}</li>" for ln in lineas) + "</ul>"
    else:
      html += "".join(f"<p>{ln}</p>" for ln in lineas)
  return html


def dialogo_orbit(mensaje: str, confirmar: str, estilo=None, cancelar: str | None = None, rich: bool = False, callback=None):
  """ConfirmDialog de ORBIT con el boton de confirmar en el estilo pedido.

  ConfirmDialog pinta SIEMPRE el boton de confirmar en PRIMARY (verde) y ese verde esta
  reservado a «el coche lo confirmo»: aqui se le cambia el estilo sin tocar system/ui.
  `estilo`: ButtonStyle.DANGER (desvincular, test max), ButtonStyle.ACTION (armar taller,
  restablecer) o None para dejar el de siempre. `cancelar=""` da un unico boton (informativo).
  Import tardio: este modulo es logica pura y los tests corren sin pyray.
  """
  from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog
  # «Pregunta\n\ncuerpo»: ConfirmDialog lo pinta todo al mismo tamano y centrado. Se maqueta aparte
  # (pregunta grande en negrita, cuerpo normal a la izquierda, listas con vinetas) sin tocar system/ui.
  maquetar = not rich and "\n\n" in mensaje
  dialogo = ConfirmDialog(html_dialogo(mensaje) if maquetar else mensaje, confirmar, cancelar,
                          rich=rich or maquetar, callback=callback)
  if maquetar:
    from openpilot.system.ui.widgets.html_render import HtmlRenderer, ElementType
    from openpilot.system.ui.widgets.scroller_tici import Scroller
    dialogo._html_renderer = HtmlRenderer(text=html_dialogo(mensaje), text_size={ElementType.P: 42}, center_text=False)
    dialogo._scroller = Scroller([dialogo._html_renderer], line_separator=False, spacing=0)
  if estilo is not None:
    dialogo._confirm_button.set_button_style(estilo)
  return dialogo


# ======================================================================== texto en tarjetas
def _partir_palabras(frase: str, max_car: int) -> list[str]:
  """Parte una frase larga en trozos PAREJOS (no uno lleno y una palabra suelta)."""
  n = max(1, -(-len(frase) // max_car))
  objetivo = len(frase) / n
  piezas: list[str] = []
  actual = ""
  for palabra in frase.split():
    candidato = f"{actual} {palabra}" if actual else palabra
    if actual and (len(candidato) > max_car or (len(actual) >= objetivo and len(piezas) < n - 1)):
      piezas.append(actual)
      actual = palabra
    else:
      actual = candidato
  if actual:
    piezas.append(actual)
  return piezas


def trocear(texto: str, max_car: int = 90) -> list[str]:
  """Parte un texto largo en trozos de <= max_car para las tarjetas de la pantalla pequena.

  Un parrafo nunca se mezcla con otro. Dentro de el se juntan frases enteras (o lineas, si
  el parrafo es una lista con saltos de linea, que se conservan) y solo se parte por
  palabras una frase que por si sola no cabe. Nunca parte una palabra ni pierde texto.
  """
  trozos: list[str] = []
  for parrafo in texto.split("\n\n"):
    parrafo = parrafo.strip()
    if not parrafo:
      continue
    es_lista = "\n" in parrafo
    unidades = parrafo.split("\n") if es_lista else re.split(r"(?<=[.?!])\s+", parrafo)
    sep = "\n" if es_lista else " "
    actual = ""
    for unidad in unidades:
      for pieza in _partir_palabras(unidad, max_car):
        candidato = f"{actual}{sep}{pieza}" if actual else pieza
        if len(candidato) > max_car and actual:
          trozos.append(actual)
          actual = pieza
        else:
          actual = candidato
    if actual:
      trozos.append(actual)
  return trozos
