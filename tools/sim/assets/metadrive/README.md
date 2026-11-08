# Modelos 3D de MetaDrive para los obstáculos de la sim

El MetaDrive que instala orbitpilot (`commaai/metadrive@minimal`) solo trae el modelo del triángulo de aviso. Sin estos modelos no se pueden crear conos ni barreras, y los coches no salen en la cámara. Aquí se guarda el subconjunto que usan los obstáculos, para que la rama sea reproducible sin descargar nada.

Procedencia: assets completos de MetaDrive 0.4.2.3, la misma versión que marca el `version.txt` del paquete instalado.

- URL: https://github.com/metadriverse/metadrive/releases/download/MetaDrive-0.4.2.3/assets.zip
- sha256 del zip: `3a298c9b3f46467d572a8c49c5866f742951b9e2847cc958d098a5652f7f1591`
- Se copia solo `assets/models/<carpeta>` de la tabla, sin modificar.

| Carpeta | Clase de MetaDrive | Tipo de obstáculo |
|---|---|---|
| `traffic_cone` | `TrafficCone` | cono |
| `barrier` | `TrafficBarrier` | barrera |
| `ferra` | `DefaultVehicle` | coche |
| `beetle` | `SVehicle` | compacto |
| `130` | `MVehicle` | suv |
| `lada` | `LVehicle` | furgoneta |
| `truck` | `XLVehicle` | camión |

Las texturas de carretera del paquete completo no se copian a propósito: cambiarían el aspecto de la vía respecto a lo que ven hoy openpilot y los modelos.

Los ficheros `license.txt` de cada carpeta son las licencias originales de cada modelo.

Para regenerar la carpeta:

```bash
curl -L -o /tmp/assets.zip https://github.com/metadriverse/metadrive/releases/download/MetaDrive-0.4.2.3/assets.zip
echo "3a298c9b3f46467d572a8c49c5866f742951b9e2847cc958d098a5652f7f1591  /tmp/assets.zip" | sha256sum -c
unzip -q /tmp/assets.zip -d /tmp/md_assets
for d in traffic_cone barrier ferra beetle 130 lada truck; do cp -r /tmp/md_assets/assets/models/$d tools/sim/assets/metadrive/models/; done
```
