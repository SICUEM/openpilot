#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import json
from common.params_pyx import Params

# Configuración MQTT
BROKER = "80.29.2.242"
PORT = 1883
DONGLE_ID = "UnregisteredDevice"

def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker MQTT con código: {rc}")
    if rc == 0:
        print("✅ Conexión exitosa")
    else:
        print(f"❌ Error de conexión: {rc}")

def on_message(client, userdata, msg):
    print(f"📨 Mensaje recibido: {msg.topic} -> {msg.payload.decode()}")

def check_params():
    """Verifica el estado actual de los parámetros"""
    params = Params()
    left = params.get_bool("ForceLaneChangeLeft")
    right = params.get_bool("ForceLaneChangeRight")
    c_carril = params.get_bool("c_carril")
    print(f"📊 Parámetros: c_carril={c_carril}, ForceLaneChangeLeft={left}, ForceLaneChangeRight={right}")
    return left, right, c_carril

def test_lane_change_complete():
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
        
        print("\n🧪 Prueba completa de cambio de carril...")
        print("=" * 50)
        
        # Verificar estado inicial
        print("\n1️⃣ Estado inicial:")
        check_params()
        
        # Probar cambio a la izquierda
        print("\n2️⃣ Enviando comando: cambio a la izquierda")
        client.publish(f"telemetry_config/{DONGLE_ID}/left", "true", qos=0)
        time.sleep(2)
        
        print("   Estado después del comando:")
        check_params()
        
        # Esperar y verificar si se procesó
        print("\n3️⃣ Esperando procesamiento (5 segundos)...")
        for i in range(5):
            time.sleep(1)
            left, right, c_carril = check_params()
            if not left:  # Si se procesó, debería volver a False
                print(f"   ✅ Parámetro procesado en {i+1} segundos")
                break
        else:
            print("   ⚠️ Parámetro no se procesó automáticamente")
        
        # Cancelar cambio
        print("\n4️⃣ Enviando comando: cancelar cambio")
        client.publish(f"telemetry_config/{DONGLE_ID}/left", "false", qos=0)
        time.sleep(2)
        
        print("   Estado final:")
        check_params()
        
        print("\n✅ Prueba completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    test_lane_change_complete()
