# Telemetría Completa de Adripilot

## Descripción

Este documento detalla todos los datos de telemetría que ahora envía el sistema **Adripilot** a través de MQTT. Se ha integrado la funcionalidad completa de `sicmqtthilo2.py` con mejoras adicionales para proporcionar telemetría en tiempo real del vehículo.

## Canales de Telemetría Disponibles

### 1. **carState** - Estado del Vehículo
**Topic**: `telemetry_mqtt/{DongleID}/carState`

**Datos Principales**:
- `vEgo` - Velocidad actual del vehículo (m/s)
- `vEgo_kmh` - Velocidad actual del vehículo (km/h) - **CALCULADO**
- `aEgo` - Aceleración actual del vehículo (m/s²)
- `aEgo_ms2` - Aceleración actual del vehículo (m/s²) - **CALCULADO**
- `vCruise` - Velocidad de crucero configurada (m/s)
- `vCruise_kmh` - Velocidad de crucero configurada (km/h) - **CALCULADO**
- `cruiseState` - Estado del control de crucero
- `standstill` - Vehículo detenido (true/false)
- `gasPressed` - Pedal de acelerador presionado (true/false)
- `brakePressed` - Pedal de freno presionado (true/false)
- `steeringAngleDeg` - Ángulo de dirección (grados)
- `steeringTorque` - Par de dirección
- `steeringPressed` - Volante presionado (true/false)
- `leftBlinker` - Intermitente izquierdo activo (true/false)
- `rightBlinker` - Intermitente derecho activo (true/false)
- `leftBlindspot` - Punto ciego izquierdo detectado (true/false)
- `rightBlindspot` - Punto ciego derecho detectado (true/false)
- `gearShifter` - Posición de la palanca de cambios
- `engineRPM` - RPM del motor
- `canValid` - Datos CAN válidos (true/false)
- `steerFaultTemporary` - Fallo temporal de dirección (true/false)
- `steerFaultPermanent` - Fallo permanente de dirección (true/false)

### 2. **controlsState** - Estado de Control del Sistema
**Topic**: `telemetry_mqtt/{DongleID}/controlsState`

**Datos Principales**:
- `active` - Sistema de control activo (true/false)
- `vCruise` - Velocidad de crucero del sistema (m/s)
- `uiSpeed` - Velocidad mostrada en la interfaz (m/s)
- `speedLimit` - Límite de velocidad actual (km/h)
- `longControlState` - Estado del control longitudinal
- `vPid` - Velocidad del controlador PID (m/s)
- `vTargetLead` - Velocidad objetivo con vehículo líder (m/s)
- `upAccelCmd` - Comando de aceleración hacia arriba
- `uiAccelCmd` - Comando de aceleración de la interfaz
- `ufAccelCmd` - Comando de aceleración final
- `aEgo` - Aceleración actual (m/s²)
- `aTarget` - Aceleración objetivo (m/s²)
- `aTargetMin` - Aceleración objetivo mínima (m/s²)
- `aTargetMax` - Aceleración objetivo máxima (m/s²)
- `jerkFactor` - Factor de suavidad
- `gpsPlannerActive` - Planificador GPS activo (true/false)
- `saturated` - Sistema saturado (true/false)
- `hasLead` - Vehículo líder detectado (true/false)
- `experimentalMode` - Modo experimental activo (true/false)
- `personality` - Personalidad del sistema de conducción

**Alertas del Sistema**:
- `alertText1` - Texto de alerta principal
- `alertText2` - Texto de alerta secundario
- `alertSize` - Tamaño de la alerta
- `alertStatus` - Estado de la alerta
- `alertBlinkingRate` - Velocidad de parpadeo de la alerta
- `alertType` - Tipo de alerta
- `alertSound` - Sonido de alerta

### 3. **carControl** - Control del Vehículo
**Topic**: `telemetry_mqtt/{DongleID}/carControl`

**Datos Principales**:
- `actuators` - Actuadores del vehículo
- `hudControl` - Control del HUD (Head-Up Display)
  - `setSpeed` - Velocidad configurada (m/s)
  - `setSpeed_kmh` - Velocidad configurada (km/h) - **CALCULADO**
- `active` - Control activo (true/false)

### 4. **gpsLocationExternal** - Ubicación GPS Externa
**Topic**: `telemetry_mqtt/{DongleID}/gpsLocationExternal`

**Datos Principales**:
- `latitude` - Latitud GPS
- `longitude` - Longitud GPS
- `altitude` - Altitud GPS
- `gps_valid` - Datos GPS válidos (true/false) - **CALCULADO**
- `gps_coords` - Coordenadas formateadas - **CALCULADO**

### 5. **gpsLocation** - Ubicación GPS Interna
**Topic**: `telemetry_mqtt/{DongleID}/gpsLocation`

**Datos Principales**:
- `latitude` - Latitud GPS
- `longitude` - Longitud GPS
- `altitude` - Altitud GPS
- `speed` - Velocidad GPS (m/s)
- `bearing` - Dirección GPS (radianes)
- `accuracy` - Precisión GPS (metros)
- `timestamp` - Timestamp GPS
- `source` - Fuente de datos GPS
- `vNED` - Velocidad en coordenadas NED
- `bearingDeg` - Dirección GPS (grados)
- `speedAccuracy` - Precisión de velocidad GPS
- `bearingAccuracy` - Precisión de dirección GPS

### 6. **liveCalibration** - Calibración en Vivo
**Topic**: `telemetry_mqtt/{DongleID}/liveCalibration`

**Datos Principales**:
- `calStatus` - Estado de calibración
- `calPerc` - Porcentaje de calibración
- `calValid` - Calibración válida (true/false)
- `calAge` - Edad de la calibración

### 7. **navInstruction** - Instrucciones de Navegación
**Topic**: `telemetry_mqtt/{DongleID}/navInstruction`

**Datos Principales**:
- `distanceRemaining` - Distancia restante (metros)
- `maneuverDistance` - Distancia a la próxima maniobra (metros)
- `speedLimit` - Límite de velocidad (km/h)
- `timeRemaining` - Tiempo restante (segundos)

### 8. **radarState** - Estado del Radar
**Topic**: `telemetry_mqtt/{DongleID}/radarState`

**Datos Principales**:
- `dRel` - Distancia relativa al vehículo líder (metros)
- `vRel` - Velocidad relativa al vehículo líder (m/s)
- `aRel` - Aceleración relativa al vehículo líder (m/s²)
- `vLead` - Velocidad del vehículo líder (m/s)
- `yRel` - Posición lateral relativa (metros)
- `aLeadK` - Constante de aceleración del líder
- `aLeadTau` - Constante de tiempo del líder
- `status` - Estado del radar
- `radarErrors` - Errores del radar
- `canErrors` - Errores CAN
- `radarCanError` - Error de comunicación radar-CAN

### 9. **drivingModelData** - Datos del Modelo de Conducción
**Topic**: `telemetry_mqtt/{DongleID}/drivingModelData`

**Datos Principales**:
- `laneLineMeta` - Metadatos de líneas de carril
- `laneLines` - Líneas de carril detectadas
- `roadEdges` - Bordes de carretera detectados
- `laneLineProbs` - Probabilidades de líneas de carril
- `laneLineStds` - Desviaciones estándar de líneas de carril
- `laneLineDists` - Distancias de líneas de carril

## Resumen de Telemetría Principal

**Topic**: `telemetry_mqtt/{DongleID}/resumen_principal`

Este topic especial envía un resumen consolidado de los datos más importantes cada 5 segundos:

```json
{
  "dongle_id": "TU_DONGLE_ID",
  "timestamp": 1234567890.123,
  "velocidad": {
    "vEgo": 25.5,
    "vEgo_kmh": 91.8,
    "vCruise": 30.0,
    "vCruise_kmh": 108.0,
    "standstill": false
  },
  "aceleracion": {
    "aEgo": 1.2,
    "aEgo_ms2": 1.2,
    "gasPressed": false,
    "brakePressed": false
  },
  "gps": {
    "latitude": 40.4168,
    "longitude": -3.7038,
    "altitude": 667.0,
    "gps_valid": true
  },
  "control": {
    "setSpeed": 30.0,
    "setSpeed_kmh": 108.0,
    "active": true
  },
  "radar": {
    "dRel": 45.2,
    "vRel": -2.1,
    "aRel": 0.5,
    "vLead": 23.4,
    "hasLead": true
  }
}
```

## Comandos de Control

### Intervalos
- **Topic**: `telemetry_config/{DongleID}/intervalos`
- **Valores**: `"true"` (activar) / `"false"` (desactivar)
- **Estado**: `telemetry_mqtt/{DongleID}/intervalos_status`

### Cambio de Carril
- **Izquierda**: `telemetry_config/{DongleID}/left`
- **Derecha**: `telemetry_config/{DongleID}/right`
- **Valores**: `"true"` (activar) / `"false"` (cancelar)
- **Estado**: `telemetry_mqtt/{DongleID}/lane_change_status`

## Características Especiales

### 1. **Datos Calculados**
- Conversiones automáticas de unidades (m/s ↔ km/h)
- Validación de datos GPS
- Coordenadas formateadas para fácil lectura
- Timestamps para sincronización

### 2. **Validaciones de Seguridad**
- Verificación de toggles de seguridad
- Prevención de conflictos en cambio de carril
- Validación de datos antes del envío

### 3. **Reconexión Automática**
- Reconexión automática MQTT
- Re-suscripción automática a topics
- Manejo robusto de errores de red

### 4. **Filtrado Inteligente**
- Solo se envían datos cuando hay cambios
- Filtrado por claves importantes configuradas
- Optimización del ancho de banda

## Frecuencia de Envío

- **Datos individuales**: En tiempo real cuando hay cambios
- **Resumen principal**: Cada 5 segundos
- **Comandos de control**: Inmediato
- **Estados de control**: Inmediato

## Configuración

### Archivo `canales.json`
Configura qué datos se envían y con qué frecuencia.

### Archivo `config_mqtt.json`
Configura la conexión al broker MQTT.

## Uso Recomendado

1. **Monitoreo en tiempo real**: Usar los topics individuales
2. **Dashboards**: Usar el resumen principal
3. **Control remoto**: Usar los topics de comandos
4. **Análisis histórico**: Almacenar todos los datos

## Troubleshooting

### Datos no llegan
1. Verificar conexión MQTT
2. Confirmar que los canales están habilitados
3. Revisar logs del sistema

### Datos incorrectos
1. Verificar calibración del sistema
2. Revisar estado de los sensores
3. Confirmar configuración de canales

### Rendimiento
1. Ajustar frecuencia de envío
2. Filtrar datos innecesarios
3. Optimizar configuración de red
