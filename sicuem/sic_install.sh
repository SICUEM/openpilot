#!/usr/bin/bash

# Version 2.
# Función para verificar la conexión a Internet
function check_internet() {
    ping -c 3 google.com
    if [ $? -eq 0 ]; then
        echo "Hay conexión a Internet."
    else
        echo "No hay conexión a Internet. Esperando..."
    fi
}

# Función para verificar/instalar si la biblioteca paho-mqtt está instalada
function install_paho() {
    python -c "import paho.mqtt.client"
    if [ $? -eq 0 ]; then
        echo "La biblioteca paho-mqtt ya está instalada."
    else
        echo "La biblioteca paho-mqtt no está instalada. Instalando..."
        python3 -m pip install paho-mqtt
    fi
}

# Verifica la conexión a Internet
check_internet

# Verifica si la biblioteca paho-mqtt está instalada
install_paho
