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
  estar compilado con **el mismo tinygrad que el repo**. Esto último solo se puede comprobar
  al cargarlo: si no carga, modeld vuelve al de serie y lo dice en `OrbitModeloActivo`.
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

## En el coche

**Elegir modelo.** Se escribe el id en `OrbitModeloDeseado`. Vacío, `serie` o `stock`
significan el modelo de serie. El valor es persistente y se puede cambiar en cualquier
momento.

**Cambio en marcha, sin reiniciar** (`cambio.py`). modeld mira una vez por segundo
`OrbitModeloDeseado` y si chestnut está conectado:

| Qué pasa | Cuándo se aplica |
|---|---|
| La app pide otro modelo, o chestnut aparece | Con el coche **parado** y openpilot **desacoplado**. Mientras tanto, `OrbitModeloActivo.pendiente` dice cuál espera. |
| Chestnut desaparece con el modelo corriendo en él | **Al momento**, aunque el coche se mueva: ese modelo ya no tiene dónde ejecutarse, y el de serie del comma carga en menos de un segundo. |
| Se vuelve a pedir el modelo que ya corre | Se quita el pendiente. |

Recargar deja entre 0,2 y 1 s sin `modelV2` en la GPU del PC; en chestnut hay que medirlo,
porque los pesos viajan por USB. Si el modelo pedido no carga, se carga lo que daría el
arranque (el siguiente candidato) y no se reintenta hasta que algo cambie: un modelo roto no
se recarga en cada parada.

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

**`OrbitModelos`** (JSON, lo escribe el gestor `orbit_modelos` cada 5 s con el coche
apagado): el dispositivo (`dispositivo`, `nombre_dispositivo`, `oficial`), si chestnut está
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
serie. Si la desconexión hace fallar antes la ejecución en la GPU, modeld se cae, el manager
lo reinicia y, al no ver la gráfica, carga el de serie.

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
| `cambio.py` | Cambio de modelo en marcha: cuándo recarga modeld. |
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
- **Orden de la app.** Hoy el modelo se elige escribiendo `OrbitModeloDeseado`. Cuando la app
  tenga la orden (por ejemplo `model_select`, por el mando ORBIT v2: `command_spec.py` →
  router → Param), solo tiene que escribir este mismo Param.
- **Telemetría y pantalla.** Falta enviar `OrbitModeloActivo` y `OrbitModelos` a la app (un
  grupo "Modelo" en `telemetria_grupos.py`) y mostrar un aviso en el comma cuando se vuelve al
  de serie.
- **Probar con el hardware.** Hay que ver que chestnut se detecta (USB `0xADD1:0x0001`) y si
  hace falta flashearle firmware. También hay que medir cuánto tarda compilar en el comma y
  cuánto tarda el cambio en marcha, porque los pesos viajan por USB.
- **comma 3X.** En el código se trata igual que el comma four, salvo la cámara y los avisos.
  Falta probarlo en el coche: el GPS con el cable puesto y la velocidad del USB.
