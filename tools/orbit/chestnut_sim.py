#!/usr/bin/env python3
"""
chestnut_sim.py — prueba en el PC el camino entero de los modelos del equipo con un chestnut
SIMULADO: la GPU NVIDIA del PC hace de chestnut y la CPU hace de comma (orbit/modelos/README.md,
"Probar en el PC").

Uso (en el PC, dentro del repo, con el .venv activo):
  PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py conectar      # "enchufa" chestnut
  PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py desconectar   # "desenchufa" chestnut
  PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py preparar <id> # compila ya para la GPU del PC
  PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py elegir <id>   # lo que hara la app (serie = el de serie)
  PYTHONPATH=.. python3 tools/orbit/chestnut_sim.py ver           # que pasa, en vivo (Ctrl+C para salir)

Con openpilot APAGADO (offroad) el gestor orbit_modelos compila solo los modelos de
~/.comma/orbit_models para la GPU; `preparar` hace lo mismo sin esperarle.
"""
import argparse
import json
import sys
import time

from openpilot.common.params import Params
from openpilot.orbit.modelos import chestnut as cn
from openpilot.orbit.modelos import compilar
from openpilot.orbit.modelos import errores
from openpilot.orbit.modelos import paquete as pq
from openpilot.orbit.modelos import seleccion


def conectar(si: bool) -> None:
  ruta = cn.archivo_simulado()
  if si:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.touch()
  else:
    ruta.unlink(missing_ok=True)
  print(f"chestnut simulado {'CONECTADO' if si else 'DESCONECTADO'} ({ruta})")


def preparar(modelo_id: str) -> int:
  perfil = cn.PERFILES["pc"]
  paq = pq.inspeccionar(pq.dir_modelos() / modelo_id)
  compilar.ruta_error(paq, perfil.destino, perfil.camara).unlink(missing_ok=True)
  t = time.monotonic()
  r = compilar.preparar(paq, perfil.destino, perfil.camara, gpu_disponible=True,
                        al_compilar=lambda: print(f"compilando {modelo_id} para la GPU del PC (fp32)..."))
  print(f"{modelo_id}: {r.estado} {r.origen} {r.detalle} ({time.monotonic() - t:.0f} s)")
  return 0 if r.estado == compilar.LISTO else 1


def leer(params, clave) -> dict:
  try:
    return json.loads(params.get(clave) or "{}")
  except (TypeError, ValueError):
    return {}


def ver() -> None:
  import cereal.messaging as messaging
  params = Params()
  sm = messaging.SubMaster(["modelV2", "carState", "carControl"])
  tiempos: list[float] = []
  while True:
    t = time.monotonic()
    while time.monotonic() - t < 1.0:
      sm.update(100)
      if sm.updated["modelV2"]:
        tiempos.append(sm["modelV2"].modelExecutionTime * 1000)
    activo, modelos = leer(params, seleccion.PARAM_ACTIVO), leer(params, "OrbitModelos")
    deseado = seleccion.leer_deseado(params) or "serie"
    modelo = f"{activo.get('origen', '-')} {activo.get('modelo_id') or ''}".strip()
    donde = "CHESTNUT" if activo.get("en_chestnut") else "comma"
    ms = f"{sorted(tiempos)[len(tiempos) // 2]:.0f} ms ({len(tiempos)}/s)" if tiempos else "sin modelV2"
    tiempos.clear()
    cs = sm["carState"]
    conexion = "CONECTADO" if cn.presente() else "desconectado"
    print(f"\n[{time.strftime('%H:%M:%S')}] chestnut {conexion} | pedido: {deseado} | corriendo: {modelo} en {donde} | modelo {ms}")
    acople = "ACOPLADO" if sm["carControl"].enabled else "desacoplado"
    print(f"  coche: {cs.vEgo * 3.6:.0f} km/h{' parado' if cs.standstill else ''} | openpilot {acople}")
    if activo.get("pendiente"):
      print(f"  PENDIENTE: {activo['pendiente']} (se aplica con el coche parado y openpilot desacoplado)")
    if activo.get("motivo"):
      print(f"  motivo: {activo['motivo']}")
    for m in modelos.get("modelos", []):
      print(f"  modelo {m['id']}: {m['estado']} {m.get('origen', '')} {m.get('detalle', '')[:100]}")
    if fallos := errores.leer(params):
      print(f"  ultimo fallo: {errores.formatear(fallos[-1])}")


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  sub = ap.add_subparsers(dest="orden", required=True)
  sub.add_parser("conectar")
  sub.add_parser("desconectar")
  sub.add_parser("preparar").add_argument("id")
  sub.add_parser("elegir").add_argument("id")
  sub.add_parser("ver")
  args = ap.parse_args()

  if args.orden in ("conectar", "desconectar"):
    conectar(args.orden == "conectar")
  elif args.orden == "preparar":
    sys.exit(preparar(args.id))
  elif args.orden == "elegir":
    Params().put(seleccion.PARAM_DESEADO, args.id)
    print(f"{seleccion.PARAM_DESEADO} = {args.id}")
  else:
    try:
      ver()
    except KeyboardInterrupt:
      pass
