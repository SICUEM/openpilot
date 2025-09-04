#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la telemetría completa de Adripilot.

Este script se conecta al broker MQTT y escucha todos los topics de telemetría
para verificar que los datos se están enviando correctamente.

Uso:
    python test_telemetria.py
"""

import json
import time
import paho.mqtt.client as mqtt
from openpilot.common.params import Params

class TestTelemetria:
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

        # Contadores para estadísticas
        self.contadores = {}
        self.ultimos_datos = {}

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Conectado al broker MQTT para pruebas de telemetría")
            # Suscribirse a todos los topics de telemetría
            self.suscribir_topics()
        else:
            print(f"❌ Error de conexión MQTT: {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("🔌 Desconectado del broker MQTT")

    def suscribir_topics(self):
        """Se suscribe a todos los topics de telemetría."""
        topics = [
            f"telemetry_mqtt/{self.DongleID}/carState",
            f"telemetry_mqtt/{self.DongleID}/controlsState",
            f"telemetry_mqtt/{self.DongleID}/carControl",
            f"telemetry_mqtt/{self.DongleID}/gpsLocationExternal",
            f"telemetry_mqtt/{self.DongleID}/gpsLocation",
            f"telemetry_mqtt/{self.DongleID}/liveCalibration",
            f"telemetry_mqtt/{self.DongleID}/navInstruction",
            f"telemetry_mqtt/{self.DongleID}/radarState",
            f"telemetry_mqtt/{self.DongleID}/drivingModelData",
            f"telemetry_mqtt/{self.DongleID}/resumen_principal",
            f"telemetry_mqtt/{self.DongleID}/intervalos_status",
            f"telemetry_mqtt/{self.DongleID}/lane_change_status"
        ]

        for topic in topics:
            self.mqttc.subscribe(topic, qos=0)
            print(f"📡 Suscrito a: {topic}")

    def on_message(self, client, userdata, msg):
        """Procesa los mensajes MQTT recibidos."""
        try:
            topic = msg.topic
            payload = msg.payload.decode()

            # Contar mensajes por topic
            if topic not in self.contadores:
                self.contadores[topic] = 0
            self.contadores[topic] += 1

            # Procesar según el tipo de topic
            if topic.endswith("/resumen_principal"):
                self.procesar_resumen_principal(payload)
            elif topic.endswith("/carState"):
                self.procesar_car_state(payload)
            elif topic.endswith("/controlsState"):
                self.procesar_controls_state(payload)
            elif topic.endswith("/carControl"):
                self.procesar_car_control(payload)
            elif topic.endswith("/gpsLocationExternal"):
                self.procesar_gps_external(payload)
            elif topic.endswith("/gpsLocation"):
                self.procesar_gps_internal(payload)
            elif topic.endswith("/radarState"):
                self.procesar_radar_state(payload)
            else:
                self.procesar_generico(topic, payload)

        except Exception as e:
            print(f"❌ Error al procesar mensaje: {e}")

    def procesar_resumen_principal(self, payload):
        """Procesa el resumen principal de telemetría."""
        try:
            data = json.loads(payload)
            print("\n" + "="*60)
            print("📊 RESUMEN PRINCIPAL DE TELEMETRÍA")
            print("="*60)

            if "velocidad" in data:
                vel = data["velocidad"]
                print(f"🚗 Velocidad: {vel.get('vEgo_kmh', 0):.1f} km/h")
                print(f"🎯 Crucero: {vel.get('vCruise_kmh', 0):.1f} km/h")
                print(f"⏹️  Detenido: {'Sí' if vel.get('standstill', False) else 'No'}")

            if "aceleracion" in data:
                acc = data["aceleracion"]
                print(f"⚡ Aceleración: {acc.get('aEgo_ms2', 0):.2f} m/s²")
                print(f"🦶 Gas: {'Sí' if acc.get('gasPressed', False) else 'No'}")
                print(f"🛑 Freno: {'Sí' if acc.get('brakePressed', False) else 'No'}")

            if "gps" in data:
                gps = data["gps"]
                print(f"📍 GPS: {gps.get('latitude', 0):.6f}, {gps.get('longitude', 0):.6f}")
                print(f"🏔️  Altitud: {gps.get('altitude', 0):.1f} m")
                print(f"✅ GPS Válido: {'Sí' if gps.get('gps_valid', False) else 'No'}")

            if "control" in data:
                ctrl = data["control"]
                print(f"🎛️  SetSpeed: {ctrl.get('setSpeed_kmh', 0):.1f} km/h")
                print(f"🟢 Activo: {'Sí' if ctrl.get('active', False) else 'No'}")

            if "radar" in data:
                radar = data["radar"]
                print(f"📡 Distancia líder: {radar.get('dRel', 0):.1f} m")
                print(f"🚗 Velocidad líder: {radar.get('vLead', 0):.1f} m/s")
                print(f"👁️  Tiene líder: {'Sí' if radar.get('hasLead', False) else 'No'}")

            print("="*60)

        except json.JSONDecodeError:
            print("❌ Error al decodificar resumen principal")

    def procesar_car_state(self, payload):
        """Procesa datos de carState."""
        try:
            data = json.loads(payload)
            self.ultimos_datos["carState"] = data

            # Mostrar datos importantes
            v_ego = data.get("vEgo_kmh", data.get("vEgo", 0) * 3.6)
            a_ego = data.get("aEgo_ms2", data.get("aEgo", 0))
            print(f"🚗 CarState: {v_ego:.1f} km/h, {a_ego:.2f} m/s²")

        except json.JSONDecodeError:
            print("❌ Error al decodificar carState")

    def procesar_controls_state(self, payload):
        """Procesa datos de controlsState."""
        try:
            data = json.loads(payload)
            self.ultimos_datos["controlsState"] = data

            # Mostrar datos importantes
            active = data.get("active", False)
            v_cruise = data.get("vCruise", 0) * 3.6
            print(f"🎛️  ControlsState: Activo={active}, Crucero={v_cruise:.1f} km/h")

        except json.JSONDecodeError:
            print("❌ Error al decodificar controlsState")

    def procesar_car_control(self, payload):
        """Procesa datos de carControl."""
        try:
            data = json.loads(payload)
            self.ultimos_datos["carControl"] = data

            # Extraer setSpeed del hudControl
            hud = data.get("hudControl", {})
            set_speed = hud.get("setSpeed", 0) * 3.6 if isinstance(hud, dict) else 0
            print(f"🎮 CarControl: SetSpeed={set_speed:.1f} km/h")

        except json.JSONDecodeError:
            print("❌ Error al decodificar carControl")

    def procesar_gps_external(self, payload):
        """Procesa datos de GPS externo."""
        try:
            data = json.loads(payload)
            self.ultimos_datos["gpsExternal"] = data

            lat = data.get("latitude", 0)
            lon = data.get("longitude", 0)
            gps_valid = data.get("gps_valid", False)
            print(f"📍 GPS Ext: {lat:.6f}, {lon:.6f} (Válido: {gps_valid})")

        except json.JSONDecodeError:
            print("❌ Error al decodificar GPS externo")

    def procesar_gps_internal(self, payload):
        """Procesa datos de GPS interno."""
        try:
            data = json.loads(payload)
            self.ultimos_datos["gpsInternal"] = data

            lat = data.get("latitude", 0)
            lon = data.get("longitude", 0)
            speed = data.get("speed", 0) * 3.6
            print(f"📍 GPS Int: {lat:.6f}, {lon:.6f}, {speed:.1f} km/h")

        except json.JSONDecodeError:
            print("❌ Error al decodificar GPS interno")

    def procesar_radar_state(self, payload):
        """Procesa datos de radar."""
        try:
            data = json.loads(payload)
            self.ultimos_datos["radarState"] = data

            d_rel = data.get("dRel", 0)
            v_rel = data.get("vRel", 0)
            has_lead = d_rel > 0
            print(f"📡 Radar: Distancia={d_rel:.1f}m, Vel.Rel={v_rel:.1f}m/s, Líder={has_lead}")

        except json.JSONDecodeError:
            print("❌ Error al decodificar radar")

    def procesar_generico(self, topic, payload):
        """Procesa topics genéricos."""
        try:
            data = json.loads(payload)
            topic_name = topic.split("/")[-1]
            print(f"📦 {topic_name}: {len(data)} campos")

        except json.JSONDecodeError:
            print(f"📦 {topic}: {payload[:50]}...")

    def mostrar_estadisticas(self):
        """Muestra estadísticas de los mensajes recibidos."""
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS DE TELEMETRÍA")
        print("="*60)

        total_mensajes = sum(self.contadores.values())
        print(f"📈 Total de mensajes recibidos: {total_mensajes}")
        print("\n📋 Mensajes por topic:")

        for topic, count in sorted(self.contadores.items()):
            topic_name = topic.split("/")[-1]
            print(f"   {topic_name}: {count} mensajes")

        print("="*60)

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

    def ejecutar_prueba(self, duracion=60):
        """Ejecuta la prueba por un tiempo determinado."""
        print(f"🧪 Iniciando prueba de telemetría por {duracion} segundos...")
        print(f"🎯 DongleID: {self.DongleID}")
        print("⏱️  Presiona Ctrl+C para detener antes del tiempo")

        try:
            time.sleep(duracion)
        except KeyboardInterrupt:
            print("\n⏹️  Prueba interrumpida por el usuario")

        self.mostrar_estadisticas()

    def cerrar(self):
        """Cierra la conexión MQTT."""
        self.mqttc.loop_stop()
        self.mqttc.disconnect()

def main():
    """Función principal."""
    print("🚀 Iniciando prueba de telemetría de Adripilot")

    tester = TestTelemetria()

    if not tester.conectar():
        print("❌ No se pudo conectar al broker MQTT")
        return

    try:
        # Preguntar duración de la prueba
        try:
            duracion = int(input("⏱️  Duración de la prueba en segundos (default: 60): ") or "60")
        except ValueError:
            duracion = 60

        tester.ejecutar_prueba(duracion)

    except KeyboardInterrupt:
        print("\n👋 Interrumpido por el usuario")
    finally:
        tester.cerrar()

if __name__ == "__main__":
    main()
