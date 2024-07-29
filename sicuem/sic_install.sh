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

# Función para verificar/instalar la librería confluent-kafka en el sistema
function install_confluent_kafka() {
    python -c "from confluent_kafka import Producer" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "La biblioteca confluent-kafka ya está instalada."
    else
        echo "La biblioteca confluent-kafka no está instalada. Instalando dependencias del sistema..."
        sudo apt-get update
        sudo apt-get install -y librdkafka-dev
        echo "Instalando la biblioteca confluent-kafka..."
        pip install confluent-kafka
    fi
}

# Función para verificar/instalar la librería kafka-python en el sistema
function install_kafka_python() {
    python -c "import kafka" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "La biblioteca kafka-python ya está instalada."
    else
        echo "La biblioteca kafka-python no está instalada. Instalando..."
        pip install kafka-python
        sudo reboot
    fi
}

# Función para verificar/instalar la librería pykafka en el sistema
function install_pykafka() {
    python -c "import pykafka" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "La biblioteca pykafka ya está instalada."
    else
        echo "La biblioteca pykafka no está instalada. Instalando..."
        pip install pykafka
        sudo reboot
    fi
}


# Verifica la conexión a Internet
check_internet

# Verifica si la biblioteca paho-mqtt está instalada
install_paho

# Verifica si la biblioteca confluent-kafka está instalada
install_confluent_kafka
install_kafka_python
install_pykafka

# /usr/local/pyenv/shims/pip3 install confluent-kafka >> /data/openpilot/install_mix.txt 2> /data/openpilot/error_mix2.txt
