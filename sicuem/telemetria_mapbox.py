#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import paho.mqtt.client as mqtt
from threading import Thread

class TelemetriaMapbox:

    def __init__(self, mensaje, config_path='config.json'):
        self.mensaje = mensaje
        self.config_path = config_path
        self.broker_address = self.cargar_configuracion()

        self.mqttc = mqtt.Client()
        # Configuración de callbacks básicos
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect

    def cargar_configuracion(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                broker_ip = config['config']['IpServer']['value']
                print(f"IP del servidor cargada: {broker_ip}")
                return broker_ip
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Error al cargar la configuración: {e}")
            return 'localhost'  # Dirección por defecto si falla la carga

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Conexión exitosa al broker.")
            # Publicación del mensaje al conectarse
            self.mqttc.publish("telemetry_mqtt/mapbox", self.mensaje)
            print(f"Mensaje enviado: {self.mensaje}")
        else:
            print(f"Error en la conexión: código {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("Desconectado del broker.")

    def conectar_y_enviar(self):
        try:
            self.mqttc.connect(self.broker_address, 1883, 60)
            self.mqttc.loop_forever()
        except Exception as e:
            print(f"Error al conectar: {e}")

    def iniciar(self):
        hilo_envio = Thread(target=self.conectar_y_enviar)
        hilo_envio.start()
