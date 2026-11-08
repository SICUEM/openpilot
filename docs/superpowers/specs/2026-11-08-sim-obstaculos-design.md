# Obstáculos configurables en la simulación MetaDrive — Diseño

Fecha: 2026-11-08
Rama: miguelmarchal-obstaculos
Estado: borrador para revisar

## 1. Objetivo

Meter obstáculos **estáticos** en la simulación MetaDrive del PC para que los modelos que se están entrenando aprendan a esquivarlos. Los obstáculos se configuran desde la pantalla de openpilot, en una sección nueva "Simulación" del panel ORBIT que siempre está visible, sin activar nada:

- activar o desactivar obstáculos al cargar el mapa;
- elegir el tipo (cono, barrera, triángulo o un coche parado);
- elegir dónde va cada uno: metros a lo largo de la ruta + carril + desplazamiento lateral.

No es un trabajo de rotondas: no hay NPC circulando, basta con poder poner coches parados.

En CARRO ya se hizo algo parecido con coches. Aquí se generaliza a varios tipos y se hace configurable sin tocar código.

## 2. Estado actual (leído en el código)

- La sim tiene un mod-menu por teclado (`tools/sim/bridge/metadrive/metadrive_modmenu.py`, diseño en `2026-07-08-metadrive-sim-modmenu-design.md`). Pone un coche parado, un coche que se cruza o un triángulo de aviso a una distancia fija delante del ego. No hay escenarios ni configuración.
- En la sim del PC arrancan también la pantalla de openpilot (`launch_openpilot.sh`, `BIG=1`) y los hilos ORBIT del manager. El bridge y openpilot corren en la misma máquina y **comparten los Params**.
- Los obstáculos se crean en el proceso `metadrive_process` con `env.engine.spawn_object(...)`. Hay que borrarlos **antes** de `env.reset()`, porque si quedan objetos sueltos el engine falla en un assert (lo explica `ModMenu.clear`).

### 2.1 El problema: los obstáculos no se ven en la cámara

orbitpilot usa `commaai/metadrive@minimal`, cuyos assets solo traen `warning/warning.gltf` (además de `box.bam`, skybox y similares):

| Objeto | Clase MetaDrive | ¿Funciona hoy? |
|---|---|---|
| Triángulo de aviso | `TrafficWarning` | Sí, y se ve |
| Cono | `TrafficCone` | **No**: falla al cargar `traffic_cone/scene.gltf` |
| Barrera | `TrafficBarrier` | **No**: falta `barrier/scene.gltf` |
| Coches | `DefaultVehicle`, `S/M/L/XLVehicle` | Tienen física pero **son invisibles** (`render_vehicle=False`) |
| Peatón / ciclista | `Pedestrian`, `Cyclist` | **No**: faltan sus modelos |

El "coche parado" del mod-menu actual es invisible para la cámara, así que ningún modelo que mire la imagen puede esquivarlo. **Lo primero es tener los assets completos.**

Los modelos que hacen falta salen de los assets completos de MetaDrive 0.4.2.3 (la misma versión que marca el `version.txt` del venv). Ya están en el repo, en `tools/sim/assets/metadrive/models/` (ver §3.5).

## 3. Diseño

### 3.1 Idea central

```
 pantalla openpilot (PC)           Params                     proceso metadrive
 panel ORBIT > Simulación  ──▶  OrbitSimObstaculos  ──▶  GestorObstaculos (lee cada ~1 s)
                           ◀──  OrbitSimEstado      ◀──  (mapa, ruta, colocados, errores)
```

- **Un solo Param con el escenario** (`OrbitSimObstaculos`, JSON). Es la única fuente de verdad. Lo escribe la UI y lo lee la sim, sin abrir canales nuevos. Más adelante, la app (por MQTT) o un script de entrenamiento pueden escribir el mismo Param sin tocar la sim.
- **Un Param de vuelta** (`OrbitSimEstado`, JSON) que escribe la sim. Lleva el mapa cargado, la longitud de la ruta, el número de carriles, los obstáculos colocados y omitidos con su motivo, y si los assets están bien. La UI lo muestra para que se sepa siempre por qué no aparece un obstáculo, igual que se hizo con `OrbitModeloErrores` en chestnut.
- **Un módulo puro compartido** (`orbit/sim_obstaculos.py`) con el esquema, la validación, el catálogo de tipos y los presets. No importa ni MetaDrive ni pyray. Lo usan la UI y la sim y se prueba con tests sin levantar nada.

### 3.2 Formato del escenario

```json
{
  "v": 1,
  "rev": 7,
  "activo": true,
  "obstaculos": [
    {"tipo": "cono",  "s": 80.0,  "carril": 1, "lateral": 0.0},
    {"tipo": "coche", "s": 150.0, "carril": 2, "lateral": -0.5, "giro": 0}
  ]
}
```

- `rev`: la UI lo incrementa en cada cambio. La sim solo recoloca cuando cambia.
- `s`: metros a lo largo de la ruta del ego, contados desde el punto de salida.
- `carril`: 1 es el carril derecho, que es lo natural para quien lo configura. MetaDrive numera al revés (el índice 0 está junto a la línea central); la conversión se hace en la sim y se fija con un test.
- `lateral`: metros respecto al centro del carril, positivo hacia la izquierda. Se limita a ±(ancho del carril) para no sacarlo de la calzada.
- `giro`: grados sobre el rumbo del carril (opcional, 0 por defecto). Sirve para un coche cruzado o una barrera atravesada.
- Límite de 30 obstáculos, para no hundir la física ni el tamaño del Param.

### 3.3 Catálogo de tipos

| `tipo` | Clase | Notas |
|---|---|---|
| `cono` | `TrafficCone` (static) | |
| `barrera` | `TrafficBarrier` (static) | 2 m de ancho; con `giro=90` corta el carril |
| `triangulo` | `TrafficWarning` (static) | El único que funciona sin los assets completos |
| `coche` | `DefaultVehicle` | Sin policy, así que se queda parado; `render_vehicle=True` |
| `compacto` / `suv` / `furgoneta` / `camion` | `SVehicle` / `MVehicle` / `LVehicle` / `XLVehicle` | Igual que `coche` |

Todos los obstáculos son estáticos: ninguno lleva policy ni se mueve. Solo los obstáculos llevan `render_vehicle=True`. El ego sigue con `False`, porque la cámara va dentro y lo taparía.

### 3.4 Colocación (proceso metadrive)

Nuevo `tools/sim/bridge/metadrive/metadrive_obstaculos.py` con la clase `GestorObstaculos`:

1. **Cálculo de la ruta** tras cada `reset()`. Se recorren `ego.navigation.checkpoints` por parejas, se toman los carriles de `road_network.graph[a][b]` y se van sumando las longitudes. El punto de partida es la longitud del ego en su primer carril, así que `s = 0` cae en la salida.
2. **Colocación de cada obstáculo**: se busca el tramo que contiene `s` y se obtiene `pos = lane.position(s_local, lateral)` y `heading = lane.heading_theta_at(s_local) + giro`. Con eso se llama a `spawn_object`, como en el mod-menu.
3. **Omisión con motivo**, que se apunta en `OrbitSimEstado`, en estos casos:
   - `s` cae más allá del final de la ruta;
   - el carril no existe en ese tramo;
   - faltan los assets de ese tipo;
   - el obstáculo cae a menos de 8 m del ego, para no crearlo encima del coche.
4. **Ciclo de vida**: el gestor guarda los ids que crea.
   - Antes de cada `reset()` (sea del teclado, del mod-menu o un cambio de mapa) se llama a `gestor.clear()`. Después del reset se recoloca todo.
   - Cada ~1 s se lee el Param. Si cambia `rev`, se borra y se recoloca. Si `activo=false`, se borra todo.
5. **Convivencia con el mod-menu**: cada uno borra solo lo suyo. El HUD del mod-menu enseña además cuántos obstáculos del escenario hay puestos.

### 3.5 Assets

- **Los modelos van en el repo**, en `tools/sim/assets/metadrive/models/` (unos 49 MB). Solo se guardan las carpetas que usan los obstáculos: `traffic_cone`, `barrier`, `ferra`, `beetle`, `130`, `lada` y `truck`. El `README.md` de esa carpeta recoge la URL, el sha256 del zip y la orden para regenerarla. Así la rama es reproducible sin descargar nada y sin tocar el venv.
- **Fuera de LFS**: el LFS del repo apunta al GitLab de sunnypilot, donde no se puede subir. Por eso una regla en `.gitattributes` guarda esa carpeta como blobs normales, igual que los logos ORBIT. Ningún fichero pasa de 10 MB.
- **No se copian las texturas de carretera** del paquete completo: cambiarían el aspecto de la vía que ven hoy openpilot y los modelos.
- **Cómo los encuentra MetaDrive**: en `apply_metadrive_patches` se envuelve `AssetLoader.file_path`. Para `("models", <carpeta>, ...)`, si la carpeta existe en `tools/sim/assets/metadrive/models/` devuelve esa ruta; si no, la del paquete. El resto de assets (texturas, shaders, triángulo) sigue saliendo del paquete minimal.
- Al arrancar, la sim comprueba que están los modelos. Si falta alguno, no se cae: omite ese tipo y lo apunta en `OrbitSimEstado`.

### 3.6 Interfaz (pantalla openpilot)

Nuevo subpanel "Simulación" en `OrbitLayout` (`selfdrive/ui/sunnypilot/layouts/settings/orbit_panel.py`). **Siempre está visible**, sin variables de entorno ni interruptores. En un comma real no hace nada: solo escribe un Param que nadie lee. Si `OrbitSimEstado` está vacío, la sección lo indica con "Simulación no conectada", para que no parezca que algo falla.

- Interruptor **"Obstáculos al cargar el mapa"** (`activo`).
- **Estado** (de `OrbitSimEstado`): mapa, longitud de ruta, carriles, "5 colocados · 1 omitido (s=900 m fuera de ruta)" y un aviso si faltan assets.
- **Lista de obstáculos**, una fila por cada uno ("Cono · 80 m · carril 1 · +0,0 m") con editar y borrar.
- **Añadir / editar**, un diálogo con:
  - tipo (selector);
  - distancia (botones ±10 / ±1 m);
  - carril (1…N según el estado);
  - lateral (±0,25 m);
  - giro (0 / 45 / 90).
- **Presets**: "Coche parado en mi carril", "Slalom de conos", "Obra (barrera + conos)" y "Borrar todo".
- Cada cambio escribe el Param con `rev+1` y la sim lo recoloca en ~1 s.

Siguiendo el patrón de `orbit_ajustes.py`, la lógica (textos, validación, lectura y escritura del Param) va en un módulo sin pyray y se prueba con un Params falso. La parte que pinta queda fina.

### 3.7 Params nuevos

En `common/params_keys.h`:
- `OrbitSimObstaculos` (string, PERSISTENT): el escenario sobrevive a reinicios de la sim.
- `OrbitSimEstado` (string, CLEAR_ON_MANAGER_START).

## 4. Fases

1. **Spike de assets** (lo único con incógnita real). Con el parche de `AssetLoader`, crear un cono y un coche delante del ego y guardar un frame de `rgb_road` para comprobar que **se ven en la cámara**. Medir además el impacto en FPS con la GTX 1050.
2. **Núcleo de la sim**: módulo puro con su esquema y tests, `GestorObstaculos`, lectura del Param y `OrbitSimEstado`. Se puede probar escribiendo el Param a mano.
3. **UI**: subpanel Simulación con su lista, diálogo y presets.
4. **Extras**, según se necesiten: registro de choques por obstáculo (útil para evaluar el entrenamiento) y verbo MQTT para la app.

## 5. Preguntas abiertas

- **¿Escenario único o uno por mapa?** El mapa se elige al lanzar (`--map`) y las rutas miden distinto. Propuesta: un escenario único; lo que caiga fuera de la ruta se omite y se avisa. Si se usan varios mapas a menudo, se cambia a `{"mapas": {"loop": [...], "roundabout": [...]}}`.
- **¿Qué ve el modelo?** Este diseño solo pone los obstáculos en el mundo (cámara y física). El esquive lo hace el modelo entrenado o la Jetson (`orbit_obstacle_pulse`); openpilot de serie no esquiva. Si en la sim hiciera falta un "radar" falso como el de CARRO, sería una pieza aparte.

## 6. Fuera de alcance

- Configuración desde la app móvil (de momento solo la pantalla).
- Colocar obstáculos tocando un minimapa.
- Obstáculos en movimiento y NPC circulando (por ejemplo, dando vueltas en la rotonda), peatones y ciclistas.
- Cambios de comportamiento en el comma real: la sección de la UI se ve, pero solo escribe un Param que únicamente lee `tools/sim`.
