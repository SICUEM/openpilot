#!/usr/bin/env python3
"""Deja un paquete de modelo LISTO para un destino y una camara: si ya trae un .pkl valido lo
acepta tal cual; si no, compila sus ONNX con el compile_modeld.py del repo.

NO HAY COMPILADOR PROPIO. Se llama a selfdrive/modeld/compile_modeld.py, el mismo que usa el
SConscript, con los mismos flags de tinygrad (helpers.usbgpu_tg_flags para chestnut): un
.pkl compilado con otros flags o con otro tinygrad no carga en modeld.

ORDEN:
  1. ya LISTO (marcador vigente) ............ nada que hacer
  2. ya fallo con estas mismas entradas ...... no se repite (repetir solo vuelve a fallar)
  3. trae driving_tinygrad.pkl ............... se valida (contrato, camara, compilado para AMD,
                                               warp en el dispositivo con el que modeld le da
                                               los frames) y, si vale, se acepta sin compilar
  4. trae los dos ONNX ....................... se validan y se compilan (solo si la GPU de
                                               destino esta disponible: chestnut conectado)

Compilar para chestnut ABRE la GPU en exclusiva: solo con el coche apagado (el gestor corre
only_offroad) y nunca a la vez que modeld.

DESTINOS: usbgpu (chestnut, la AMD por USB), local (el backend del ultimo scons, para conducir
en el simulador sin GPU) y gpu_pc (chestnut simulado con la GPU NVIDIA del PC: CUDA con nvrtc
y pesos en fp32, ver compilar_fp32.py).

Uso manual (PC o comma):
  python3 orbit/modelos/compilar.py <carpeta_del_modelo> --destino local --camara 1928x1208
"""
import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from openpilot.common.basedir import BASEDIR
from openpilot.common.transformations.model import MEDMODEL_INPUT_SIZE
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.selfdrive.modeld.helpers import get_tg_input_devices, usbgpu_tg_flags
from openpilot.orbit.modelos import paquete as pq

COMPILE_MODELD = os.path.join(BASEDIR, "selfdrive", "modeld", "compile_modeld.py")
COMPILAR_FP32 = os.path.join(BASEDIR, "orbit", "modelos", "compilar_fp32.py")
MODELD_PROCESS = "selfdrive.modeld.modeld"

LISTO = "listo"
ERROR = "error"
PENDIENTE_CHESTNUT = "pendiente_chestnut"  # hay que compilar y chestnut no esta conectado
SIN_MODELO = "sin_modelo"                  # la carpeta no trae ni .pkl ni los dos ONNX


FASE_VALIDAR = "validar"
FASE_COMPILAR = "compilar"
LINEAS_LOG_ERROR = 8


@dataclass
class Resultado:
  estado: str
  detalle: str = ""
  origen: str = ""     # "entregado" | "compilado" cuando esta listo
  fase: str = ""       # con ERROR: FASE_VALIDAR | FASE_COMPILAR (errores.py)
  cacheado: bool = False  # ERROR ya registrado en un intento anterior con las mismas entradas


def ruta_error(paq: pq.Paquete, destino: str, cam: tuple[int, int]) -> Path:
  return paq.ruta / pq.DIR_COMPILADO / f"{destino}_{pq.camara_str(cam)}.error.json"


def ruta_log(paq: pq.Paquete, destino: str, cam: tuple[int, int]) -> Path:
  return paq.ruta / pq.DIR_COMPILADO / f"{destino}_{pq.camara_str(cam)}.log"


def cola_log(ruta: Path, lineas: int = LINEAS_LOG_ERROR) -> str:
  """Las ultimas lineas utiles del log de compile_modeld: ahi esta el porque del fallo."""
  try:
    texto = ruta.read_text(errors="replace").splitlines()
  except OSError:
    return ""
  utiles = [l.strip() for l in texto if l.strip() and not l.startswith("#")]
  return " | ".join(utiles[-lineas:])


def entorno_cuda_pc() -> dict[str, str]:
  """tinygrad compila CUDA con nvrtc y necesita cuda_fp16.h. Si no los encuentra cae EN SILENCIO
  a su generador PTX propio, que una GTX 10xx (Pascal) rechaza al cargar (CUDA_ERROR_INVALID_PTX).
  Vienen en los paquetes pip nvidia-cuda-nvrtc-cu12 y nvidia-cuda-runtime-cu12 del venv."""
  try:
    import nvidia.cuda_nvrtc
    import nvidia.cuda_runtime
  except ImportError:
    return {}
  nvrtc = Path(list(nvidia.cuda_nvrtc.__path__)[0]) / "lib" / "libnvrtc.so.12"
  runtime = Path(list(nvidia.cuda_runtime.__path__)[0])
  if not nvrtc.is_file() or not (runtime / "include" / "cuda_fp16.h").is_file():
    return {}
  return {"NVRTC_PATH": str(nvrtc), "CUDA_PATH": str(runtime)}


def dispositivos_entrada(destino: str) -> dict[str, str]:
  """WARP_DEV y QUEUE_DEV con los que modeld alimenta un .pkl de este destino: tienen que ser los
  mismos con los que se compilo (flags_tinygrad)."""
  if destino == pq.DESTINO_GPU_PC:
    # el frame de camara del simulador vive en memoria del host: el warp va en CPU
    return {"WARP_DEV": "CPU", "QUEUE_DEV": "CUDA"}
  return get_tg_input_devices(MODELD_PROCESS, usbgpu=destino == pq.DESTINO_USBGPU)


def flags_tinygrad(destino: str) -> dict[str, str]:
  if destino == pq.DESTINO_USBGPU:
    flags = usbgpu_tg_flags(get_tg_input_devices(MODELD_PROCESS, usbgpu=True)['WARP_DEV'])
  elif destino == pq.DESTINO_GPU_PC:
    dev = dispositivos_entrada(destino)
    flags = f"DEV={dev['QUEUE_DEV']} WARP_DEV={dev['WARP_DEV']} JIT_BATCH_SIZE=0"
  else:
    # el backend con el que se compilo el repo (tg_input_devices.json lo escribe el SConscript)
    dev = get_tg_input_devices(MODELD_PROCESS, usbgpu=False)
    queue = 'CPU:LLVM' if dev['QUEUE_DEV'] == 'CPU' and sys.platform != 'darwin' else dev['QUEUE_DEV']
    flags = f"DEV={queue} WARP_DEV={dev['WARP_DEV']} JIT_BATCH_SIZE=0"
  return dict(kv.split('=', 1) for kv in flags.split())


def validar_pkl_entregado(paq: pq.Paquete, destino: str, cam: tuple[int, int]) -> list[str]:
  try:
    info = pq.leer_pkl(paq.pkl_entregado)
  except (OSError, ValueError) as e:
    return [str(e)]
  errores, _ = pq.comparar_contrato(info["metadata"]["vision"], info["metadata"]["on_policy"])
  if not info["run_policy"]:
    errores.append("el .pkl no trae run_policy")
  if tuple(cam) not in info["camaras"]:
    trae = ', '.join(pq.camara_str(c) for c in info['camaras']) or 'ninguna'
    errores.append(f"el .pkl no trae el warp de la camara {pq.camara_str(cam)} (trae {trae})")
  if destino == pq.DESTINO_USBGPU and not info["amd"]:
    errores.append("el .pkl no esta compilado para la GPU AMD (chestnut)")
  if destino == pq.DESTINO_GPU_PC and "CUDA" not in info["dispositivos"]:
    errores.append("el .pkl no esta compilado para CUDA (chestnut simulado del PC)")
  if destino != pq.DESTINO_LOCAL:
    # el warp recibe los frames de camara en WARP_DEV: compilado para otro, carga pero revienta
    # al ejecutarse (p. ej. compilado en un PC con WARP_DEV=CPU y en el comma va en QCOM)
    warp = dispositivos_entrada(destino)["WARP_DEV"]
    if not any(d.split(":")[0] == warp.split(":")[0] for d in info["dispositivos"]):
      trae = ', '.join(info['dispositivos']) or 'ninguno'
      errores.append(f"el .pkl no tiene el warp en {warp}, que es donde modeld le da los frames (trae {trae})")
  return errores


def validar_onnx(paq: pq.Paquete) -> list[str]:
  try:
    vision, politica = pq.metadata_onnx(paq.vision_onnx), pq.metadata_onnx(paq.policy_onnx)
  except Exception as e:
    return [f"no se pueden leer los ONNX: {type(e).__name__}: {e}"]
  errores, _ = pq.comparar_contrato(vision, politica)
  return errores


def compilar_onnx(paq: pq.Paquete, destino: str, cam: tuple[int, int]) -> Path:
  salida = pq.ruta_pkl_compilado(paq.ruta, destino, cam)
  tmp = salida.with_name(salida.name + ".tmp")
  salida.parent.mkdir(parents=True, exist_ok=True)
  model_w, model_h = MEDMODEL_INPUT_SIZE
  entorno = {**os.environ, **flags_tinygrad(destino)}
  if destino == pq.DESTINO_GPU_PC:
    if not (cuda := entorno_cuda_pc()):
      raise RuntimeError("faltan nvrtc y las cabeceras de CUDA en el venv (ver orbit/modelos/README.md, chestnut simulado)")
    entorno.update(cuda)
  cmd = [sys.executable, COMPILAR_FP32 if destino == pq.DESTINO_GPU_PC else COMPILE_MODELD,
         '--model-size', f'{model_w}x{model_h}',
         '--camera-resolutions', pq.camara_str(cam),
         '--vision-onnx', str(paq.vision_onnx),
         '--on-policy-onnx', str(paq.policy_onnx),
         '--output', str(tmp),
         '--frame-skip', str(ModelConstants.MODEL_RUN_FREQ // ModelConstants.MODEL_CONTEXT_FREQ)]
  with open(ruta_log(paq, destino, cam), "w") as log:
    log.write(f"# {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
    log.flush()
    ret = subprocess.run(cmd, cwd=BASEDIR, env=entorno,
                         stdout=log, stderr=subprocess.STDOUT, check=False)
  if ret.returncode != 0 or not tmp.is_file():
    tmp.unlink(missing_ok=True)
    log = ruta_log(paq, destino, cam)
    raise RuntimeError(f"compile_modeld termino con codigo {ret.returncode} (log {log.name}): {cola_log(log)}")
  os.replace(tmp, salida)
  return salida


def preparar(paq: pq.Paquete, destino: str, cam: tuple[int, int], gpu_disponible: bool,
             al_compilar=None) -> Resultado:
  """Ver el docstring del modulo. `gpu_disponible`: la GPU de destino se puede abrir ahora
  (chestnut conectado y coche apagado). `al_compilar()` se llama justo antes de compilar,
  para que quien llama publique el estado (compilar tarda minutos)."""
  if (pkl := pq.pkl_listo(paq.ruta, destino, cam)) is not None:
    origen = (pq.leer_json(pq.ruta_marcador(paq.ruta, destino, cam)) or {}).get("origen", "")
    return Resultado(LISTO, str(pkl), origen)

  huella = pq.huella_entradas(paq, destino, cam)
  fallo = pq.leer_json(ruta_error(paq, destino, cam))
  if fallo and fallo.get("huella") == huella:
    return Resultado(ERROR, str(fallo.get("detalle", "")), fase=str(fallo.get("fase", "")), cacheado=True)

  def fallar(detalle: str, fase: str = FASE_VALIDAR) -> Resultado:
    pq.escribir_json_atomico(ruta_error(paq, destino, cam), {"huella": huella, "detalle": detalle, "fase": fase,
                                                            "ts": time.time_ns() // 1_000_000_000})
    return Resultado(ERROR, detalle, fase=fase)

  errores_pkl: list[str] = []
  if paq.tiene_pkl:
    errores_pkl = validar_pkl_entregado(paq, destino, cam)
    if not errores_pkl:
      pq.escribir_marcador(paq.ruta, destino, cam, paq.pkl_entregado, "entregado")
      ruta_error(paq, destino, cam).unlink(missing_ok=True)
      return Resultado(LISTO, str(paq.pkl_entregado), "entregado")

  if not paq.tiene_onnx:
    if paq.tiene_pkl:
      return fallar("el .pkl entregado no vale y no hay ONNX para compilar: " + "; ".join(errores_pkl))
    return Resultado(SIN_MODELO, f"faltan {pq.PKL_ENTREGADO} o {pq.VISION_ONNX} + {pq.POLICY_ONNX}")

  if errores := validar_onnx(paq):
    return fallar("; ".join(errores))
  if not gpu_disponible:
    previo = (" (el .pkl entregado no vale: " + "; ".join(errores_pkl) + ")") if errores_pkl else ""
    return Resultado(PENDIENTE_CHESTNUT, "hay que compilarlo y chestnut no esta disponible" + previo)

  if al_compilar is not None:
    al_compilar()
  try:
    salida = compilar_onnx(paq, destino, cam)
  except Exception as e:
    return fallar(str(e), FASE_COMPILAR)
  pq.escribir_marcador(paq.ruta, destino, cam, salida, "compilado")
  ruta_error(paq, destino, cam).unlink(missing_ok=True)
  return Resultado(LISTO, str(salida), "compilado")


def _parse_cam(s: str) -> tuple[int, int]:
  w, h = s.lower().split('x')
  return int(w), int(h)


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("carpeta", type=Path)
  ap.add_argument("--destino", choices=(pq.DESTINO_LOCAL, pq.DESTINO_USBGPU, pq.DESTINO_GPU_PC), default=pq.DESTINO_LOCAL)
  ap.add_argument("--camara", type=_parse_cam, default=(1928, 1208), help="WxH (3X: 1928x1208, comma four: 1344x760)")
  ap.add_argument("--reintentar", action="store_true", help="olvida un fallo anterior con las mismas entradas")
  args = ap.parse_args()

  paquete = pq.inspeccionar(args.carpeta)
  if args.reintentar:
    ruta_error(paquete, args.destino, args.camara).unlink(missing_ok=True)
  r = preparar(paquete, args.destino, args.camara, gpu_disponible=True,
               al_compilar=lambda: print("compilando (puede tardar varios minutos)..."))
  print(f"{paquete.modelo_id}: {r.estado} {r.origen} {r.detalle}")
  sys.exit(0 if r.estado == LISTO else 1)
