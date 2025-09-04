# Integración de Comandos MQTT en Adripilot

## Descripción

Este documento describe la integración de funcionalidades de **intervalos** y **cambio de carril** en el sistema Adripilot mediante comandos MQTT. La funcionalidad ha sido integrada desde `sicmqtthilo2.py` al sistema `mqtt_envio_general.py` de Adripilot.

## Funcionalidades Integradas

### 1. Control de Intervalos
- **Topic de comando**: `telemetry_config/{DongleID}/intervalos`
- **Valores**: `"true"` (activar) / `"false"` (desactivar)
- **Parámetro del sistema**: `intervalos_toggle`
- **Topic de estado**: `telemetry_mqtt/{DongleID}/intervalos_status`

### 2. Control de Cambio de Carril
- **Topic de comando izquierda**: `telemetry_config/{DongleID}/left`
- **Topic de comando derecha**: `telemetry_config/{DongleID}/right`
- **Valores**: `"true"` (activar) / `"false"` (cancelar)
- **Parámetros del sistema**: `ForceLaneChangeLeft`, `ForceLaneChangeRight`
- **Topic de estado**: `telemetry_mqtt/{DongleID}/lane_change_status`

## Características de Seguridad

### Validación de Toggle de Seguridad
- Los comandos de cambio de carril requieren que el toggle `c_carril` esté activado
- Si `c_carril` está desactivado, los comandos de cambio de carril son rechazados

### Prevención de Conflictos
- No se puede activar cambio a la izquierda si ya hay cambio a la derecha activo
- No se puede activar cambio a la derecha si ya hay cambio a la izquierda activo
- En caso de conflicto, ambos cambios se cancelan automáticamente

## Archivos Modificados

### `mqtt_envio_general.py`
- ✅ Agregado callback `on_message` para manejar comandos MQTT
- ✅ Suscripción a topics de comandos de intervalos y cambio de carril
- ✅ Implementación de validaciones de seguridad
- ✅ Publicación de estados en tiempo real
- ✅ Manejo de reconexión con re-suscripción automática

### `test_comandos.py` (Nuevo)
- ✅ Script de prueba para verificar la funcionalidad
- ✅ Menú interactivo para pruebas individuales
- ✅ Secuencia automática de pruebas

## Uso

### Ejecutar el Sistema Adripilot
```bash
cd /home/drago/Escritorio/OPENPILOTSIC/openpilot/sicuem/adripilot
python mqtt_envio_general.py
```

### Probar Comandos
```bash
cd /home/drago/Escritorio/OPENPILOTSIC/openpilot/sicuem/adripilot
python test_comandos.py
```

## Topics MQTT

### Comandos (Entrada)
- `telemetry_config/{DongleID}/intervalos` - Control de intervalos
- `telemetry_config/{DongleID}/left` - Cambio de carril izquierda
- `telemetry_config/{DongleID}/right` - Cambio de carril derecha

### Estados (Salida)
- `telemetry_mqtt/{DongleID}/intervalos_status` - Estado actual de intervalos
- `telemetry_mqtt/{DongleID}/lane_change_status` - Estado actual de cambio de carril

## Ejemplos de Uso

### Activar Intervalos
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("80.29.2.242", 1883, 60)
client.publish("telemetry_config/TU_DONGLE_ID/intervalos", "true", qos=0)
```

### Cambio de Carril a la Izquierda
```python
client.publish("telemetry_config/TU_DONGLE_ID/left", "true", qos=0)
```

### Cambio de Carril a la Derecha
```python
client.publish("telemetry_config/TU_DONGLE_ID/right", "true", qos=0)
```

### Cancelar Cambio de Carril
```python
client.publish("telemetry_config/TU_DONGLE_ID/left", "false", qos=0)
# o
client.publish("telemetry_config/TU_DONGLE_ID/right", "false", qos=0)
```

## Configuración

### Archivo `config_mqtt.json`
```json
{
  "broker": "80.29.2.242",
  "broker_port": 1883
}
```

### Archivo `canales.json`
El archivo de canales no requiere modificaciones para esta funcionalidad.

## Logs y Debugging

El sistema genera logs detallados para facilitar el debugging:

- `🎯` - Comando recibido
- `✅` - Comando ejecutado exitosamente
- `🛑` - Comando cancelado o bloqueado
- `⚠️` - Advertencia o conflicto
- `❌` - Error
- `📡` - Estado publicado

## Compatibilidad

Esta integración es compatible con:
- ✅ Sistema de parámetros de OpenPilot
- ✅ Broker MQTT existente
- ✅ Funcionalidad original de `sicmqtthilo2.py`
- ✅ Sistema de telemetría de Adripilot

## Notas Importantes

1. **DongleID**: El sistema utiliza automáticamente el DongleID del dispositivo
2. **Seguridad**: Los comandos de cambio de carril requieren el toggle `c_carril` activado
3. **Reconexión**: El sistema maneja automáticamente las reconexiones MQTT
4. **Estados**: Los estados se publican automáticamente en tiempo real
5. **Conflictos**: El sistema previene conflictos entre cambios de carril

## Troubleshooting

### Comandos no funcionan
1. Verificar que el broker MQTT esté funcionando
2. Confirmar que el DongleID sea correcto
3. Revisar los logs para errores específicos

### Cambio de carril bloqueado
1. Verificar que el toggle `c_carril` esté activado
2. Revisar los logs para mensajes de seguridad

### Reconexión MQTT
1. El sistema se reconecta automáticamente
2. Los topics se re-suscriben automáticamente
3. Revisar la conectividad de red
