#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para enviar comandos de intervalos y cambio de carril
a través de MQTT al sistema adripilot.

Uso:
    python test_comandos.py

Este script envía comandos de prueba a los topics MQTT correspondientes
para verificar que la integración funciona correctamente.
"""

import json
import time
import paho.mqtt.client as mqtt
from openpilot.common.params import Params

class TestComandos:
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

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Conectado al broker MQTT para pruebas")
        else:
            print(f"❌ Error de conexión MQTT: {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("🔌 Desconectado del broker MQTT")

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

    def enviar_comando_intervalos(self, activar=True):
        """Envía comando de intervalos."""
        topic = f"telemetry_config/{self.DongleID}/intervalos"
        payload = "true" if activar else "false"

        result = self.mqttc.publish(topic, payload, qos=0)
        if result.rc == 0:
            print(f"📤 Comando intervalos enviado: {payload} a {topic}")
        else:
            print(f"❌ Error al enviar comando intervalos: {result.rc}")

    def enviar_comando_carril_izquierda(self, activar=True):
        """Envía comando de cambio de carril a la izquierda."""
        topic = f"telemetry_config/{self.DongleID}/left"
        payload = "true" if activar else "false"

        result = self.mqttc.publish(topic, payload, qos=0)
        if result.rc == 0:
            print(f"📤 Comando carril izquierda enviado: {payload} a {topic}")
        else:
            print(f"❌ Error al enviar comando carril izquierda: {result.rc}")

    def enviar_comando_carril_derecha(self, activar=True):
        """Envía comando de cambio de carril a la derecha."""
        topic = f"telemetry_config/{self.DongleID}/right"
        payload = "true" if activar else "false"

        result = self.mqttc.publish(topic, payload, qos=0)
        if result.rc == 0:
            print(f"📤 Comando carril derecha enviado: {payload} a {topic}")
        else:
            print(f"❌ Error al enviar comando carril derecha: {result.rc}")

    def ejecutar_pruebas(self):
        """Ejecuta una secuencia de pruebas."""
        print(f"🧪 Iniciando pruebas para DongleID: {self.DongleID}")
        print("=" * 50)

        # Prueba 1: Activar intervalos
        print("\n1️⃣ Probando activación de intervalos...")
        self.enviar_comando_intervalos(True)
        time.sleep(2)

        # Prueba 2: Desactivar intervalos
        print("\n2️⃣ Probando desactivación de intervalos...")
        self.enviar_comando_intervalos(False)
        time.sleep(2)

        # Prueba 3: Cambio de carril a la izquierda
        print("\n3️⃣ Probando cambio de carril a la izquierda...")
        self.enviar_comando_carril_izquierda(True)
        time.sleep(2)

        # Prueba 4: Cancelar cambio de carril
        print("\n4️⃣ Probando cancelación de cambio de carril...")
        self.enviar_comando_carril_izquierda(False)
        time.sleep(2)

        # Prueba 5: Cambio de carril a la derecha
        print("\n5️⃣ Probando cambio de carril a la derecha...")
        self.enviar_comando_carril_derecha(True)
        time.sleep(2)

        # Prueba 6: Cancelar cambio de carril
        print("\n6️⃣ Probando cancelación de cambio de carril...")
        self.enviar_comando_carril_derecha(False)
        time.sleep(2)

        # Prueba 7: Conflicto de carriles (izquierda cuando hay derecha)
        print("\n7️⃣ Probando conflicto de carriles...")
        self.enviar_comando_carril_derecha(True)
        time.sleep(1)
        self.enviar_comando_carril_izquierda(True)  # Esto debería cancelar ambos
        time.sleep(2)

        print("\n✅ Pruebas completadas!")

    def menu_interactivo(self):
        """Menú interactivo para probar comandos individualmente."""
        while True:
            print("\n" + "=" * 50)
            print("🎮 MENÚ DE PRUEBAS DE COMANDOS")
            print("=" * 50)
            print("1. Activar intervalos")
            print("2. Desactivar intervalos")
            print("3. Cambio de carril a la izquierda")
            print("4. Cambio de carril a la derecha")
            print("5. Cancelar cambio de carril")
            print("6. Ejecutar todas las pruebas")
            print("7. Salir")
            print("=" * 50)

            try:
                opcion = input("Selecciona una opción (1-7): ").strip()

                if opcion == "1":
                    self.enviar_comando_intervalos(True)
                elif opcion == "2":
                    self.enviar_comando_intervalos(False)
                elif opcion == "3":
                    self.enviar_comando_carril_izquierda(True)
                elif opcion == "4":
                    self.enviar_comando_carril_derecha(True)
                elif opcion == "5":
                    self.enviar_comando_carril_izquierda(False)
                    self.enviar_comando_carril_derecha(False)
                elif opcion == "6":
                    self.ejecutar_pruebas()
                elif opcion == "7":
                    print("👋 Saliendo...")
                    break
                else:
                    print("❌ Opción no válida")

            except KeyboardInterrupt:
                print("\n👋 Saliendo...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def cerrar(self):
        """Cierra la conexión MQTT."""
        self.mqttc.loop_stop()
        self.mqttc.disconnect()

def main():
    """Función principal."""
    print("🚀 Iniciando script de pruebas de comandos MQTT")

    tester = TestComandos()

    if not tester.conectar():
        print("❌ No se pudo conectar al broker MQTT")
        return

    try:
        # Preguntar si quiere ejecutar todas las pruebas o usar el menú
        print("\n¿Qué quieres hacer?")
        print("1. Ejecutar todas las pruebas automáticamente")
        print("2. Usar menú interactivo")

        opcion = input("Selecciona (1 o 2): ").strip()

        if opcion == "1":
            tester.ejecutar_pruebas()
        elif opcion == "2":
            tester.menu_interactivo()
        else:
            print("❌ Opción no válida, ejecutando pruebas automáticas...")
            tester.ejecutar_pruebas()

    except KeyboardInterrupt:
        print("\n👋 Interrumpido por el usuario")
    finally:
        tester.cerrar()

if __name__ == "__main__":
    main()
