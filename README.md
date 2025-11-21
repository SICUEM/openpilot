Readme hecho por [Adrian Cañadas](https://github.com/Dragoadri) 

# ![Logo de la Universidad Europea](https://upload.wikimedia.org/wikipedia/commons/3/3a/UE_Madrid_Logo_Positive_RGB.png)
# SIC-Librerias - Sunnypilot
# Version Congelada que no funciona.

-----

**Rama de Desarrollo:** 'sic-pruebas'<br>
**Proyecto Basado en:** Sunnypilot (fork de OpenPilot por Comma.ai)<br>
**Grupo de Investigación:** SICUEM<br>


---

## ! ULTIMOS PUNTOS CLAVE

- En la clase LiveStreamVideoStreamTrack, los videos no se guardan en archivos, sino que se transmiten en vivo a través de un socket de mensajería de OpenPilot


---

## 🧪 Descripción del Proyecto

La rama `sic-pruebas` es una extensión de Sunnypilot desarrollada por el grupo de investigación **SICUEM**, centrada en la mejora de sistemas avanzados de asistencia a la conducción (ADAS). En este proyecto, hemos trabajado en dos áreas clave:

- **Telemetría Avanzada:** Implementación de un sistema de telemetría que permite el monitoreo en tiempo real del estado del vehículo, recopilación de datos críticos y análisis del rendimiento del sistema.

- **Detección de Maniobras Críticas:** Desarrollo de algoritmos que permiten identificar cuándo el vehículo se aproxima a maniobras complejas, anticipándose a situaciones de riesgo para mejorar la seguridad.

Además, se han realizado mejoras significativas en la **interfaz de usuario (front-end)**, optimizando la visualización de datos relevantes y mejorando la experiencia de usuario.

---

## 📚 Documentación Adicional

Para más detalles técnicos, consulta la documentación completa del proyecto:
👉 [Documentación del Proyecto](https://docs.google.com/document/d/1sxwJNi6hhJmm7Wsi8D8DlvUuuSTA4Juq6f6QMueI7lE/edit?usp=sharing)

---

## 👨‍💻 Integrantes del Proyecto

- **Adrián Cañadas**
- **Javier Fernández**
- **Nourdine Alaine**
- **Sergio Bemposta**

Grupo de Investigación **SICUEM** - Universidad Europea

---

## 🚀 Instalación y Configuración

### ⚙️ Requisitos Previos

- **Sistema Operativo:** Ubuntu 24.04 o superior
- **Dependencias:** Python 3.8+, C++, QT (para la interfaz gráfica)
- **Hardware:** Compatible con Comma Two o EON

> **Nota:** En sistemas Windows se recomienda utilizar WSL, y en macOS o distribuciones Linux no compatibles se recomienda el uso de dev containers.

---

### 📥 Clonación del Repositorio

```bash
# Clonación parcial para descarga rápida
git clone --filter=blob:none --recurse-submodules --also-filter-submodules https://github.com/commaai/openpilot.git

# O clonación completa
git clone --recurse-submodules https://github.com/commaai/openpilot.git
```
---
### ⚙️ Configuración del Entorno

```bash
# Acceder al directorio del proyecto
cd openpilot

# Ejecutar el script de configuración para Ubuntu
tools/ubuntu_setup.sh

# Sincronizar Git LFS
git lfs pull

# Activar el entorno virtual de Python
source .venv/bin/activate

# Compilar openpilot
scons -u -j$(nproc)
```
---

### 🏎️ openpilot in Simulator

```bash
# Run locally
./tools/sim/launch_openpilot.sh

```
### 🔗 Bridge Usage
```bash
$ ./run_bridge.py -h

usage: run_bridge.py [-h] [--joystick] [--high_quality] [--dual_camera]
                     [--simulator SIMULATOR] [--town TOWN]
                     [--spawn_point NUM_SELECTED_SPAWN_POINT]
                     [--host HOST] [--port PORT]

Bridge between the simulator and openpilot.

options:
  -h, --help            show this help message and exit
  --joystick
  --high_quality
  --dual_camera
  --simulator SIMULATOR
  --town TOWN
  --spawn_point NUM_SELECTED_SPAWN_POINT
  --host HOST
  --port PORT

```
