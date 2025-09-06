#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script específico para verificar que la velocidad se está enviando correctamente
por MQTT desde Adripilot.

Uso:
    python test_velocidad.py
"""

import json
import time
import paho.mqtt.client as mqtt
from openpilot.common.params import Params

class TestVelocidad:
    def __init__(self):
        self.params = Params()
        self.DongleID = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "TestDevice"

        # Cargar configuración MQTT
        with open("config_mqtt.json", "r") as f:
            config = json.load(f)
            self.broker_address = config.get("broker", "localhost")

        self.mqttc = mqtt.Client()
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_message = self.on_message

        self.velocidad_recibida = False
        self.ultima_velocidad = None
        self.contador_mensajes = 0

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Conectado al broker MQTT para verificar velocidad")
            # Suscribirse específicamente a los topics de velocidad
            topics_velocidad = [
                f"telemetry_mqtt/{self.DongleID}/carState",
                f"telemetry_mqtt/{self.DongleID}/controlsState",
                f"telemetry_mqtt/{self.DongleID}/resumen_principal"
            ]

            for topic in topics_velocidad:
                self.mqttc.subscribe(topic, qos=0)
                print(f"📡 Suscrito a: {topic}")
        else:
            print(f"❌ Error de conexión MQTT: {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("🔌 Desconectado del broker MQTT")

    def on_message(self, client, userdata, msg):
        """Procesa los mensajes MQTT recibidos."""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            self.contador_mensajes += 1

            print(f"\n📨 Mensaje #{self.contador_mensajes} recibido en: {topic}")

            if topic.endswith("/carState"):
                self.procesar_car_state(payload)
            elif topic.endswith("/controlsState"):
                self.procesar_controls_state(payload)
            elif topic.endswith("/resumen_principal"):
                self.procesar_resumen(payload)
            else:
                print(f"📦 Otro mensaje: {payload[:100]}...")

        except Exception as e:
            print(f"❌ Error al procesar mensaje: {e}")

    def procesar_car_state(self, payload):
        """Procesa datos de carState para extraer velocidad."""
        try:
            data = json.loads(payload)
            print("🔍 Analizando carState...")

            # Buscar variables de velocidad
            v_ego = data.get("vEgo")
            v_ego_kmh = data.get("vEgo_kmh")
            v_cruise = data.get("vCruise")
            v_cruise_kmh = data.get("vCruise_kmh")

            print(f"   📊 vEgo: {v_ego}")
            print(f"   📊 vEgo_kmh: {v_ego_kmh}")
            print(f"   📊 vCruise: {v_cruise}")
            print(f"   📊 vCruise_kmh: {v_cruise_kmh}")

            if v_ego is not None:
                self.velocidad_recibida = True
                self.ultima_velocidad = {
                    "vEgo": v_ego,
                    "vEgo_kmh": v_ego_kmh,
                    "timestamp": time.time()
                }
                print(f"✅ VELOCIDAD ENCONTRADA: {v_ego:.2f} m/s = {v_ego_kmh:.1f} km/h")
            else:
                print("❌ NO SE ENCONTRÓ vEgo en carState")

            # Mostrar todas las claves disponibles
            print(f"   🔑 Claves disponibles: {list(data.keys())}")

        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar carState: {e}")

    def procesar_controls_state(self, payload):
        """Procesa datos de controlsState para extraer velocidad."""
        try:
            data = json.loads(payload)
            print("🔍 Analizando controlsState...")

            v_ego = data.get("vEgo")
            v_ego_raw = data.get("vEgoRaw")
            v_cruise = data.get("vCruise")

            print(f"   📊 vEgo: {v_ego}")
            print(f"   📊 vEgoRaw: {v_ego_raw}")
            print(f"   📊 vCruise: {v_cruise}")

            if v_ego is not None:
                print(f"✅ VELOCIDAD EN CONTROLS: {v_ego:.2f} m/s")

        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar controlsState: {e}")

    def procesar_resumen(self, payload):
        """Procesa el resumen principal."""
        try:
            data = json.loads(payload)
            print("🔍 Analizando resumen principal...")

            if "velocidad" in data:
                vel = data["velocidad"]
                v_ego = vel.get("vEgo")
                v_ego_kmh = vel.get("vEgo_kmh")

                print(f"   📊 Resumen - vEgo: {v_ego}")
                print(f"   📊 Resumen - vEgo_kmh: {v_ego_kmh}")

                if v_ego is not None:
                    print(f"✅ VELOCIDAD EN RESUMEN: {v_ego:.2f} m/s = {v_ego_kmh:.1f} km/h")

        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar resumen: {e}")

    def conectar(self):
        """Conecta al broker MQTT."""
        try:
            self.mqttc.connect(self.broker_address, 1883, 60)
            self.mqttc.loop_start()
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Error al conectar: {e}")
            return False

    def ejecutar_prueba(self, duracion=30):
        """Ejecuta la prueba por un tiempo determinado."""
        print(f"🧪 Iniciando prueba de velocidad por {duracion} segundos...")
        print(f"🎯 DongleID: {self.DongleID}")
        print("⏱️  Presiona Ctrl+C para detener antes del tiempo")

        try:
            time.sleep(duracion)
        except KeyboardInterrupt:
            print("\n⏹️  Prueba interrumpida por el usuario")

        # Mostrar resultados
        print("\n" + "="*60)
        print("📊 RESULTADOS DE LA PRUEBA DE VELOCIDAD")
        print("="*60)
        print(f"📈 Total de mensajes recibidos: {self.contador_mensajes}")
        print(f"✅ Velocidad recibida: {'SÍ' if self.velocidad_recibida else 'NO'}")

        if self.ultima_velocidad:
            print(f"🚗 Última velocidad: {self.ultima_velocidad['vEgo']:.2f} m/s = {self.ultima_velocidad['vEgo_kmh']:.1f} km/h")
        else:
            print("❌ No se recibió ninguna velocidad")

        print("="*60)

    def cerrar(self):
        """Cierra la conexión MQTT."""
        self.mqttc.loop_stop()
        self.mqttc.disconnect()

def main():
    """Función principal."""
    print("🚀 Iniciando prueba específica de velocidad de Adripilot")

    tester = TestVelocidad()

    if not tester.conectar():
        print("❌ No se pudo conectar al broker MQTT")
        return

    try:
        # Preguntar duración de la prueba
        try:
            duracion = int(input("⏱️  Duración de la prueba en segundos (default: 30): ") or "30")
        except ValueError:
            duracion = 30

        tester.ejecutar_prueba(duracion)

    except KeyboardInterrupt:
        print("\n👋 Interrumpido por el usuario")
    finally:
        tester.cerrar()

if __name__ == "__main__":
    main()
