# Modelos del equipo en chestnut

Sirve para ejecutar en **chestnut**, la gráfica externa de comma conectada por USB al comma (kit
"ready to drive" con una XFX Radeon RX 9060 de 8 GB), los modelos de conducción que entrena el
equipo. El modelo se elige con una variable (`OrbitModeloDeseado`), y la app la escribirá
cuando exista ese botón.

```
compañero ──(carpeta del modelo)──▶ /data/orbit_models/<id>/
                                           │  coche APAGADO y chestnut conectado
                                           ▼
                         gestor orbit_modelos: ¿ya viene compilado y vale? ── sí ──▶ LISTO
                                           └─ no: compila sus ONNX ───────────────▶ LISTO
OrbitModeloDeseado = <id> (la app, cuando quiera)
                                           │  al ARRANCAR modeld, y en marcha con el coche
                                           │  PARADO y openpilot DESACOPLADO (sin reiniciar)
                                           ▼
modeld: ¿chestnut conectado y <id> LISTO para esta cámara? ── sí ──▶ modelo del equipo en chestnut
                                           └─ no ──▶ modelo de serie (grande en chestnut si está, si no, el pequeño en el comma)
                                                     y el motivo queda en OrbitModeloActivo
```

## Qué dispositivo es y qué se le aplica

`chestnut.perfil()` lo detecta (`HARDWARE.get_device_type()`), y a partir de ahí se decide
para qué cámara se compila, el destino de compilación y qué avisos se publican:

| Dispositivo | Cámara | Destino | Soporte de comma | Avisos que se publican |
|---|---|---|---|---|
| comma four (`mici`) | 1344x760 | `usbgpu` (la AMD de chestnut) | **oficial** | — |
| comma 3X (`tizi`) | 1928x1208 | `usbgpu` | no oficial, pero funciona: lo probó comma y lo usa la comunidad | el cable USB puede quitar el GPS (cable óptico o ferritas) |
| comma 3 (`tici`) | 1928x1208 | `usbgpu` | no, y sin pruebas conocidas | sin pruebas |
| PC | 1928x1208 (la del simulador) | `gpu_pc` (chestnut simulado con la NVIDIA) | — | — |

En los tres comma, la detección USB (`0xADD1:0x0001`) y los flags de tinygrad son los
mismos. Lo que cambia es la cámara, porque el `.pkl` lleva el warp de una sola resolución:
un modelo compilado en un comma four no vale para un 3X. En todos se avisa si el USB de
chestnut negocia menos de 5000 Mbps, el mismo umbral que usa comma.

La gráfica no guarda nada. Su memoria (VRAM) se borra al apagarse. El modelo vive en el disco
del comma, y modeld lo sube a la gráfica por USB cada vez que arranca.

## El contrato: qué tiene que cumplir un modelo

Se comprueba contra los ONNX de serie del repo (`selfdrive/modeld/models/driving_*.onnx`),
porque es lo único que el modeld de ORBIT sabe alimentar e interpretar.
Lo implementa `paquete.comparar_contrato`.

Un modelo son **dos redes**, igual que el de openpilot:

| Red | Entradas | Salidas |
|---|---|---|
| **vision** (`driving_vision.onnx`) | `img` y `big_img`, las dos de forma **(1, 12, 128, 256)**: las imágenes de la cámara normal y la gran angular que prepara modeld (2 fotogramas × 6 canales YUV, 128×256). | Un vector de salida con `output_slices` en sus metadatos. Tiene que incluir **al menos** las salidas con nombre del de serie: `meta`, `desire_pred`, `pose`, `wide_from_device_euler`, `road_transform`, `lane_lines`, `lane_lines_prob`, `road_edges`, `lead`, `lead_prob` y `hidden_state`. |
| **on_policy** (`driving_on_policy.onnx`) | `features_buffer` (1, 25, **N**), `desire_pulse` **(1, 25, 8)** y `traffic_convention` **(1, 2)**. Puede tener también `action_t` **(1, 2)**. | Al menos `plan` y `desire_state` en sus `output_slices`. |

Hay tres reglas:

1. **Lo que da modeld no se puede cambiar.** Las imágenes, `desire_pulse`, `traffic_convention`
   y `action_t` tienen que tener exactamente esas formas. Modeld las construye así y no sabe
   construirlas de otra manera.
2. **Las salidas con nombre tienen que estar todas.** Las leen `parse_model_outputs.py`, el
   planner y la UI. Puede haber salidas de más; `pad` no cuenta.
3. **El tamaño interno es libre, pero coherente.** Un modelo más potente puede tener un
   `hidden_state` de otro tamaño (el de serie es 512). La única condición es que el último
   número de `features_buffer` de su política sea ese mismo tamaño, porque modeld alimenta la
   política con el `hidden_state` de su visión. El validador lo muestra como aviso, no como
   error.

`output_slices` va en los metadatos del ONNX (`metadata_props`), igual que en los modelos de
comma. Es lo que lee `get_model_metadata.py`. El modelo grande de serie (`big_driving_*`,
unos 300 MB de ONNX) cumple este contrato y sirve como modelo de prueba.

## Cómo se entrega un modelo

Una carpeta por modelo. **El nombre de la carpeta es el id** que se escribe en
`OrbitModeloDeseado`: letras, números, `.`, `_` y `-`, con un máximo de 64 caracteres.

```
/data/orbit_models/<id>/
  driving_vision.onnx        ┐ fuente: se compila en el coche si hace falta
  driving_on_policy.onnx     ┘
  driving_tinygrad.pkl       ya compilado (opcional; puede venir troceado con .chunkmanifest)
  manifest.json              opcional: {"nombre": "...", "version": "...", "notas": "..."}
  compilado/                 lo escribe ORBIT: no tocar
```

- **Si trae `driving_tinygrad.pkl`**, se valida y, si vale, se usa sin compilar. Un `.pkl`
  vale si cumple el contrato, trae el warp de la cámara de ese coche y está compilado para la
  AMD. Las cámaras son 1928x1208 en el comma 3X y 1344x760 en el comma four. Además tiene que
  estar compilado con **el mismo tinygrad que el repo** y tener el warp en el dispositivo
  donde modeld le da los frames (`QCOM` en el comma; un `.pkl` hecho en un PC con
  `WARP_DEV=CPU` se rechaza). Lo del tinygrad solo se puede comprobar al ejecutarlo: si falla
  en el periodo de prueba, se veta (ver "Cuando un modelo falla").
- **Si no trae `.pkl`, o el que trae no vale**, se compilan los ONNX con
  `selfdrive/modeld/compile_modeld.py`, el mismo compilador y los mismos parámetros que usa el
  SConscript para chestnut (`helpers.usbgpu_tg_flags`). Compilar necesita chestnut conectado y
  el coche apagado.

Cómo llega la carpeta al comma (por SSH, descargada, etc.) queda fuera de esta parte.

## Antes de llevarlo al coche: el validador en el PC

```bash
source .venv/bin/activate
PYTHONPATH=.. python3 tools/orbit/validar_modelo.py <carpeta_del_modelo>
```

Revisa los ONNX o el `.pkl` contra el contrato y da dos veredictos: si vale para **chestnut
(el coche)** y si vale para el **simulador (PC)**. Sale con 0 si vale para chestnut.

- `--ejemplo-serie-grande <carpeta>` crea un paquete de prueba con el modelo grande de serie.
- `--compilar-local` compila los ONNX para la GPU o la CPU de este PC, con el backend del
  último `scons`. Sirve para conducir con el modelo en el simulador:

```bash
PYTHONPATH=.. python3 tools/orbit/validar_modelo.py ~/.comma/orbit_models/<id> --compilar-local
# Conducir con él en el sim (se aplica al arrancar, o en marcha con el coche parado y desacoplado):
python3 -c "from openpilot.common.params import Params; Params().put('OrbitModeloDeseado', '<id>')"
```

En el PC los modelos van en `~/.comma/orbit_models`, o en `$ORBIT_MODELS_DIR` si está definida.

## Qué espera de la app móvil

**La variable es el Param `OrbitModeloDeseado`.** Es lo único que la app tiene que acabar
escribiendo en el coche para cambiar de modelo.

| Valor | Qué significa |
|---|---|
| `m1`, `modelo_v3`, … | El id del modelo: el nombre de su carpeta en `/data/orbit_models/<id>/`. Letras, números, `.`, `_` y `-`, con un máximo de 64 caracteres. |
| vacío, `serie` o `stock` | El modelo de serie. |

Es persistente: la elección sobrevive a reinicios. Un id que no existe o que no está listo no
rompe nada: corre el de serie y el motivo queda en `OrbitModeloActivo` y `OrbitModeloErrores`.

**Dónde se recoge en el coche.** Lo lee modeld con `seleccion.leer_deseado()`:
- **al arrancar**, para elegir qué modelo carga;
- **una vez por segundo en marcha**, mediante el Vigilante de `cambio.py`. Si cambia, el
  modelo queda pendiente y se aplica con el coche parado y openpilot desacoplado.

**Qué se devuelve a la app:**

| Param | Qué dice |
|---|---|
| `OrbitModeloActivo` | Qué modelo corre, dónde, el pendiente y por qué no es el pedido. |
| `OrbitModelos` | El estado de cada modelo en el coche (listo, compilando, error...). |
| `OrbitModeloErrores` | Los últimos fallos, con su fase y su motivo. |

**Estado actual: la app todavía no lo escribe.** No hay nada que traiga esta variable desde
el móvil. Hoy se pone a mano (`Params().put('OrbitModeloDeseado', '<id>')`) o con
`chestnut_sim.py elegir <id>` en el PC. Los tres Params de respuesta tampoco llegan aún a la
app.

**Por dónde debería llegar (propuesta, falta implementarla).** ORBIT ya tiene dos vías de
entrada desde la app:

| Vía | Qué es | ¿Encaja? |
|---|---|---|
| **`cfg/desired`** (`orbit/config_v2.py`) | Configuración de estado. Es un mensaje retenido en `orbit/v2/cfg/desired/<dongle>`, con una lista cerrada de claves, tipos y una versión que no retrocede. Así llega ya `telemetry_profile` al Param `OrbitTelemetryProfile`. | **Sí (recomendada).** La elección de modelo es un estado que se mantiene, se puede cambiar en cualquier momento y se aplica cuando el coche está parado. Al ser retenido, si el comma estaba desconectado recibe la última elección al conectarse. |
| Verbo del mando v2 (`orbit/command_spec.py` → router) | Órdenes puntuales con gate y ACK (`set_mode`, `cruise_delta`...). | Peor: un verbo es "hazlo ya", y el cambio de modelo no se puede aplicar en cualquier momento. |

Lo previsto:
- añadir en `config_v2.py` una clave, por ejemplo `driving_model`, de tipo id validado (el
  mismo patrón que `paquete.ID_VALIDO`) y con destino el Param `OrbitModeloDeseado`;
- responder por `cfg/reported`;
- enviar `OrbitModeloActivo`, `OrbitModelos` y `OrbitModeloErrores` en un grupo de
  telemetría "Modelo" (`telemetria_grupos.py`).

**El nombre de la clave (`driving_model` u otro) hay que acordarlo con quien hace la app**,
porque es lo que van a enviar.

## En el coche

**Elegir modelo.** Se escribe el id en `OrbitModeloDeseado` (ver "Qué espera de la app
móvil"). Vacío, `serie` o `stock` significan el modelo de serie. El valor es persistente y se
puede cambiar en cualquier momento.

**Ojo con el selector de modelos de sunnypilot.** orbitpilot está construido sobre
sunnypilot, y su menú Ajustes → Models sigue en la interfaz. Si alguien elige ahí un modelo
de la comunidad, el manager arranca `modeld_tinygrad` (`sunnypilot/modeld_v2`) en vez del
modeld de serie (`process_config.py`, condición `is_stock_model`). Todo lo de ORBIT vive en
el modeld de serie, así que en ese caso se ignora `OrbitModeloDeseado` y no queda ningún
aviso. Con ese menú sin tocar, que es lo normal, no afecta. Ver "Pendiente".

**Cambio en marcha, sin reiniciar** (`cambio.py`). modeld mira una vez por segundo
`OrbitModeloDeseado` y si chestnut está conectado:

| Qué pasa | Cuándo se aplica |
|---|---|
| La app pide otro modelo, o chestnut aparece | Con el coche **parado** y openpilot **desacoplado**. Mientras tanto, `OrbitModeloActivo.pendiente` dice cuál espera. |
| Chestnut desaparece con el modelo corriendo en él | **Al momento**, aunque el coche se mueva: ese modelo ya no tiene dónde ejecutarse, y el de serie del comma carga en menos de un segundo. |
| Se vuelve a pedir el modelo que ya corre | Se quita el pendiente. |

Recargar deja entre 0,2 y 1 s sin `modelV2` en la GPU del PC; en chestnut hay que medirlo,
porque los pesos viajan por USB. Si el modelo pedido no carga, se carga lo que daría el
arranque (el siguiente candidato). Si el fallo fue **al cargar** (por ejemplo, la gráfica aún
ocupada por el compilador del gestor justo al arrancar el coche), se reintenta a los 10 s,
como mucho 2 veces, también con el coche parado y desacoplado. Después no se reintenta hasta
que algo cambie: un modelo roto no se recarga en cada parada.

**Tiempo real.** Con el modelo en el comma, modeld corre en tiempo real (SCHED_FIFO en el
núcleo 7), como el de serie. Con el modelo en chestnut no, porque el USB satura un núcleo.
`cambio.tiempo_real()` lo pone o lo quita en cada carga, también en los cambios en marcha.

**Qué carga modeld** (`seleccion.candidatos`). Prueba en este orden y se queda con el primero
que carga:
1. El modelo pedido, si chestnut está conectado y el modelo está LISTO para su cámara.
2. El modelo grande de serie en chestnut, si está compilado. Es lo que ya hacía openpilot con
   una gráfica conectada.
3. El modelo pequeño de serie en el comma. Siempre funciona.

Si un candidato falla al cargar, se registra y se prueba el siguiente.

**`OrbitModeloActivo`** (JSON, lo escribe modeld al cargar):

```json
{"origen": "equipo|serie_grande|serie", "modelo_id": "m1", "deseado": "m1",
 "chestnut": true, "destino": "usbgpu", "en_chestnut": true, "usbgpu": true,
 "motivo": "", "pendiente": "", "ts_ms": 1761990000000}
```

Si `motivo` está vacío, se cargó justo lo que se pidió. Si no, explica por qué no. Por
ejemplo: `chestnut no esta conectado`, `el modelo m1 no esta listo para usbgpu 1344x760` o
`equipo m1 no carga: ...`.

`pendiente` (por ejemplo, `equipo m2`) es el modelo que se cargará en cuanto el coche esté
parado y desacoplado.

**`OrbitModelos`** (JSON, lo revisa el gestor `orbit_modelos` cada 5 s con el coche
apagado y lo escribe solo si algo cambia): el dispositivo (`dispositivo`, `nombre_dispositivo`, `oficial`), si chestnut está
conectado y a qué velocidad (`usb_mbps`), los `avisos`, y el estado de cada carpeta para el
destino y la cámara de ese dispositivo.

| estado | qué significa |
|---|---|
| `listo` | Se puede cargar. `origen`: `entregado` (venía compilado) o `compilado` (lo compiló ORBIT). |
| `compilando` | Compilando ahora. Tarda minutos y ocupa la gráfica. |
| `pendiente_chestnut` | Hay que compilarlo y chestnut no está conectado. |
| `error` | No vale (el motivo está en `detalle`). **No se reintenta** hasta que cambien sus ficheros o el tinygrad del repo. |
| `sin_modelo` | La carpeta no trae ni `.pkl` ni los dos ONNX. |

El gestor solo corre **con el coche apagado** (`only_offroad`), porque compilar ocupa la
gráfica en exclusiva y modeld la necesita en marcha. Si el coche arranca a mitad de una
compilación, el gestor se detiene. El `.tmp` a medio hacer no se da por bueno, y se vuelve a
compilar en el siguiente apagado. El registro de cada compilación queda en
`compilado/<destino>_<cámara>.log`.

**Si chestnut se desconecta en marcha**, modeld lo ve en menos de un segundo y carga el de
serie. Si la ejecución en la gráfica falla antes, modeld captura el error y, si chestnut ya
no está, carga el de serie en ese mismo momento, sin caerse. Lo que no se puede capturar es
un cuelgue dentro del driver: eso hay que verlo en las pruebas reales.

## Cuando un modelo falla

**Periodo de prueba y vetos** (`prueba.py`). Que un `.pkl` cargue no garantiza que funcione:
un tinygrad distinto o un warp de otro dispositivo revientan en la primera ejecución. Sin
esto, modeld se caería, el manager lo reiniciaría con el mismo modelo, y así todo el viaje.

| Qué pasa | Qué se hace |
|---|---|
| Falla (excepción o salidas NaN/inf) en sus primeros 40 frames | Se **veta** y modeld carga el siguiente candidato al momento |
| Falla después | Se descarta hasta que reinicie modeld, sin veto |
| modeld muere con el modelo en prueba (segfault, etc.) | Al arrancar cuenta una caída; a la segunda, se **veta** |
| Va más lento que 50 ms por frame | Aviso de `rendimiento` (se sigue usando) |
| Chestnut desconectado | Nunca veta: el modelo no tiene la culpa |

Un veto (`OrbitModeloVetos`) dura hasta que cambie el `.pkl` (entregarlo o compilarlo de
nuevo) o el tinygrad del repo. El pequeño de serie no entra en prueba, porque es la red final.

**Por qué falló: `OrbitModeloErrores`** (`errores.py`). Cada fallo queda con su fase, el
modelo y el motivo, con fichero y línea si es una excepción. Se guardan los 30 últimos, sobreviven a
reinicios y también van a cloudlog como evento `orbit_modelo_error`. El mismo fallo seguido
se cuenta en `veces` en vez de repetirse.

| fase | cuándo |
|---|---|
| `validar` | el gestor rechaza el `.pkl` entregado o los ONNX (contrato, cámara, warp...) |
| `compilar` | `compile_modeld` falla; el motivo lleva las últimas líneas de su log |
| `eleccion` | se pidió un modelo y corre otro (aviso con los motivos) |
| `cargar` | el `.pkl` no carga (pickle, gráfica ocupada...) |
| `ejecutar` / `salidas` | carga pero falla al ejecutarse, o da NaN/inf |
| `arranque` | modeld murió con el modelo en prueba |
| `chestnut` | chestnut se desconectó con el modelo corriendo |
| `rendimiento` | más lento que el ritmo de modeld (aviso) |

### Cómo ver los errores

**En el comma** (por SSH, con el coche encendido o apagado):

```bash
ssh comma@<ip-del-comma>
cd /data/openpilot
PYTHONPATH=/data/pythonpath python3 -m openpilot.orbit.modelos.errores
```

**En el PC** (simulador o chestnut simulado):

```bash
cd ~/Investigacion/orbitpilot
source .venv/bin/activate
python3 -m openpilot.orbit.modelos.errores
```

Sale una entrada por fallo, de la más antigua a la más reciente:

```
[2026-11-02 16:28:39] ERROR cargar m1 origen=equipo destino=usbgpu
    RuntimeError: device busy (en ops_amd.py:120 _open)
```

Cómo leerla: la hora, `ERROR` o `AVISO`, la fase (ver la tabla de arriba), el modelo, dónde
corría y, debajo, el motivo. `veces=N` indica que el mismo fallo se repitió seguido N veces.
Si no hay nada, dice `sin errores registrados`.

**En vivo, en el PC:** `chestnut_sim.py ver` (ver "Probar en el PC") muestra cada segundo el
último fallo junto al modelo que corre, el pedido y el pendiente.

**Otros sitios donde mirar:**
- El JSON crudo está en el Param `OrbitModeloErrores` (`cat /data/params/d/OrbitModeloErrores`
  en el comma). Los modelos vetados están en `OrbitModeloVetos`.
- Cada fallo también va a cloudlog como evento `orbit_modelo_error`, así que queda en los
  logs de la ruta.
- Si el fallo es de compilación, el log completo está en
  `/data/orbit_models/<id>/compilado/<destino>_<cámara>.log`.

**Levantar un veto a mano**, por ejemplo tras arreglar el driver sin cambiar el `.pkl`:
borrar el Param `OrbitModeloVetos` (`rm /data/params/d/OrbitModeloVetos` en el comma, con el
coche apagado).

## Probar en el PC: chestnut simulado

La GTX/RTX del PC hace de chestnut (CUDA) y la CPU hace de comma, así que se ve el camino
entero: compilar, elegir, cambiar en marcha y desenchufar.

Hace falta, una sola vez:

```bash
source .venv/bin/activate
# nvrtc y las cabeceras de CUDA. Sin ellos, tinygrad usa en silencio su generador PTX, que una
# GTX 10xx rechaza (CUDA_ERROR_INVALID_PTX). No están en pyproject: un `uv sync` los quita.
uv pip install nvidia-cuda-nvrtc-cu12==12.9.86 nvidia-cuda-runtime-cu12==12.9.79
scons -u -j$(nproc)     # SIN TG_BACKEND: el modelo de serie, en la CPU (el "comma")
```

Para los modelos de `gpu_pc`, los pesos fp16 se suben a fp32 (`compilar_fp32.py`), porque las
Pascal van muy lentas en fp16. En una GTX 1050, el pequeño de serie tarda 19 ms en la GPU
frente a 200 ms en la CPU, y el grande 85 ms.

```bash
PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py conectar
PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py preparar serie-peq   # o esperar al gestor (offroad)
PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py elegir serie-peq
PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py ver                  # en otra terminal, en vivo
# arrancar openpilot y el bridge del simulador, conducir, parar, y probar:
PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py elegir serie-grande  # se aplica al parar y desacoplar
PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py desconectar          # pasa al de serie al momento
```

`ver` muestra cada segundo:
- si chestnut está conectado;
- qué se pidió y qué corre, y dónde;
- el tiempo del modelo y los `modelV2` por segundo;
- la velocidad del coche y si está acoplado;
- el pendiente, el motivo y el estado de cada modelo.

## Ficheros

| Fichero | Qué hace |
|---|---|
| `paquete.py` | Estructura de la carpeta, contrato, lectura de un `.pkl` sin ejecutarlo y marcador LISTO. |
| `compilar.py` | Acepta un `.pkl` entregado o compila los ONNX. También se puede usar a mano. |
| `chestnut.py` | Qué dispositivo es (comma four, 3X, PC), si chestnut está conectado y su velocidad USB. |
| `seleccion.py` | Qué candidatos prueba modeld y qué publica en `OrbitModeloActivo`. |
| `cambio.py` | Cambio de modelo en marcha: cuándo recarga modeld, reintento tras fallo de carga y tiempo real. |
| `prueba.py` | Periodo de prueba de cada modelo recién cargado y vetos. |
| `errores.py` | Registro de fallos con su motivo (`OrbitModeloErrores`). |
| `compilar_fp32.py` | `compile_modeld.py` con pesos fp32, para el chestnut simulado del PC. |
| `gestor.py` | Proceso `orbit_modelos` (offroad): prepara los modelos y publica `OrbitModelos`. |
| `selfdrive/modeld/modeld.py` | `load_model`: carga el candidato y, si falla, pasa al siguiente. |
| `tools/orbit/validar_modelo.py` | Validador para el PC. |
| `tools/orbit/chestnut_sim.py` | Chestnut simulado: conectar, desconectar, preparar, elegir y ver. |
| `orbit/test/test_modelos_chestnut.py` | Tests (`pytest orbit/test/test_modelos_chestnut.py`). |

Hay que recompilar `common` con scons después de añadir los Params a `common/params_keys.h`.

## Pendiente

- **Espacio en disco: sin gestionar.** No se sabe cuántos modelos habrá. Cada uno ocupa sus
  ONNX más un `.pkl` compilado (el modelo grande, unos 300 MB más 300 MB), y nada borra
  modelos antiguos. Hay que decidir una política: cuota, borrar los no usados, etc.
- **Orden de la app.** Hoy el modelo se elige escribiendo `OrbitModeloDeseado` a mano. Falta
  la clave de `cfg/desired` que lo escriba desde la app (ver "Qué espera de la app móvil"), y
  acordar su nombre con quien hace la app.
- **Telemetría y pantalla.** Falta enviar `OrbitModeloActivo`, `OrbitModelos` y
  `OrbitModeloErrores` a la app (un grupo "Modelo" en `telemetria_grupos.py`) y mostrar un
  aviso en el comma cuando se vuelve al de serie.
- **Selector de modelos de sunnypilot.** Si se elige un modelo en Ajustes → Models, ORBIT se
  ignora sin avisar. Opciones: (1) que el modeld de ORBIT arranque siempre que haya un modelo
  del equipo pedido, (2) registrar al menos el aviso en `OrbitModeloErrores` y
  `OrbitModeloActivo`, (3) quitar ese menú si los modelos de la comunidad no interesan. La
  recomendada es 1 + 2. Falta decidir si los modelos de sunnypilot interesan al proyecto.
- **Seguridad de la entrega.** modeld hace `pickle.loads` del `.pkl`, y eso ejecuta código: un
  `.pkl` manipulado ejecutaría lo que quisiera dentro de modeld. Mientras la carpeta se copie a
  mano en el comma no hay riesgo nuevo. **Se aborda cuando la app (o un servidor) envíe los
  modelos al coche:** el canal tiene que ser de confianza, y el comma tiene que comprobar una
  firma o un hash publicado por el equipo antes de dar el modelo por bueno. Lo lógico es que
  lo haga el gestor, antes de marcarlo LISTO.
- **Memoria de la gráfica al cambiar.** Falta comprobar en la RX 9060 de 8 GB que cambiar
  entre dos modelos grandes no se queda sin memoria (el allocator de tinygrad puede
  retenerla). Si pasa, quedará como fallo de `cargar` en `OrbitModeloErrores`.
- **Probar con el hardware.** Hay que ver que chestnut se detecta (USB `0xADD1:0x0001`) y si
  hace falta flashearle firmware. También hay que medir cuánto tarda compilar en el comma y
  cuánto tarda el cambio en marcha, porque los pesos viajan por USB.
- **comma 3X.** En el código se trata igual que el comma four, salvo la cámara y los avisos.
  Falta probarlo en el coche: el GPS con el cable puesto y la velocidad del USB.
- **Cómo llega la carpeta del modelo al comma.** Hoy se copia a mano a
  `/data/orbit_models/<id>/` (por SSH, por ejemplo). No hay un mecanismo para que el compañero
  suba los modelos ni para que la app los descargue.
- **Firmware de chestnut.** El flasheador (`system/hardware/chestnut/flash.py`) está en la rama
  `dev-chestnut` y llegará a master cuando esa rama se mergee. No lo traemos aquí.
- **Monitorización de chestnut** (temperatura y alimentación). La hace `ChestnutState` en
  `dev-chestnut` y convivirá con lo nuestro cuando se mergee. Entonces habrá que revisar que
  el aviso de USB lento no salga dos veces (el nuestro, en `chestnut.avisos`, y el suyo).
- **Fallo de copia disco→USB de tinygrad (commaai/openpilot#39175).** Nuestro tinygrad
  (submódulo `sunnypilot/tinygrad`, `ac1632ab`) **no trae** la protección que lo arregla en
  upstream (tinygrad PR #18824). La AMD por USB tiene cola SDMA, así que
  `supports_copy_from_disk` vale True (`tinygrad/runtime/ops_amd.py:646`) y las copias
  DISK→AMD van por la copia directa (`tinygrad/engine/realize.py:165`), que es la que falla.
  - **Afecta** a compilar los ONNX en el coche: el gestor y `compile_modeld` cargan los pesos
    del ONNX desde disco. Saldría como fallo de `compilar` en `OrbitModeloErrores`, con
    `Device hang detected` o fallos de la GPU.
  - En principio **no afecta** a cargar un `.pkl` en modeld: los pesos van dentro del pickle y
    se copian desde memoria. Un `.pkl` entregado ya compilado lo evita.
  - **Arreglo propuesto, sin tocar el submódulo:** un envoltorio como `compilar_fp32.py` que
    ponga `supports_copy_from_disk = False` en el allocator AMD cuando `dev.is_usb()` antes de
    lanzar `compile_modeld`. Es lo mismo que hace upstream, y la copia cae al camino normal de
    subida por USB (`copyin`).
  - Hay que confirmarlo en el coche con el reproductor del issue. Sin hardware no se puede.
- **Validación del warp del `.pkl` entregado.** Todos los `.pkl` de `compile_modeld` traen el
  warp de cada cámara (`compile_modeld.py:294`), y modeld no funciona sin él
  (`jits[(cam_w, cam_h)]`). El warp se ejecuta en `WARP_DEV`, que en el comma es `QCOM`, con
  y sin chestnut (`SConscript`). En el PC se comprobó que el dispositivo del warp aparece en el
  `.pkl` (`CPU` en los de `gpu_pc`). Falta verlo con un `.pkl` compilado en el comma (`QCOM`).
  Si se rechaza un `.pkl` y hay ONNX, se compilan los ONNX, así que no bloquea.
- **Ajustar los umbrales del periodo de prueba** con datos reales: 40 frames, 50 ms por frame
  y 2 caídas para vetar.
- **Cuelgues dentro del driver de la eGPU.** No se pueden capturar. Si modeld se queda
  colgado, el manager no lo reinicia. Hay que verlo en las pruebas reales.
