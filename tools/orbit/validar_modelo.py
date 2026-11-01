#!/usr/bin/env python3
"""
validar_modelo.py — comprueba EN EL PC que un modelo del equipo cumple el contrato de ORBIT
antes de llevarlo al coche (orbit/modelos/README.md).

Uso (en el PC, dentro del repo, con el .venv activo):
  PYTHONPATH=.. python3 tools/orbit/validar_modelo.py <carpeta_del_modelo>
  PYTHONPATH=.. python3 tools/orbit/validar_modelo.py <carpeta_del_modelo> --compilar-local
  PYTHONPATH=.. python3 tools/orbit/validar_modelo.py --ejemplo-serie-grande /tmp/modelo_grande

Que mira:
  - driving_vision.onnx + driving_on_policy.onnx: entradas, salidas y tamanos contra los ONNX
    de serie del repo (lo que el modeld de ORBIT sabe alimentar e interpretar).
  - driving_tinygrad.pkl (si viene ya compilado): el mismo contrato leyendo su metadata, para
    que camaras trae warp (3X 1928x1208, comma four 1344x760) y si esta compilado para la GPU
    AMD de chestnut. Que lo cargue de verdad solo se sabe en el coche: depende de que el
    tinygrad con el que se compilo sea el del repo.

--compilar-local compila los ONNX para el backend de este PC (CPU o CUDA, el del ultimo scons)
y lo deja LISTO para el destino "local": asi se puede conducir con el en el simulador
(OrbitModeloDeseado = <id>; ver el README).

--ejemplo-serie-grande crea un paquete de prueba con el modelo grande de serie del repo
(big_driving_*.onnx, que cumple el contrato): sirve para probar todo el camino sin tener aun
los modelos del equipo.

Sale con 0 si el modelo vale y 1 si no.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from openpilot.orbit.modelos import compilar
from openpilot.orbit.modelos import paquete as pq


def _cam(s: str) -> tuple[int, int]:
  w, h = s.lower().split("x")
  return int(w), int(h)


def imprimir(ok: bool, texto: str) -> None:
  print(f"  [{'OK' if ok else 'XX'}] {texto}")


def revisar_onnx(paq: pq.Paquete) -> bool:
  print(f"ONNX ({pq.VISION_ONNX} + {pq.POLICY_ONNX})")
  try:
    vision, politica = pq.metadata_onnx(paq.vision_onnx), pq.metadata_onnx(paq.policy_onnx)
  except Exception as e:
    imprimir(False, f"no se pueden leer: {type(e).__name__}: {e}")
    return False
  print(f"    vision:    entradas {vision['input_shapes']}  salidas {vision['output_shapes']}")
  print(f"    on_policy: entradas {politica['input_shapes']}  salidas {politica['output_shapes']}")
  errores, avisos = pq.comparar_contrato(vision, politica)
  for a in avisos:
    print(f"  [..] {a}")
  for e in errores:
    imprimir(False, e)
  if not errores:
    imprimir(True, "cumple el contrato")
  return not errores


def revisar_pkl(paq: pq.Paquete) -> tuple[bool, bool]:
  """(estructura y contrato bien, compilado para la AMD de chestnut)."""
  print(f"PKL ({pq.PKL_ENTREGADO}, ya compilado)")
  try:
    info = pq.leer_pkl(paq.pkl_entregado)
  except (OSError, ValueError) as e:
    imprimir(False, str(e))
    return False, False
  errores, avisos = pq.comparar_contrato(info["metadata"]["vision"], info["metadata"]["on_policy"])
  for a in avisos:
    print(f"  [..] {a}")
  for e in errores:
    imprimir(False, e)
  if not errores:
    imprimir(True, "su metadata cumple el contrato")
  imprimir(info["run_policy"], "trae run_policy")
  camaras = ", ".join(pq.camara_str(c) for c in info["camaras"]) or "ninguna"
  imprimir(bool(info["camaras"]), f"warp para camaras: {camaras}")
  dispositivos = ", ".join(info["dispositivos"]) or "desconocidos"
  if info["amd"]:
    imprimir(True, f"compilado para la GPU AMD de chestnut (dispositivos: {dispositivos})")
  else:
    imprimir(False, f"NO esta compilado para la GPU AMD (dispositivos: {dispositivos}): en el coche no se usara " +
             "(se compilaran los ONNX si los hay)")
  return not errores and info["run_policy"] and bool(info["camaras"]), info["amd"]


def crear_ejemplo(destino: Path) -> None:
  from openpilot.selfdrive.modeld.helpers import MODELS_DIR
  destino.mkdir(parents=True, exist_ok=True)
  for src, dst in (("big_driving_vision.onnx", pq.VISION_ONNX), ("big_driving_on_policy.onnx", pq.POLICY_ONNX)):
    shutil.copyfile(MODELS_DIR / src, destino / dst)
  manifiesto = {"nombre": "Grande de serie (prueba)", "version": "0.11.2",
                "notas": "big_driving de openpilot, para probar el camino de chestnut"}
  (destino / pq.MANIFIESTO).write_text(json.dumps(manifiesto, indent=2) + "\n")
  print(f"paquete de ejemplo creado en {destino}")


def main() -> int:
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("carpeta", type=Path, nargs="?")
  ap.add_argument("--compilar-local", action="store_true", help="compilar los ONNX para este PC (simulador)")
  ap.add_argument("--camara", type=_cam, default=(1928, 1208), help="WxH para --compilar-local (simulador: 1928x1208)")
  ap.add_argument("--ejemplo-serie-grande", type=Path, metavar="CARPETA", help="crear un paquete de prueba y validarlo")
  args = ap.parse_args()

  if args.ejemplo_serie_grande:
    crear_ejemplo(args.ejemplo_serie_grande)
    args.carpeta = args.ejemplo_serie_grande
  if args.carpeta is None:
    ap.error("falta la carpeta del modelo")
  if not args.carpeta.is_dir():
    print(f"no existe la carpeta {args.carpeta}")
    return 1

  paq = pq.inspeccionar(args.carpeta)
  print(f"Modelo '{paq.modelo_id}'  nombre: {paq.nombre}  version: {paq.version or '-'}")
  if not pq.id_valido(paq.modelo_id):
    imprimir(False, "el nombre de la carpeta no vale como id (letras, numeros, . _ -; max 64)")
    return 1
  if not paq.tiene_onnx and not paq.tiene_pkl:
    imprimir(False, f"no hay {pq.PKL_ENTREGADO} ni la pareja {pq.VISION_ONNX} + {pq.POLICY_ONNX}")
    return 1

  ok_onnx = revisar_onnx(paq) if paq.tiene_onnx else False
  ok_pkl, pkl_amd = revisar_pkl(paq) if paq.tiene_pkl else (False, False)
  # con ONNX validos vale en los dos sitios: el coche (o este PC) los compila para su GPU
  vale_chestnut = ok_onnx or (ok_pkl and pkl_amd)
  vale_pc = ok_onnx or (ok_pkl and not pkl_amd)

  if args.compilar_local:
    if not ok_onnx:
      print("no se compila: los ONNX no cumplen el contrato (o no estan)")
      return 1
    flags = " ".join(f"{k}={v}" for k, v in compilar.flags_tinygrad(pq.DESTINO_LOCAL).items())
    print(f"compilando para este PC ({flags}), camara {pq.camara_str(args.camara)}...")
    compilar.ruta_error(paq, pq.DESTINO_LOCAL, args.camara).unlink(missing_ok=True)
    r = compilar.preparar(paq, pq.DESTINO_LOCAL, args.camara, gpu_disponible=True)
    imprimir(r.estado == compilar.LISTO, f"{r.estado} {r.origen} {r.detalle}")
    if r.estado != compilar.LISTO:
      return 1
    destino = pq.dir_modelos() / paq.modelo_id
    if paq.ruta.resolve() != destino.resolve():
      print(f"para el simulador, deja la carpeta en {destino} (o exporta ORBIT_MODELS_DIR={paq.ruta.parent})")

  veredicto = {True: "VALE", False: "NO VALE"}
  print(f"RESULTADO  chestnut (coche): {veredicto[vale_chestnut]}   simulador (PC): {veredicto[vale_pc]}")
  return 0 if vale_chestnut else 1


if __name__ == "__main__":
  sys.exit(main())
