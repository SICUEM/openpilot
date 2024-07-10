#!/usr/bin/bash

# Función para verificar la conexión a Internet
function check_internet() {
    while true; do
        ping -c 1 google.com &> /dev/null
        if [ $? -eq 0 ]; then
            echo "Hay conexión a Internet."
            break
        else
            echo "No hay conexión a Internet. Esperando..."
            sleep 5
        fi
    done
}

# Función para verificar/instalar si la biblioteca paho-mqtt está instalada
function install_paho() {
    python -c "import paho.mqtt.client" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "La biblioteca paho-mqtt ya está instalada."
    else
        echo "La biblioteca paho-mqtt no está instalada. Instalando..."
        pip install paho-mqtt
        sudo reboot
    fi
}

# Función para verificar/instalar la librería Kakfa en el sistema
function install_kafka() {
    python -c "from confluent_kafka import Producer" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "La biblioteca paho-mqtt ya está instalada."
    else
        echo "La biblioteca paho-mqtt no está instalada. Instalando..."
        pip install confluent-kafka
        sudo reboot
    fi
}

# Verifica la conexión a Internet
check_internet

# Verifica si la biblioteca paho-mqtt está instalada
install_paho

# Verifica si la biblioteca confluent-kafka está instalada
install_kafka

# /usr/local/pyenv/shims/pip3 install confluent-kafka >> /data/openpilot/install_mix.txt 2> /data/openpilot/error_mix2.txt
