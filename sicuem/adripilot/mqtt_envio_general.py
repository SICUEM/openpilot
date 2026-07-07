#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
import cereal.messaging as messaging
from cereal.services import SERVICE_LIST
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
import os
from .mqtt_comandos import MQTTComandos
from .camera_sender import CameraSender

class MQTTEnvioGeneral:
  def __init__(self):
    self.velocidadActualizacion = 1
    self.base_path = os.path.dirname(os.path.abspath(__file__))
    self.jsonConfig = os.path.join(self.base_path, "config_mqtt.json")
    self.jsonCanales = os.path.join(self.base_path, "canales.json")
    self.espera = 0.5
    self.pause_event = threading.Event()
    self.pause_event.set()
    self.stop_event = threading.Event()
    self.params = Params()
    self.DongleID = self.params.get("DongleId") if self.params.get("DongleId") else "DongleID"  # Params.get() ya devuelve str
    self.conectado = False
    self._last_heartbeat = 0.0
    self.HEARTBEAT_SECS = 3.0
    self.load_config()
    self.cargar_canales()
    self.init_submaster()
    self.init_mqtt()
    self.init_comandos()
    self.init_camera_sender()
    self._link_camera_to_comandos()

  def load_config(self):
    with open(self.jsonConfig, "r") as f:
      config = json.load(f)
      self.broker_address = config.get("broker", "localhost")
      self.broker_port = int(config.get("broker_port", 1883))
    try:
      self._cfg_mtime = os.path.getmtime(self.jsonConfig)
    except OSError:
      self._cfg_mtime = None

  def _maybe_reload_broker(self):
    """Relee config_mqtt.json en caliente. Si el usuario cambia la IP del broker
    desde la UI del comma (Ajustes -> Servidor AdriPilot), reconecta SIN reiniciar
    openpilot. Antes la IP se leia una sola vez al arrancar y el cambio no surtia
    efecto hasta un reinicio -> causa tipica de 'cambie la IP y sigue sin salir'."""
    try:
      mtime = os.path.getmtime(self.jsonConfig)
    except OSError:
      return
    if mtime == self._cfg_mtime:
      return
    self._cfg_mtime = mtime
    try:
      with open(self.jsonConfig, "r") as f:
        cfg = json.load(f)
      new_broker = cfg.get("broker", self.broker_address)
      new_port = int(cfg.get("broker_port", self.broker_port))
    except Exception:
      return
    if new_broker == self.broker_address and new_port == self.broker_port:
      return
    cloudlog.warning(f"[Bemposta] broker cambiado {self.broker_address}:{self.broker_port} -> "
                     f"{new_broker}:{new_port}, reconectando (sin reiniciar openpilot)")
    self.broker_address, self.broker_port = new_broker, new_port
    try:
      self.mqttc.loop_stop()
    except Exception:
      pass
    try:
      self.mqttc.disconnect()
    except Exception:
      pass
    self.conectado = False
    threading.Thread(target=self.setup_mqtt, daemon=True).start()
    try:
      if getattr(self, "comandos_mqtt", None):
        self.comandos_mqtt.reload_broker(new_broker)
    except Exception:
      pass

  def cargar_canales(self):
    with open(self.jsonCanales, "r") as f:
      data = json.load(f)
    enabled = [item for item in data["canales"] if item.get("enable") == 1]
    # Solo suscribir a canales que sean servicios cereal reales en este build
    # ('navInstruction' ya no existe en el sunnypilot nuevo). Evita el KeyError
    # del SubMaster y el acceso posterior self.sm[canal].
    self.enabled_items = [item for item in enabled if item["canal"] in SERVICE_LIST]
    dropped = [item["canal"] for item in enabled if item["canal"] not in SERVICE_LIST]
    if dropped:
      print(f"[Bemposta] canales sin servicio cereal, ignorados: {dropped}")
    self.lista_suscripciones = [item["canal"] for item in self.enabled_items]
    self.keys_importantes_por_canal = {
      item["canal"]: item.get("keys_importantes", [])
      for item in self.enabled_items
    }

  def init_submaster(self):
    self.sm = messaging.SubMaster(self.lista_suscripciones)

  def init_mqtt(self):
    self.mqttc = mqtt.Client()
    self.mqttc.max_queued_messages_set(0)  # No encolar mensajes en RAM si no hay conexión
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.reconnect_delay_set(min_delay=1, max_delay=30)
    threading.Thread(target=self.setup_mqtt, daemon=True).start()

  def init_comandos(self):
    """Inicializa el sistema de comandos MQTT.
    Protegido: si el cliente de ordenes falla al construirse, la telemetria
    (y por tanto la PRESENCIA del dispositivo en la app) NO debe caerse con el.
    Antes esto no estaba en try/except y una excepcion aqui abortaba todo el
    __init__ -> manager lo tragaba -> ni telemetria ni ordenes ni dispositivo."""
    try:
      self.comandos_mqtt = MQTTComandos()
      self.comandos_mqtt.start()
    except Exception:
      cloudlog.exception("[Bemposta] init_comandos fallo; la telemetria sigue sin ordenes")
      self.comandos_mqtt = None

  def init_camera_sender(self):
    """Inicializa el sistema de envío de imágenes de cámaras.
    La configuracion (enabled, frecuencia) se carga automaticamente
    desde /data/adripilot_camera_config.json si existe."""
    try:
      self.camera_sender = CameraSender(
        mqtt_client=self.mqttc,
        dongle_id=self.DongleID,
        camera_type="road",
        interval_seconds=2.0,  # Default, se sobreescribe si hay config persistida
      )
      self.camera_sender.start()
    except Exception:
      self.camera_sender = None

  def _link_camera_to_comandos(self):
    """Conecta el CameraSender con MQTTComandos para permitir control remoto desde la app."""
    if getattr(self, 'camera_sender', None) is not None and getattr(self, 'comandos_mqtt', None) is not None:
      self.comandos_mqtt.set_camera_sender(self.camera_sender)

  def setup_mqtt(self):
    while not self.stop_event.is_set():
      try:
        cloudlog.warning(f"[Bemposta] MQTTEnvioGeneral conectando a broker {self.broker_address}:{self.broker_port}")
        self.mqttc.connect(self.broker_address, self.broker_port, 60)
        if not self.conectado:
          self.mqttc.loop_start()
          # Esperar un momento para que se establezca la conexión
          time.sleep(0.5)
        break
      except Exception as e:
        # Diagnostico clave: si el broker cambio de IP (IP domestica dinamica),
        # este es el log que lo delata. Antes estaba silenciado y no se veia nada.
        cloudlog.warning(f"[Bemposta] MQTTEnvioGeneral NO pudo conectar a {self.broker_address}:{self.broker_port}: {e}. Reintento en 5s")
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
      cloudlog.warning(f"[Bemposta] MQTTEnvioGeneral CONECTADO al broker {self.broker_address}:{self.broker_port} (rc={rc})")
      # "Cold start" sync: publicar nuestro estado actual como mensaje
      # RETAINED para que cualquier app que se conecte despues lo reciba
      # inmediatamente (sin necesidad de que el usuario mueva nada).
      #
      # Lo hacemos con un pequeno delay para dar tiempo a que el otro
      # cliente MQTT (mqtt_comandos, que tiene las suscripciones) procese
      # los retained que el broker le pueda estar entregando del lado app
      # (caso: el usuario cambio algo en la app mientras el Comma estaba
      # offline). Asi publicamos DESPUES de haber aplicado esos cambios
      # y nuestro retained refleja el estado real.
      threading.Timer(1.5, self._publish_state_snapshot_retained).start()
    else:
      self.conectado = False
      cloudlog.warning(f"[Bemposta] MQTTEnvioGeneral rechazado por broker (rc={rc})")

  def _publish_state_snapshot_retained(self):
    """Publica el estado actual de SteerTorqueMode y config_jetson con retain=True.

    Se llama una vez al conectar MQTT. El broker guarda estos mensajes y los
    entrega instantaneamente a cualquier subscriber futuro (p.ej. la app al
    lanzarse). source='comma_ui' para que el anti-eco de mqtt_comandos.py
    ignore el retained cuando le llegue a el mismo por su suscripcion.
    """
    if not self.conectado:
      return
    try:
      # --- SteerTorqueMode ---
      mode_raw = self.params.get("SteerTorqueMode")
      try:
        mode = int(mode_raw) if mode_raw else 0
      except (ValueError, TypeError):
        mode = 0
      steer_payload = {
        "dongle_id": self.DongleID,
        "steer_torque_mode": mode,
        "source": "comma_ui",
        "timestamp": int(time.time() * 1000),
      }
      steer_str = json.dumps(steer_payload)
      self.mqttc.publish("steer_torque_mode/global", steer_str, qos=0, retain=True)
      self.mqttc.publish(f"telemetry_config/{self.DongleID}/steer_torque_mode", steer_str, qos=0, retain=True)
      print(f"[COLD-START SYNC] Retained SteerTorqueMode={mode} publicado")

      # --- config_jetson.json (IPs, puertos, calidad, enabled) ---
      config_path = os.path.join(self.base_path, "config_jetson.json")
      if os.path.exists(config_path):
        try:
          with open(config_path, "r") as f:
            cfg = json.load(f)
        except Exception:
          cfg = {}
        # Propagar el _version EXACTO del disco. Asi, si este retained vuelve
        # a nosotros via handle_jetson_config, el anti-eco por _version lo
        # descartara porque sera igual al ya guardado en disco (no mayor).
        # Si no hay _version en el archivo (migracion), no lo inventamos
        # aqui para no pisarnos a nosotros mismos en el futuro.
        jetson_payload = {
          "dongle_id": self.DongleID,
          "jetson_enabled": cfg.get("jetson_enabled", False),
          "jetson_ip": cfg.get("jetson_ip", ""),
          "comma_ip": cfg.get("comma_ip", ""),
          "jetson_img_port": cfg.get("jetson_img_port", 5555),
          "jetson_torque_port": cfg.get("jetson_torque_port", 5556),
          "jpeg_quality": cfg.get("jpeg_quality", 80),
          "source": "comma_ui",
          "timestamp": int(time.time() * 1000),
        }
        if "_version" in cfg:
          jetson_payload["_version"] = str(cfg["_version"])
        jet_str = json.dumps(jetson_payload)
        self.mqttc.publish("jetson_config/global", jet_str, qos=0, retain=True)
        self.mqttc.publish(f"telemetry_config/{self.DongleID}/jetson_config", jet_str, qos=0, retain=True)
        print(f"[COLD-START SYNC] Retained jetson_config publicado: {jetson_payload}")
    except Exception as e:
      print(f"[COLD-START SYNC] ERROR publicando snapshot: {e}")

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False
    cloudlog.warning(f"[Bemposta] MQTTEnvioGeneral DESCONECTADO del broker {self.broker_address} (rc={rc})")

  def start(self):
    threading.Thread(target=self.loop, daemon=True).start()

  def stop(self):
    """Detiene el sistema MQTT completo."""
    self.stop_event.set()
    if hasattr(self, 'comandos_mqtt'):
      self.comandos_mqtt.stop()
    if hasattr(self, 'camera_sender') and self.camera_sender is not None:
      self.camera_sender.stop()
    self.mqttc.disconnect()
    # print("🛑 Sistema MQTT detenido")  # Comentado para reducir uso de memoria

  def loop(self):
    while not self.stop_event.is_set():
      self.pause_event.wait()
      self.sm.update()

      # Recoger en caliente un cambio de IP del broker hecho desde la UI.
      self._maybe_reload_broker()

      # Verificar conexión antes de intentar enviar (evita encolar mensajes)
      # Usar verificación más simple: si está conectado según el callback
      is_connected = self.conectado
      # También verificar el estado real del cliente si está disponible
      if hasattr(self.mqttc, 'is_connected'):
        is_connected = is_connected and self.mqttc.is_connected()

      if not is_connected:
        # Sin conexión: no procesar ni encolar mensajes para evitar saturación de RAM
        # Log ocasional para debug (cada 50 iteraciones = ~50 segundos)
        if hasattr(self, '_no_connection_log_counter'):
          self._no_connection_log_counter += 1
        else:
          self._no_connection_log_counter = 0

        # Log eliminado para reducir uso de memoria

        time.sleep(self.velocidadActualizacion)
        continue

      # Resetear contador si hay conexión
      if hasattr(self, '_no_connection_log_counter'):
        self._no_connection_log_counter = 0

      # Publicar Jetson config si fue cambiada desde la UI del Comma
      try:
        jetson_payload = self.params.get("JetsonConfigMqttPayload")
        if jetson_payload and len(jetson_payload) > 2:
          payload_str = jetson_payload
          print(f"[JETSON SYNC] Detectado JetsonConfigMqttPayload: {payload_str[:200]}")
          try:
            # retain=True: el broker guarda la ultima version de cada topic y
            # la entrega automaticamente a futuros subscribers. Asi la app al
            # lanzarse tiene el estado actual sin tener que preguntarle a nadie.
            result1 = self.mqttc.publish("jetson_config/global", payload_str, qos=0, retain=True)
            result2 = self.mqttc.publish(f"telemetry_config/{self.DongleID}/jetson_config", payload_str, qos=0, retain=True)
            print(f"[JETSON SYNC] Publicado (retained) a jetson_config/global rc={result1.rc}")
            print(f"[JETSON SYNC] Publicado (retained) a telemetry_config/{self.DongleID}/jetson_config rc={result2.rc}")
          except Exception as e:
            print(f"[JETSON SYNC] ERROR publicando MQTT: {e}")
          self.params.remove("JetsonConfigMqttPayload")
          print("[JETSON SYNC] Param JetsonConfigMqttPayload eliminado")
      except Exception as e:
        print(f"[JETSON SYNC] ERROR leyendo param: {e}")

      # Publicar SteerTorqueMode si fue cambiado desde la UI del Comma
      try:
        steer_mode_payload = self.params.get("SteerTorqueModeMqttPayload")
        if steer_mode_payload and len(steer_mode_payload) > 2:
          payload_str = steer_mode_payload
          print(f"[STEER MODE SYNC] Detectado payload: {payload_str[:200]}")
          try:
            # retain=True: ver comentario arriba en JetsonConfig.
            result1 = self.mqttc.publish("steer_torque_mode/global", payload_str, qos=0, retain=True)
            result2 = self.mqttc.publish(f"telemetry_config/{self.DongleID}/steer_torque_mode", payload_str, qos=0, retain=True)
            print(f"[STEER MODE SYNC] Publicado (retained) a steer_torque_mode/global rc={result1.rc}")
            print(f"[STEER MODE SYNC] Publicado (retained) a telemetry_config/{self.DongleID}/steer_torque_mode rc={result2.rc}")
          except Exception as e:
            print(f"[STEER MODE SYNC] ERROR publicando MQTT: {e}")
          self.params.remove("SteerTorqueModeMqttPayload")
      except Exception as e:
        print(f"[STEER MODE SYNC] ERROR leyendo param: {e}")

      # Publicar JetsonObstacleApplyTarget si fue cambiado desde la UI del Comma
      try:
        apply_target_payload = self.params.get("JetsonObstacleApplyTargetMqttPayload")
        if apply_target_payload and len(apply_target_payload) > 2:
          payload_str = apply_target_payload
          print(f"[APPLY TARGET SYNC] Detectado payload: {payload_str[:200]}")
          try:
            # retain=True: que la app reciba el estado al reconectarse.
            result1 = self.mqttc.publish(f"telemetry_config/{self.DongleID}/jetson_apply_target", payload_str, qos=0, retain=True)
            print(f"[APPLY TARGET SYNC] Publicado (retained) a telemetry_config/{self.DongleID}/jetson_apply_target rc={result1.rc}")
          except Exception as e:
            print(f"[APPLY TARGET SYNC] ERROR publicando MQTT: {e}")
          self.params.remove("JetsonObstacleApplyTargetMqttPayload")
      except Exception as e:
        print(f"[APPLY TARGET SYNC] ERROR leyendo param: {e}")

      # Publicar JetsonObstacleStatus (modo 3 COMMA+JETSON) si cambió en controlsd
      try:
        obstacle_payload = self.params.get("JetsonObstacleStatusMqttPayload")
        if obstacle_payload and len(obstacle_payload) > 2:
          payload_str = obstacle_payload
          print(f"[OBSTACLE STATUS SYNC] Detectado payload: {payload_str[:200]}")
          try:
            # retain=False aquí: el status del esquive es transitorio, no
            # queremos que un suscriptor que se conecte tarde reciba un
            # "DODGING_RIGHT" de hace 10 minutos como si estuviera vivo.
            result1 = self.mqttc.publish("jetson_obstacle_status/global", payload_str, qos=0, retain=False)
            result2 = self.mqttc.publish(f"telemetry_config/{self.DongleID}/jetson_obstacle_status", payload_str, qos=0, retain=False)
            print(f"[OBSTACLE STATUS SYNC] Publicado a jetson_obstacle_status/global rc={result1.rc}")
            print(f"[OBSTACLE STATUS SYNC] Publicado a telemetry_config/{self.DongleID}/jetson_obstacle_status rc={result2.rc}")
          except Exception as e:
            print(f"[OBSTACLE STATUS SYNC] ERROR publicando MQTT: {e}")
          self.params.remove("JetsonObstacleStatusMqttPayload")
      except Exception as e:
        print(f"[OBSTACLE STATUS SYNC] ERROR leyendo param: {e}")

      for canal in self.enabled_items:
        nombre = canal["canal"]
        topic = canal["topic"].format(self.DongleID)

        if nombre in self.sm.data and self.sm.updated[nombre]:
          datos = self.sm[nombre].to_dict()
          datos_filtrados = self.enviar_datos_importantes(nombre, datos)
          if datos_filtrados:
            # Verificar conexión nuevamente antes de cada publicación
            if self.conectado:
              # Verificar también el estado real si está disponible
              if hasattr(self.mqttc, 'is_connected') and not self.mqttc.is_connected():
                continue
              try:
                self.mqttc.publish(topic, json.dumps(datos_filtrados), qos=0)
              except Exception as e:
                # NO tocar self.conectado aqui: un fallo de serializacion
                # (json.dumps de un to_dict() con bytes/NaN, etc.) o un error
                # puntual de un canal NO significa que el socket MQTT este caido.
                # Si lo poniamos a False, como on_disconnect nunca disparaba, la
                # telemetria quedaba CONGELADA para siempre. Dejar que las callbacks
                # (on_disconnect) gestionen el estado real de la conexion.
                cloudlog.warning(f"[Bemposta] fallo publicando canal {nombre} en {topic}: {e}")
            # Si no hay conexión, simplemente no enviar (no encolar)

      # Heartbeat de PRESENCIA. La app marca "conectado" solo si le llega
      # telemetria en <10 s. Onroad carState ya fluye; pero PARADO/OFFROAD ningun
      # canal se actualiza (sm.updated=False) y no se publica nada -> el dispositivo
      # aparece desconectado aunque el MQTT este perfectamente conectado. Republicamos
      # el ultimo carState conocido a ritmo bajo para que salga "conectado" tambien en
      # banco (como hacia el sender antiguo, que publicaba cada ciclo sin condicion).
      now = time.time()
      if self.conectado and (now - self._last_heartbeat) >= self.HEARTBEAT_SECS:
        self._last_heartbeat = now
        if not (hasattr(self.mqttc, 'is_connected') and not self.mqttc.is_connected()):
          try:
            if "carState" in self.sm.data:
              hb = self.sm["carState"].to_dict()
            else:
              hb = {}
            hb["dongle_id"] = self.DongleID
            self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/carState", json.dumps(hb), qos=0)
          except Exception as e:
            cloudlog.warning(f"[Bemposta] heartbeat fallo: {e}")

      time.sleep(self.velocidadActualizacion)

  def enviar_datos_importantes(self, canal, datos):
    claves = self.keys_importantes_por_canal.get(canal, [])

    # Si no hay claves definidas, usar datos directamente sin copiar
    if not claves:
      datos["dongle_id"] = self.DongleID
      return datos
    else:
      resultado = {k: datos[k] for k in claves if k in datos}
      resultado["dongle_id"] = self.DongleID
      return resultado

if __name__ == "__main__":
  sender = MQTTEnvioGeneral()
  sender.start()

  while not sender.conectado:
    time.sleep(0.5)

  while True:
    time.sleep(10)
