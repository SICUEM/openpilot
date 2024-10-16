#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import signal
import sys
from threading import Event
import paho.mqtt.client as mqtt

class TelemetriaMapbox:

    def __init__(self):
        # Inicialización de atributos y configuración de MQTT
        signal.signal(signal.SIGINT, self.signal_handler)
        self.pause_event = Event()
        self.pause_event.set()

        # Configura la dirección del broker MQTT (deberías actualizar este valor con la correcta)
        self.broker_address = "mqtt_broker_address"  # Cambia esto a la dirección de tu broker MQTT
        self.mqttc = mqtt.Client("TelemetriaMapboxClient")  # Identificador del cliente MQTT
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_subscribe = self.on_subscribe
        self.mqttc.on_message = self.on_message

        # Intentar conectar con el broker MQTT
        try:
            self.mqttc.connect(self.broker_address, 1883, 60)
            self.mqttc.loop_start()  # Inicia el bucle para manejar mensajes
            print("Conexión MQTT establecida correctamente")
        except Exception as e:
            print(f"Error de conexión con MQTT: {e}")

    def signal_handler(self, sig, frame):
        """Manejador de la señal SIGINT para detener el programa de forma controlada."""
        print('Recibido SIGINT (CTRL+C), cerrando el programa de manera controlada...')
        self.mqttc.loop_stop()  # Detiene el bucle de MQTT
        sys.exit(0)

    def on_connect(self, mqttc, obj, flags, rc):
        """Función que se ejecuta cuando el cliente se conecta al broker MQTT."""
        print(f"Conectado a MQTT con código de resultado: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Función que se ejecuta cuando el cliente se desconecta del broker MQTT."""
        print(f"Desconectado de MQTT con código de resultado: {rc}")

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        """Función que se ejecuta cuando la suscripción se realiza correctamente."""
        print("Suscripción exitosa")

    def on_message(self, mqttc, obj, msg):
        """Función que maneja los mensajes recibidos del broker MQTT."""
        print(f"Mensaje recibido en el topic {msg.topic}: {msg.payload}")

    def enviar_telemetria(self, json_data):
        """Función para enviar el JSON de telemetría por MQTT."""
        try:
            # Convertir el JSON a string para enviarlo por MQTT
            json_str = json.dumps(json_data)

            # Publicar el JSON en el topic de telemetría, ej. "telemetria/mapbox"
            self.mqttc.publish("telemetria/mapbox", json_str)
            print(f"Enviando datos de telemetría: {json_str}")

        except Exception as e:
            print(f"Error al enviar la telemetría: {e}")

# Ejemplo de uso directo:
# Si quisieras probar esta clase directamente, puedes pasarle un JSON como este.
if __name__ == "__main__":
    # Ejemplo de JSON para pruebas
    test_json = {
        "routes": [
            {
                "distance": 550.246,
                "duration": 192.969,
                "legs": [
                    {
                        "annotation": {"maxspeed": [{"unknown": True}]},
                        "steps": [
                            {
                                "maneuver": {
                                    "type": "depart",
                                    "location": [-3.919654, 40.375375]
                                },
                                "geometry": {
                                    "coordinates": [[-3.919654, 40.375375], [-3.919479, 40.375537]],
                                    "type": "LineString"
                                },
                                "distance": 23.345,
                                "duration": 5.603
                            }
                        ]
                    }
                ]
            }
        ],
        "waypoints": [
            {"location": [-3.919654, 40.375375]},
            {"location": [-3.919183, 40.373396]}
        ],
        "code": "Ok",
        "uuid": "uBUxxudaMKQO2lc03IXuCHzSAjrZF608Q4vWluhXHpD1bab3Qm-9Ug=="
    }

    # Inicializa TelemetriaMapbox y envía el JSON de prueba
    telemetria = TelemetriaMapbox()
    telemetria.enviar_telemetria(test_json)
