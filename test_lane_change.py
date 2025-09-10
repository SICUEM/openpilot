#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import json

# Configuración MQTT
BROKER = "80.29.2.242"
PORT = 1883
DONGLE_ID = "UnregisteredDevice"  # Usar el ID que aparece en los logs

def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker MQTT con código: {rc}")
    if rc == 0:
        print("✅ Conexión exitosa")
    else:
        print(f"❌ Error de conexión: {rc}")

def on_message(client, userdata, msg):
    print(f"📨 Mensaje recibido: {msg.topic} -> {msg.payload.decode()}")

def test_lane_change():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # Conectar al broker
        client.connect(BROKER, PORT, 60)
        client.loop_start()

        # Suscribirse a los topics de estado
        client.subscribe(f"telemetry_mqtt/{DONGLE_ID}/lane_change_status")
        client.subscribe(f"telemetry_mqtt/{DONGLE_ID}/intervalos_status")

        time.sleep(2)  # Esperar conexión

        print("\n🧪 Probando comandos de cambio de carril...")

        # Probar cambio a la izquierda
        print("\n1️⃣ Enviando comando: cambio a la izquierda")
        client.publish(f"telemetry_config/{DONGLE_ID}/left", "true", qos=0)
        time.sleep(3)

        # Cancelar cambio
        print("\n2️⃣ Enviando comando: cancelar cambio")
        client.publish(f"telemetry_config/{DONGLE_ID}/left", "false", qos=0)
        time.sleep(3)

        # Probar cambio a la derecha
        print("\n3️⃣ Enviando comando: cambio a la derecha")
        client.publish(f"telemetry_config/{DONGLE_ID}/right", "true", qos=0)
        time.sleep(3)

        # Cancelar cambio
        print("\n4️⃣ Enviando comando: cancelar cambio")
        client.publish(f"telemetry_config/{DONGLE_ID}/right", "false", qos=0)
        time.sleep(3)

        print("\n✅ Pruebas completadas")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    test_lane_change()
