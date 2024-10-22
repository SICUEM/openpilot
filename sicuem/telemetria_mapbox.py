import paho.mqtt.client as mqtt
import json

class TelemetriaMapbox:
  def __init__(self, broker_address="195.235.211.197", port=1883, topic="telemetria/mapbox"):
    self.broker_address = broker_address
    self.port = port
    self.topic = topic
    self.mqtt_client = mqtt.Client()

    # Conexión al broker MQTT
    self.mqtt_client.connect(self.broker_address, self.port, 60)
    self.mqtt_client.loop_start()
    print(f"Conectado al broker MQTT en {self.broker_address}:{self.port}")

  def send_json(self, json_file_path):
    """Envía el archivo JSON a través de MQTT"""
    try:
      with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)
        self.mqtt_client.publish(self.topic, json.dumps(data), qos=0)
        print(f"Archivo JSON enviado a {self.topic}")
    except Exception as e:
      print(f"Error al enviar el archivo JSON: {e}")

  def disconnect(self):
    """Desconecta del broker MQTT"""
    self.mqtt_client.loop_stop()
    self.mqtt_client.disconnect()
    print("Desconectado del broker MQTT")
