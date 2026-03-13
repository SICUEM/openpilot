#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
import time
import json
import signal
import sys
import os
from datetime import datetime
from threading import Thread, Event
from openpilot.common.params import Params
import cereal.messaging as messaging
import requests
import paho.mqtt.client as mqtt


class SicMqttHilo2:
  def __init__(self):
    self.initialize_variables()
    self.cargar_canales()
    self.initialize_mqtt_client()
    self.load_configuration()
    self.start_mqtt_thread()
    # Archivo de debug compartido con mqtt_comandos.py
    self.debug_file = "/tmp/mqtt_debug_messages.txt"
    self.max_messages = 30
    self.debug_enabled = False
    self._last_debug_check = 0

  def initialize_variables(self):
    """
    Inicializa las variables principales de la clase.

    - Configura rutas de archivos JSON para canales y configuración.
    - Establece valores predeterminados para variables importantes como `espera` y `indice_canal`.
    - Inicializa eventos para pausar y detener hilos de forma segura.
    - Carga parámetros del sistema, como el `DongleID`, desde una base de datos interna.

    Comentarios clave:
    - `pause_event`: Permite pausar operaciones de manera segura.
    - `stop_event`: Señal para detener hilos en ejecución.
    """
    self.velocidadActualizacion = 1
    self.jsonCanales = "../../sicuem/canales.json"  # Ruta al archivo JSON de configuración de canales
    self.jsonConfig = "../../sicuem/config.json"  # Ruta al archivo JSON de configuración general
    self.espera = 0.5  # Intervalo de espera predeterminado en segundos
    self.indice_canal = 0  # Índice inicial para los canales
    self.conectado = False
    self.last_lider_toggle_state = None

    # Estado inicial de conexión MQTT
    self.sm = messaging.SubMaster(
      ['carState', 'controlsState', 'liveCalibration', 'carControl', 'gpsLocationExternal', 'gpsLocation',
       'navInstruction', 'radarState', 'drivingModelData'])  # Objeto SubMaster para recibir datos (sin inicializar)
    self.pause_event = Event()  # Evento para pausar operaciones
    self.pause_event.set()  # Activa el evento inicialmente
    self.stop_event = Event()  # Evento para detener hilos
    params = Params()  # Carga de parámetros del sistema
    self.params = params  # Almacena la referencia a los parámetros
    self.DongleID = params.get("DongleId").decode('utf-8') if params.get("DongleId") else "DongleID"
    self.params.put_bool("intervalos_toggle", False)
    print(f"🆔 DongleID local: {self.DongleID}")

    # El `DongleID` identifica de manera única el dispositivo conectado.

  def cargar_canales(self):
    """
    Carga la configuración de los canales desde el archivo JSON.
    - Utiliza `verificar_toggle_canales` para ajustar dinámicamente los canales habilitados/deshabilitados.
    - Filtra solo los canales habilitados (`enable: 1`).
    - Guarda las claves importantes asociadas a cada canal.
    """
    with open(self.jsonCanales, 'r') as f:
      data_canales = json.load(f)

    # Ajustar los canales habilitados/deshabilitados según los parámetros
    self.verificar_toggle_canales(data_canales)

    # Filtrar solo los canales habilitados
    self.enabled_items = [item for item in data_canales['canales'] if item['enable'] == 1]

    # Obtener los nombres de los canales habilitados para la suscripción
    self.lista_suscripciones = [item['canal'] for item in self.enabled_items]

    # Mapear claves importantes por canal
    self.keys_importantes_por_canal = {
      item['canal']: item.get('keys_importantes', [])
      for item in self.enabled_items
    }

  def initialize_mqtt_client(self):
    """Configura el cliente MQTT y sus callbacks con reconexión automática."""
    self.mqttc = mqtt.Client()
    self.mqttc.max_queued_messages_set(0)  # No encolar mensajes en RAM si no hay conexión
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.on_message = self.on_message

    # Configurar reintento de conexión automática
    self.mqttc.reconnect_delay_set(min_delay=1, max_delay=30)

  def load_configuration(self):
    """
    Carga y procesa el archivo de configuración JSON.

    - Abre y lee el archivo de configuración general (`self.jsonConfig`).
    - Configura parámetros críticos como velocidad de envío, estado de pausa y dirección del broker MQTT.

    Manejo de errores:
    - Si el archivo no existe, está malformado o contiene claves no válidas, informa el error al usuario.
    - Cubre casos como valores no numéricos o divisiones por cero.

    Comentarios clave:
    - `self.espera`: Calcula el intervalo entre operaciones basado en la configuración de velocidad.
    - `self.pause_event`: Se limpia (desactiva) si el envío está deshabilitado (`send_value == 0`).
    """
    try:
      with open(self.jsonConfig, 'r') as f:
        self.dataConfig = json.load(f)  # Carga los datos desde el archivo JSON

      # Configuración de velocidad (tiempo de espera entre operaciones)
      speed_value = self.dataConfig['config']['speed']['value']
      self.espera = 1.0 / float(speed_value)

      # Configuración de envío (habilitar o deshabilitar operaciones)
      send_value = int(self.dataConfig['config']['send']['value'])
      if send_value == 0:
        self.pause_event.clear()  # Pausa las operaciones si `send` es 0

      # Dirección del broker MQTT
      self.broker_address = self.dataConfig['config']['IpServer']['value']

    except FileNotFoundError:
      print(f"Error: El archivo '{self.jsonConfig}' no se encontró.")
    except json.JSONDecodeError:
      print(f"Error: El archivo '{self.jsonConfig}' no contiene un JSON válido.")
    except KeyError as e:
      print(f"Error: Falta la clave {e} en la configuración del archivo JSON.")
    except ValueError as e:
      print(f"Error: Valor no válido en la configuración: {e}")
    except ZeroDivisionError:
      print("Error: La configuración de velocidad no puede ser cero.")
    except Exception as e:
      print(f"Error inesperado: {e}")

  def start_mqtt_thread(self):
    """
    Inicia un hilo no bloqueante para manejar la conexión MQTT.

    - Crea y lanza un hilo en segundo plano que ejecuta `setup_mqtt_connection`.
    - El hilo es "daemon", lo que significa que se detiene automáticamente cuando termina el programa.

    Comentarios clave:
    - Se usa un hilo para evitar que la conexión MQTT bloquee el flujo principal del programa.
    - `setup_mqtt_connection`: Se encarga de establecer la conexión con el broker y manejar reconexiones.
    """
    Thread(target=self.setup_mqtt_connection, daemon=True).start()

  # ----------------------------------------------------------------------------------------------- INIT STUFF END

  def start(self) -> int:
    # self.reanudar_envio() #

    self.cargar_canales()

    # SubMaster ya creado en __init__, no duplicar (causa memory leak)

    time.sleep(self.velocidadActualizacion)
    hilo_telemetry = Thread(target=self.loop, daemon=True)
    hilo_telemetry.start()

    self.watchdog_mqtt()

    self.enviar_estado_lider_toggle()

    return 0

  def watchdog_mqtt(self, intervalo=10):
    """
    Verifica si MQTT sigue conectado. Si no, intenta reconectar.
    Se ejecuta periódicamente cada 'intervalo' segundos.
    """

    def loop_watchdog():
      while not self.stop_event.is_set():
        if not self.conectado or not self.mqttc.is_connected():
          try:
            self.mqttc.reconnect()
            self.mqttc.subscribe("opmqttsender/messages", qos=0)
            self.mqttc.subscribe("telemetry_publish/vego", qos=0)
            self.mqttc.subscribe("telemetry_config/+/intervalos", qos=0)
            self.mqttc.subscribe("telemetry_config/+/left", qos=0)
            self.mqttc.subscribe("telemetry_config/+/right", qos=0)
          except Exception:
            pass
        time.sleep(intervalo)

    Thread(target=loop_watchdog, daemon=True).start()

  # ------------------------------------------------------------------------------------------------ FUNCION START END

  def verificar_toggle_canales(self, data_canales):
    """
    Activa todos los canales sin importar el estado de los toggles.
    - Fuerza el atributo `enable` de cada canal a 1.
    - Imprime un mensaje para cada canal activado.
    """
    for item in data_canales['canales']:
      try:
        # Forzar el estado del canal a habilitado (enable = 1)
        if item['enable'] != 1:  # Solo actualiza si no está ya habilitado
          self.cambiar_enable_canal(item['canal'], 1)
          # print(f"Canal habilitado: {item['canal']}")  # Comentado para reducir uso de memoria
      except Exception as e:
        pass  # Error silenciado para reducir uso de memoria

  def setup_mqtt_connection(self):
    """Configura la conexión MQTT con manejo de reconexión."""
    while not self.stop_event.is_set():
      try:
        self.mqttc.connect(self.broker_address, 1883, 60)
        self.mqttc.subscribe("opmqttsender/messages", qos=0)
        self.mqttc.subscribe("telemetry_publish/vego", qos=0)
        self.mqttc.subscribe("telemetry_config/+/intervalos", qos=0)
        self.mqttc.subscribe("telemetry_config/+/left", qos=0)
        self.mqttc.subscribe("telemetry_config/+/right", qos=0)

        # Evita iniciar múltiples veces el loop
        if not self.conectado:
          self.mqttc.loop_start()
          self.conectado = True
        break
      except Exception as e:
        time.sleep(5)

  def signal_handler(self, sig, frame):
    """Manejador de la señal SIGINT para detener el programa de forma controlada."""
    self.cleanup()
    sys.exit(0)

  # ------------------------------------------------------------------------------------------------ VERIFICAR QUE TOGGLES ESTAN ACTIVADOS

  def loop(self):
    """
    Bucle principal que:
    - Verifica constantemente el estado de `telemetria_uem`.
    - Si `telemetria_uem` está habilitado (`True`), ejecuta `loop_principal`.
    - Si está deshabilitado (`False`), espera y sigue verificando.
    """
    self.conexion()  # Verifica la conexión a Internet en segundo plano

    # Hilo para publicar pings periódicos
    hilo_ping = Thread(target=self.loopPing, daemon=True)
    hilo_ping.start()

    while True:
      # Verificar el estado de telemetria_uem
      # if self.params.get_bool("telemetria_uem"):
      # print("Telemetría habilitada, ejecutando operaciones.")
      self.loop_principal()
      # else:
      # print("Telemetría deshabilitada, esperando...")

      self.verificar_cambio_lider_toggle()
      time.sleep(0.5)  # Pausa breve antes de volver a verificar

  def verificar_cambio_lider_toggle(self):
    """Detecta cambios en `lider_toggle` y los envía por MQTT."""
    # Verificar conexión antes de procesar
    if not self.conectado or not hasattr(self.mqttc, 'is_connected') or not self.mqttc.is_connected():
      return

    # Obtener el estado actual de `lider_toggle`
    lider_toggle_actual = self.params.get_bool("lider_toggle")

    # Si es la primera vez o si ha cambiado, enviar por MQTT
    if lider_toggle_actual != self.last_lider_toggle_state:
      estado_mqtt = "on" if lider_toggle_actual else "off"
      # Verificar conexión nuevamente antes de publicar
      if self.conectado and self.mqttc.is_connected():
        self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lider_toggle", estado_mqtt, qos=0)
        # print(f"📡 Estado `lider_toggle` cambiado: {estado_mqtt}")  # Comentado para reducir uso de memoria

      # Actualizar el estado registrado
      self.last_lider_toggle_state = lider_toggle_actual

  def enviar_estado_lider_toggle(self):
    """Envia el estado inicial de `lider_toggle` cuando el programa inicia."""
    # Verificar conexión antes de enviar
    if not self.conectado or not hasattr(self.mqttc, 'is_connected') or not self.mqttc.is_connected():
      return

    lider_toggle_actual = self.params.get_bool("lider_toggle")
    estado_mqtt = "on" if lider_toggle_actual else "off"

    # Verificar conexión nuevamente antes de publicar
    if self.conectado and self.mqttc.is_connected():
      self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lider_toggle", estado_mqtt, qos=0)
      # print(f"📡 Estado inicial `lider_toggle` enviado: {estado_mqtt}")  # Comentado para reducir uso de memoria

    # Guardar el estado inicial para futuras comparaciones
    self.last_lider_toggle_state = lider_toggle_actual

  def loop_principal(self):
    """
    Ejecuta las operaciones principales de telemetría:
    - Carga dinámicamente los canales habilitados.
    - Envía datos importantes a través de MQTT.
    - Publica periódicamente el estado del archivo mapbox.
    """
    self.pause_event.wait()  # Pausa las operaciones si está desactivada la telemetría

    # Verificar conexión antes de procesar (evita encolar mensajes)
    if not self.conectado or not hasattr(self.mqttc, 'is_connected') or not self.mqttc.is_connected():
      # Sin conexión: no procesar ni encolar mensajes para evitar saturación de RAM
      time.sleep(self.espera)
      return

    # Recargar canales solo cada 60 segundos (evita file I/O + objetos nuevos cada 0.5s)
    now = time.time()
    if not hasattr(self, '_last_canal_reload') or (now - self._last_canal_reload) > 60:
      self.cargar_canales()
      self._last_canal_reload = now

    if len(self.enabled_items) > 0 and self.sm:
      for canal_actual in self.enabled_items:
        canal_nombre = canal_actual['canal']
        if canal_nombre in self.sm.data:
          try:
            self.sm.update()
            # Convierte los datos de SubMaster a un diccionario
            datos_canal = self.sm[canal_nombre].to_dict()
            # Envía solo los datos importantes
            datos_importantes = self.enviar_datos_importantes(canal_nombre, datos_canal)
            #print(f"📤 Enviando datos importantes para {canal_nombre}: {datos_importantes}")

            # print("Enviando canal:",canal_actual['topic'])
            # canal_actual['topic']
            self.publicarInfo(canal_actual['topic'], datos_importantes)

            '''
            self.mqttc.publish(
              str(canal_actual['topic']).format(self.DongleID),
              json.dumps(datos_importantes),
              qos=0
            )
            '''
          except KeyError:
            continue

      # Publicar estado del archivo mapbox (solo cada 10s, no cada 0.5s)
      if not hasattr(self, '_last_mapbox_check') or (time.time() - self._last_mapbox_check) > 10:
        self.enviar_estado_archivo_mapbox()
        self._last_mapbox_check = time.time()

      # Espera configurada entre iteraciones
      time.sleep(self.espera)

  def loopPing(self):
    """Bucle que publica mensajes de ping periódicamente sin bloquear."""
    while not self.stop_event.is_set():
      self.pause_event.wait()
      # Verificar conexión antes de publicar ping (evita encolar mensajes)
      if self.conectado and hasattr(self.mqttc, 'is_connected') and self.mqttc.is_connected():
        self.mqttc.publish("telemetry_config/ping", str(time.time()).format(self.DongleID), qos=0)
      # Si no hay conexión, simplemente no enviar (no encolar)
      time.sleep(3)

  ##------------------------------------------------------------------------------------------------ loop related end

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True

  def on_disconnect(self, client, userdata, rc):
    """Maneja la desconexión. La reconexión la maneja reconnect_delay_set() y el watchdog."""
    self.conectado = False
    # NO bloquear este callback — paho-mqtt maneja la reconexión automáticamente
    # con reconnect_delay_set(). Bloquear aquí causa acumulación de buffers internos.

  def save_debug_message(self, topic, payload):
    """Guarda un mensaje MQTT para el modo debug."""
    try:
      if not self.debug_enabled:
        if time.time() - self._last_debug_check > 10:
          self.debug_enabled = self.params.get_bool("modo_debug")
          self._last_debug_check = time.time()
        if not self.debug_enabled:
          return
    except Exception:
      return

    try:
      timestamp = time.strftime("%H:%M:%S", time.localtime())
      payload_display = payload[:50] if len(payload) > 50 else payload
      message = f"[{timestamp}] {topic}\n{payload_display}\n"

      messages = []
      if os.path.exists(self.debug_file):
        try:
          file_size = os.path.getsize(self.debug_file)
          if file_size > 100 * 1024:
            with open(self.debug_file, 'rb') as f:
              f.seek(max(0, file_size - 50 * 1024))
              content = f.read().decode('utf-8', errors='ignore')
              lines = content.split('\n')
          else:
            with open(self.debug_file, 'r', encoding='utf-8') as f:
              lines = f.readlines()

          i = len(lines) - 1
          temp_messages = []
          while i >= 0 and len(temp_messages) < self.max_messages:
            if lines[i].strip().startswith('['):
              if i > 0:
                temp_messages.insert(0, (lines[i-1].strip() + '\n' + lines[i].strip()).strip())
                i -= 2
              else:
                i -= 1
            else:
              i -= 1
          messages = temp_messages
        except Exception:
          messages = []

      messages.append(message.strip())
      if len(messages) > self.max_messages:
        messages = messages[-self.max_messages:]

      if messages:
        try:
          with open(self.debug_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(messages))
        except Exception:
          pass
    except Exception:
      pass

  def on_message(self, client, userdata, msg):
    """Callback que maneja los mensajes MQTT."""
    # Guardar mensaje para modo debug
    try:
      payload_str = msg.payload.decode(errors="ignore").strip()
      self.save_debug_message(msg.topic, payload_str)
    except Exception:
      pass

    if msg.topic == "telemetry_publish/vego":
      try:
        data = json.loads(msg.payload.decode())  # Intenta cargar el JSON
        #print(f"✅ Datos decodificados correctamente: {data}")  # 🟢 Verifica que se decodifica bien

        # Extraer valores y asegurarse de que son string antes de guardarlos
        jv = str(data.get("Jv", "0"))
        nd = str(data.get("Nd", "0"))
        v3 = str(data.get("v3", "0"))
        sim = str(data.get("Ur", "0"))

        # Guardar en Params y verificar
        self.params.put("Velocidad_C1", jv)
        self.params.put("Velocidad_C2", nd)
        self.params.put("Velocidad_C3", v3)
        self.params.put("Velocidad_C4", sim)

        #print(f"📌 Velocidades guardadas: C1: {jv}, C2: {nd}, C3: {v3}" + f", C4: {sim}")

      except json.JSONDecodeError:
        pass  # Error silenciado para reducir uso de memoria


    elif msg.topic.startswith("telemetry_config/") and msg.topic.endswith("/intervalos"):
      partes = msg.topic.split("/")
      if len(partes) >= 3:
        id_coma = partes[1]
        if id_coma == self.DongleID:
          payload = msg.payload.decode(errors="ignore").strip().lower()
          if payload == "true":
            self.params.put_bool("intervalos_toggle", True)
          elif payload == "false":
            self.params.put_bool("intervalos_toggle", False)

    elif msg.topic.startswith("telemetry_config/") and msg.topic.endswith("/left"):
      partes = msg.topic.split("/")
      if len(partes) >= 3 and partes[1] == self.DongleID:
        payload = msg.payload.decode(errors="ignore").strip().lower()

        # Verificar toggle de seguridad c_carril
        if not self.params.get_bool("c_carril"):
          return

        if payload == "false":
          self.params.put_bool("ForceLaneChangeLeft", False)
          self.params.put_bool("ForceLaneChangeRight", False)

        elif self.params.get_bool("ForceLaneChangeRight"):
          self.params.put_bool("ForceLaneChangeLeft", False)
          self.params.put_bool("ForceLaneChangeRight", False)
        else:
          self.params.put_bool("ForceLaneChangeLeft", True)


    elif msg.topic.startswith("telemetry_config/") and msg.topic.endswith("/right"):
      partes = msg.topic.split("/")
      if len(partes) >= 3 and partes[1] == self.DongleID:
        payload = msg.payload.decode(errors="ignore").strip().lower()

        # Verificar toggle de seguridad c_carril
        if not self.params.get_bool("c_carril"):
          return

        if payload == "false":
          self.params.put_bool("ForceLaneChangeLeft", False)
          self.params.put_bool("ForceLaneChangeRight", False)

        elif self.params.get_bool("ForceLaneChangeLeft"):
          self.params.put_bool("ForceLaneChangeLeft", False)
          self.params.put_bool("ForceLaneChangeRight", False)

        else:
          self.params.put_bool("ForceLaneChangeRight", True)

  def cambiar_enable_canal(self, canal, estado):
    """
    Cambia el estado (`enable`) de un canal específico en el archivo JSON.

    Parámetros:
    - canal: Nombre del canal a modificar.
    - estado: Nuevo valor para el atributo `enable` (0 o 1).

    Comportamiento:
    - Lee el archivo JSON y busca el canal especificado.
    - Si el estado actual del canal es diferente del nuevo estado:
        - Actualiza el estado en memoria.
        - Guarda los cambios en el archivo JSON.
    - Si no hay cambios, evita reescribir el archivo.
    - Recarga los canales tras realizar un cambio.

    Notas:
    - La función es eficiente, ya que minimiza las escrituras al archivo JSON.
    """
    # Leer el archivo JSON
    with open(self.jsonCanales, 'r') as f:
      dataCanales = json.load(f)

    # Buscar el canal y verificar si requiere actualización
    canal_encontrado = False
    for item in dataCanales['canales']:
      if item['canal'] == canal:
        if item['enable'] != estado:  # Actualizar solo si es necesario
          item['enable'] = estado
          canal_encontrado = True
        break

    # Si el canal fue modificado, guardar los cambios
    if canal_encontrado:
      with open(self.jsonCanales, 'w') as f:
        json.dump(dataCanales, f, indent=4)
      print(f"Estado del canal '{canal}' cambiado a {estado}.")
      self.cargar_canales()  # Recargar los canales
    else:
      print(f"No se realizaron cambios para el canal '{canal}'.")

  def enviar_datos_importantes(self, canal, datos):
    """
    Filtra y envía solo los datos importantes para el canal dado.
    - Los campos relevantes se obtienen dinámicamente de `self.keys_importantes_por_canal`.
    """
    datos_importantes = {}

    # Obtener las claves importantes para este canal
    keys_importantes = self.keys_importantes_por_canal.get(canal, [])

    # Filtrar los datos relevantes
    for key in keys_importantes:
      if key in datos:
        datos_importantes[key] = datos[key]

    return datos_importantes

  def conexion(self, url='http://www.google.com', intervalo=30):
    """Verifica la conexión a Internet periódicamente en un hilo separado."""

    def check_connection():
      # Reutilizar sesión para evitar leak de conexiones/Response objects
      session = requests.Session()
      while not self.stop_event.is_set():
        try:
          response = session.head(url, timeout=5)  # HEAD en vez de GET (sin body)
          response.close()
        except Exception:
          pass
        time.sleep(intervalo)

    Thread(target=check_connection, daemon=True).start()

  def obtener_gps_location(self):
    # Crear una instancia del SubMaster para obtener datos del canal 'gpsLocationExternal'
    sm = self.sm

    # Actualizar para obtener los datos más recientes
    sm.update(0)

    # Verificar si el mensaje de gpsLocationExternal es válido
    latitude = sm['gpsLocationExternal'].latitude
    longitude = sm['gpsLocationExternal'].longitude
    altitude = sm['gpsLocationExternal'].altitude

    # print("latitude", latitude)
    # print("longitude", longitude)

    return {
      "latitude": latitude,
      "longitude": longitude,
      "altitude": altitude
    }

  def enviar_estado_archivo_mapbox(self):
    # Obtener la posición GPS actual desde el canal 'gpsLocationExternal'
    gps_data = self.obtener_gps_location()
    current_lat = gps_data.get('latitude')
    current_lon = gps_data.get('longitude')

    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_archivo = os.path.join(ruta_actual, "../system/manager/mapbox_response.json")

    if os.path.exists(ruta_archivo):
      try:
        with open(ruta_archivo, 'r') as archivo:
          data = json.load(archivo)
          closest_maneuvers = {
            "roundabout": {"distance": float('inf'), "latitude": None, "longitude": None},
            "turn": {"distance": float('inf'), "latitude": None, "longitude": None},
            "off ramp": {"distance": float('inf'), "latitude": None, "longitude": None},  # Cambiado a "off road"
            "on ramp": {"distance": float('inf'), "latitude": None, "longitude": None}  # Cambiado a "on road"
          }

          # Analizar las rutas y encontrar maniobras específicas
          if "routes" in data and len(data["routes"]) > 0:
            for leg in data["routes"][0].get("legs", []):
              for step in leg.get("steps", []):
                maneuver = step.get("maneuver", {})
                maneuver_type = maneuver.get("type", "").strip().lower()  # Asegurar consistencia
                maneuver_lat = maneuver.get("location", [None, None])[1]
                maneuver_lon = maneuver.get("location", [None, None])[0]

                if maneuver_type in closest_maneuvers and not maneuver.get("hecho", False):
                  # Calcular la distancia manualmente si las coordenadas son válidas
                  if current_lat is not None and current_lon is not None and maneuver_lat is not None and maneuver_lon is not None:
                    calculated_distance = self.calculate_distance(
                      current_lat, current_lon, maneuver_lat, maneuver_lon
                    )
                    if calculated_distance < closest_maneuvers[maneuver_type]["distance"]:
                      closest_maneuvers[maneuver_type] = {
                        "distance": calculated_distance,
                        "latitude": maneuver_lat,
                        "longitude": maneuver_lon
                      }

                    # Marcar la maniobra como hecha si la distancia es menor a 2 metros
                    if calculated_distance < 2:
                      step["maneuver"]["hecho"] = True

          # Actualizar el archivo JSON con las maniobras marcadas como hechas
          with open(ruta_archivo, 'w') as archivo:
            json.dump(data, archivo, indent=2)

          # Obtener distancias
          roundabout_distance = closest_maneuvers["roundabout"]["distance"]
          turn_distance = closest_maneuvers["turn"]["distance"]
          off_road_distance = closest_maneuvers["off ramp"]["distance"]  # Cambiado a "off road"
          on_road_distance = closest_maneuvers["on ramp"]["distance"]  # Cambiado a "on road"

          # Guardar las distancias en los parámetros
          self.params.put("roundabout_distance", str(roundabout_distance))
          self.params.put("turn_distance", str(turn_distance))
          self.params.put("on_road_distance", str(on_road_distance))  # Cambiado a "on road"
          self.params.put("off_road_distance", str(off_road_distance))  # Cambiado a "off road"

          # Preparar el contenido para MQTT
          contenido = {
            "roundabout": roundabout_distance if roundabout_distance != float('inf') else -1,
            "turn": turn_distance if turn_distance != float('inf') else -1,
            "off_road": off_road_distance if off_road_distance != float('inf') else -1,
            "on_road": on_road_distance if on_road_distance != float('inf') else -1
          }

          print(f"Distancias enviadas: {contenido}")
          if self.params.get_bool("mapbox_toggle"):
            # Verificar conexión antes de publicar (evita encolar mensajes)
            if self.conectado and hasattr(self.mqttc, 'is_connected') and self.mqttc.is_connected():
              self.mqttc.publish("telemetry_mqtt/" + self.DongleID + "/mapbox_status", str(contenido), qos=0)
            # Si no hay conexión, simplemente no enviar (no encolar)

      except Exception as e:
        print(f"Error al procesar el archivo Mapbox: {e}")
    else:
      self.params.put("roundabout_distance", "-1")
      self.params.put("turn_distance", "-1")
      self.params.put("off_road_distance", "-1")
      self.params.put("on_road_distance", "-1")

  def calculate_distance(self, lat1, lon1, lat2, lon2):
    """Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine."""
    if None in [lat1, lon1, lat2, lon2]:
      return float('inf')

    # Conversión de coordenadas a radianes
    lat1, lon1, lat2, lon2 = map(lambda x: x * (math.pi / 180), [lat1, lon1, lat2, lon2])

    # Fórmula de Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371000  # Radio de la Tierra en metros
    return R * c

  def publicarInfo(self, canal, datos_importantes):
    #print(f"🟨 Intentando publicar en canal: {canal}")
    #print(f"📤 ***************************---------!!!!!!!Datos enviados desde canal '{canal}':")
    #imprimir_setspeed_y_vego(canal, datos_importantes)

    # Verificar conexión primero (evita encolar mensajes)
    if not self.conectado or not hasattr(self.mqttc, 'is_connected') or not self.mqttc.is_connected():
      # Sin conexión: no publicar ni encolar mensajes
      return

    permitido = (
      ('carState' in canal and self.params.get_bool("carState_toggle")) or
      ('controlsState' in canal and self.params.get_bool("controlsState_toggle")) or
      ('liveCalibration' in canal and self.params.get_bool("liveCalibration_toggle")) or
      ('carControl' in canal and self.params.get_bool("carControl_toggle")) or
      ('gpsLocationExternal' in canal and self.params.get_bool("gpsLocationExternal_toggle")) or
      ('navInstruction' in canal and self.params.get_bool("navInstruction_toggle")) or
      ('radarState' in canal and self.params.get_bool("radarState_toggle")) or
      ('drivingModelData' in canal and self.params.get_bool("drivingModelData_toggle"))
    )

    #print(f"🟦 ¿Está permitido publicar en '{canal}'? {permitido}")

    if permitido:
      try:
        # Verificar conexión nuevamente antes de publicar
        if self.conectado and self.mqttc.is_connected():
          topic_final = str(canal).format(self.DongleID)
          #print(f"📡 Publicando en topic final: {topic_final}")
          resultado = self.mqttc.publish(
            topic_final,
            json.dumps(datos_importantes),
            qos=0
          )
          #print(f"✅ Publicación MQTT result: {resultado}")
        # Si no hay conexión, simplemente no enviar (no encolar)
      except Exception as e:
        pass  # Error silenciado para reducir uso de memoria


def imprimir_setspeed_y_vego(canal, datos):
  try:
    set_speed = None

    if 'carControl' in canal:
      set_speed = datos.get("hudControl", {}).get("setSpeed", None)


    # Ruta al nuevo archivo JSON
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_json = os.path.join(ruta_base, "lead_info1.json")

    # Leer JSON existente si existe y no está vacío
    datos_json = {}
    if os.path.exists(ruta_json) and os.path.getsize(ruta_json) > 0:
      with open(ruta_json, "r") as f:
        try:
          datos_json = json.load(f)
        except json.JSONDecodeError:
          datos_json = {}

    # Guardar solo el setSpeed si está presente
    if set_speed is not None:
      datos_json["setSpeed"] = set_speed
      with open(ruta_json, "w") as f:
        json.dump(datos_json, f, indent=2)
        #print("✅ setSpeed guardado correctamente en lead_info1.json")

  except Exception:
    pass
