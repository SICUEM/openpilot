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
    self.jsonCanales = "../../sicuem/canales.json"  # Ruta al archivo JSON de configuración de canales
    self.jsonConfig = "../../sicuem/config.json"   # Ruta al archivo JSON de configuración general
    self.espera = 0.5                              # Intervalo de espera predeterminado en segundos
    self.indice_canal = 0                          # Índice inicial para los canales
    self.conectado = False                         # Estado inicial de conexión MQTT
    self.sm = None                                 # Objeto SubMaster para recibir datos (sin inicializar)
    self.pause_event = Event()                     # Evento para pausar operaciones
    self.pause_event.set()                         # Activa el evento inicialmente
    self.stop_event = Event()                      # Evento para detener hilos
    params = Params()                              # Carga de parámetros del sistema
    self.params = params                           # Almacena la referencia a los parámetros
    self.DongleID = params.get("DongleId").decode('utf-8') if params.get("DongleId") else "DongleID"
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
    """
    Configura el cliente MQTT y sus callbacks.

    - Crea una instancia de cliente MQTT.
    - Asocia funciones de callback para manejar eventos de conexión, desconexión y recepción de mensajes.

    Comentarios clave:
    - `on_connect`: Se llama automáticamente cuando el cliente se conecta al broker.
    - `on_disconnect`: Maneja desconexiones, permitiendo reconexiones automáticas.
    - `on_message`: Procesa mensajes recibidos en los tópicos suscritos.
    """
    self.mqttc = mqtt.Client()                      # Inicializa el cliente MQTT
    self.mqttc.on_connect = self.on_connect         # Callback para manejar la conexión
    self.mqttc.on_disconnect = self.on_disconnect   # Callback para manejar la desconexión
    self.mqttc.on_message = self.on_message         # Callback para manejar mensajes recibidos


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




#----------------------------------------------------------------------------------------------- INIT STUFF END

  def start(self) -> int:
    self.reanudar_envio() #TEMPORAL


    #self.cargar_canales()

    if self.lista_suscripciones:
      try:
        self.sm = messaging.SubMaster(
          ['carState', 'controlsState', 'liveCalibration', 'carControl', 'gpsLocationExternal', 'gpsLocation',
           'navInstruction', 'radarState', 'drivingModelData'])
      except Exception:
        self.sm = None



    time.sleep(2)
    hilo_telemetry = Thread(target=self.loop, daemon=True)
    hilo_telemetry.start()
    return 0


#------------------------------------------------------------------------------------------------ FUNCION START END

  def verificar_toggle_canales(self, data_canales):
    """
    Verifica dinámicamente si los canales deben estar habilitados o deshabilitados.
    - Consulta un parámetro (`{canal}_toggle`) para determinar el estado de cada canal.
    - Si el estado actual del canal (`enable`) no coincide con el parámetro, se actualiza.

    Adicional:
    - Imprime un mensaje cada vez que un canal se habilita (`enable = 1`).
    """
    params = Params()  # Objeto para obtener valores de parámetros del sistema

    for item in data_canales['canales']:
      toggle_param_name = f"{item['canal']}_toggle"  # Nombre del parámetro asociado al canal
      try:
        # Obtener el valor del parámetro (True/False)
        toggle_value = params.get_bool(toggle_param_name)

        # Determinar el nuevo estado del canal
        if toggle_value is not None:
          nuevo_estado = 1 if toggle_value else 0

          # Si el estado actual no coincide, actualizarlo
          if item['enable'] != nuevo_estado:
            self.cambiar_enable_canal(item['canal'], nuevo_estado)

            # Imprimir mensaje si el canal se habilita
            if nuevo_estado == 1:
              print(f"Canal habilitado: {item['canal']}")
      except Exception as e:
        print(f"Error al verificar el toggle para {item['canal']}: {e}")

  def setup_mqtt_connection(self):
    """Configura la conexión MQTT y maneja los errores sin bloquear el programa."""
    while not self.stop_event.is_set():
      try:
        self.mqttc.connect(self.broker_address, 1883, 60)
        self.mqttc.subscribe("opmqttsender/messages", qos=0)
        self.mqttc.loop_start()
        self.conectado = True
        print("Conectado al broker MQTT con éxito.")
        break
      except Exception as e:
        print(f"Error al conectar con el broker MQTT: {e}")
        print("Reintentando conexión en 5 segundos...")
        time.sleep(5)  # Reintentar después de 5 segundos

  def signal_handler(self, sig, frame):
    """Manejador de la señal SIGINT para detener el programa de forma controlada."""
    self.cleanup()
    sys.exit(0)


#------------------------------------------------------------------------------------------------ VERIFICAR QUE TOGGLES ESTAN ACTIVADOS

  def cleanup(self):
    """Cierra las conexiones y detiene los hilos de manera segura."""
    self.stop_event.set()  # Señal para detener los hilos
    if self.mqttc:
      self.mqttc.loop_stop()
      self.mqttc.disconnect()
    self.pause_event.set()

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
      print("Conectado al broker MQTT con éxito.")



  def on_disconnect(self, client, userdata, rc):
    """Maneja la desconexión del cliente MQTT y trata de reconectar."""
    self.conectado = False
    print("Desconectado del broker MQTT. Intentando reconectar...")
    self.start_mqtt_thread()

  def on_message(self, client, userdata, msg):
    """Maneja los mensajes recibidos en el tema MQTT."""
    if msg.topic == "opmqttsender/messages":
        message = msg.payload.decode()
        print(f"Mensaje recibido: {message}")
        self.params.put_bool_nonblocking("sender_uem_up", False)
        self.params.put_bool_nonblocking("sender_uem_down", False)
        self.params.put_bool_nonblocking("sender_uem_left", False)
        self.params.put_bool_nonblocking("sender_uem_right", False)
        if message == "up":
            self.params.put_bool_nonblocking("sender_uem_up", True)
        elif message == "down":
            self.params.put_bool_nonblocking("sender_uem_down", True)
        elif message == "left":
            self.params.put_bool_nonblocking("sender_uem_left", True)
        elif message == "right":
            self.params.put_bool_nonblocking("sender_uem_right", True)




  def cambiar_enable_canal(self, canal, estado):
    with open(self.jsonCanales, 'r') as f:
      dataCanales = json.load(f)
    for item in dataCanales['canales']:
      if item['canal'] == canal:
        item['enable'] = estado
        break
    with open(self.jsonCanales, 'w') as f:
      json.dump(dataCanales, f, indent=4)
    self.cargar_canales()

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

  def pausar_envio(self):
    self.pause_event.clear()
    self.dataConfig['config']['send']['value'] = 0

  def reanudar_envio(self):
    self.pause_event.set()
    #self.dataConfig['config']['send']['value'] = 1

  def conexion(self, url='http://www.google.com', intervalo=5):
    """Verifica la conexión a Internet periódicamente en un hilo separado."""
    def check_connection():
      while not self.stop_event.is_set():
        try:
          response = requests.get(url, timeout=5)
          if response.status_code == 200:
            print("Conexión a Internet exitosa.")
        except requests.ConnectionError:
          print(f"No hay conexión a Internet. Intentando nuevamente en {intervalo} segundos...")
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

    return {
      "latitude": latitude,
      "longitude": longitude,
      "altitude": altitude
    }



  def haversine_distance(self,lat1, lon1, lat2, lon2):
    # Radio de la Tierra en metros
    R = 6371000
    # Convertir coordenadas de grados a radianes
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Calcular la distancia usando la fórmula haversine
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

  def enviar_estado_archivo_mapbox(self):
    # Obtener la posición GPS actual desde el canal 'gpsLocationExternal'
    gps_data = self.obtener_gps_location()
    current_lat = gps_data.get('latitude')
    current_lon = gps_data.get('longitude')
    #print(current_lat)
    #print(current_lon)

    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_archivo = os.path.join(ruta_actual, "../system/manager/mapbox_response.json")

    if os.path.exists(ruta_archivo):

      try:
        with open(ruta_archivo, 'r') as archivo:
          data = json.load(archivo)
          closest_maneuvers = {
            "roundabout": {"distance": float('inf'), "latitude": None, "longitude": None},
            "intersection": {"distance": float('inf'), "latitude": None, "longitude": None},
            "merge": {"distance": float('inf'), "latitude": None, "longitude": None}
          }

          # Analizar las rutas y encontrar maniobras específicas
          if "routes" in data and len(data["routes"]) > 0:
            for leg in data["routes"][0].get("legs", []):
              for step in leg.get("steps", []):
                maneuver_type = step.get("maneuver", {}).get("type", "")
                distance = step.get("distance", 0)
                maneuver_lat = step.get("maneuver", {}).get("location", [None, None])[1]
                maneuver_lon = step.get("maneuver", {}).get("location", [None, None])[0]

                if maneuver_type in closest_maneuvers:
                  # Calcular la distancia manualmente si las coordenadas son válidas
                  if current_lat is not None and current_lon is not None and maneuver_lat is not None and maneuver_lon is not None:
                    # Conversión de coordenadas a radianes
                    lat1 = current_lat * (3.141592653589793 / 180)
                    lon1 = current_lon * (3.141592653589793 / 180)
                    lat2 = maneuver_lat * (3.141592653589793 / 180)
                    lon2 = maneuver_lon * (3.141592653589793 / 180)

                    # Fórmula de Haversine
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = (math.sin(dlat / 2) ** 2 +
                         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    R = 6371000  # Radio de la Tierra en metros
                    calculated_distance = R * c

                    # Actualizar la distancia si es más cercana

                    closest_maneuvers[maneuver_type]["distance"] = calculated_distance
                    closest_maneuvers[maneuver_type]["latitude"] = maneuver_lat
                    closest_maneuvers[maneuver_type]["longitude"] = maneuver_lon
                    #print(calculated_distance)


          # Establecer las distancias en Params, enviando -1 si no se encuentra ninguna maniobra
          self.params.put("roundabout_distance",
                          str(closest_maneuvers["roundabout"]["distance"]) if closest_maneuvers["roundabout"][
                                                                                "distance"] != float('inf') else "-1")
          self.params.put("intersection_distance",
                          str(closest_maneuvers["intersection"]["distance"]) if closest_maneuvers["intersection"][
                                                                                  "distance"] != float('inf') else "-1")
          self.params.put("merge_distance",
                          str(closest_maneuvers["merge"]["distance"]) if closest_maneuvers["merge"][
                                                                           "distance"] != float('inf') else "-1")

          # Preparar el contenido para MQTT
          contenido = (
            f"Roundabout distance: {self.params.get('roundabout_distance').decode('utf-8')} m\n"
            f"Intersection distance: {self.params.get('intersection_distance').decode('utf-8')} m\n"
            f"Merge distance: {self.params.get('merge_distance').decode('utf-8')} m"
          )
          if not self.params.get_bool("mapbox_toggle"):
            print("mapbox desactivado")
          else:
            #print("envia mapbox distancia")
            self.mqttc.publish("telemetry_mqtt/mapbox_status", contenido, qos=0)
      except Exception as e:
        print(f"Error al leer el archivo: {e}")
    else:
      pass

  def loop(self):
    self.conexion()
    hilo_ping = Thread(target=self.loopPing, daemon=True)
    hilo_ping.start()
    while not self.stop_event.is_set():
      self.pause_event.wait()
      self.cargar_canales()
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
              self.mqttc.publish(
                str(canal_actual['topic']).format(self.DongleID),
                json.dumps(datos_importantes),
                qos=0
              )
            except KeyError:
              continue

      self.enviar_estado_archivo_mapbox()
      time.sleep(self.espera)

  def loopPing(self):
    """Bucle que publica mensajes de ping periódicamente sin bloquear."""
    while not self.stop_event.is_set():
      self.pause_event.wait()
      self.mqttc.publish("telemetry_config/ping", str(time.time()), qos=0)
      time.sleep(3)




