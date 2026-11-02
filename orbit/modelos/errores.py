#!/usr/bin/env python3
"""Registro de los fallos de los modelos del equipo: POR QUE no se uso o dejo de usarse un modelo,
para verlo en las pruebas reales sin tener que leer los logs de modeld.

Cada entrada va al Param OrbitModeloErrores (JSON, lista con las MAX_ENTRADAS mas recientes,
PERSISTENT: sobrevive a reinicios) y a cloudlog como evento "orbit_modelo_error".

  fase ........ donde fallo:
                  validar      el gestor rechaza el .pkl entregado o los ONNX (contrato, camara...)
                  compilar     compile_modeld fallo (con el final de su log)
                  eleccion     se pidio un modelo y modeld cargo otro (motivos de seleccion)
                  cargar       el .pkl no se pudo cargar (pickle, tinygrad distinto, GPU ocupada...)
                  ejecutar     el modelo cargo pero fallo al ejecutarse
                  salidas      el modelo da salidas no finitas (NaN / inf)
                  arranque     modeld murio con el modelo en prueba (cuelgue, segfault...)
                  chestnut     chestnut se desconecto con el modelo corriendo en el
                  rendimiento  el modelo va mas lento que el ritmo de modeld (aviso)
  nivel ....... "error" (el modelo no se usa) | "aviso" (se usa, pero hay algo que mirar)

Ver el registro en el comma o en el PC:
  python3 -m openpilot.orbit.modelos.errores
"""
import json
import time
import traceback

from openpilot.common.swaglog import cloudlog

PARAM_ERRORES = "OrbitModeloErrores"
MAX_ENTRADAS = 30
MAX_DETALLE = 600

ERROR = "error"
AVISO = "aviso"


def describir(e: BaseException) -> str:
  """Tipo, mensaje y el ultimo punto del traceback: lo minimo para saber por donde empezar."""
  texto = f"{type(e).__name__}: {e}"
  if (tb := traceback.extract_tb(e.__traceback__)):
    f = tb[-1]
    texto += f" (en {f.filename.rsplit('/', 1)[-1]}:{f.lineno} {f.name})"
  return texto


def leer(params) -> list[dict]:
  try:
    datos = json.loads(params.get(PARAM_ERRORES) or "[]")
  except (TypeError, ValueError):
    return []
  return datos if isinstance(datos, list) else []


def registrar(params, fase: str, detalle: str, modelo_id: str | None = None, nivel: str = ERROR, **extra) -> dict:
  entrada = {"ts_ms": time.time_ns() // 1_000_000, "fase": fase, "nivel": nivel,
             "modelo_id": modelo_id, "detalle": detalle[:MAX_DETALLE], **extra}
  cloudlog.event("orbit_modelo_error", error=nivel == ERROR, **entrada)
  lista = leer(params)
  # el mismo fallo seguido (p. ej. en cada arranque) no se come el registro: se cuenta
  if lista and all(lista[-1].get(k) == entrada[k] for k in ("fase", "modelo_id", "detalle")):
    entrada["veces"] = int(lista[-1].get("veces", 1)) + 1
    lista.pop()
  try:
    params.put(PARAM_ERRORES, json.dumps((lista + [entrada])[-MAX_ENTRADAS:], sort_keys=True))
  except Exception:
    cloudlog.exception("orbit: no se pudo guardar OrbitModeloErrores")
  return entrada


def formatear(e: dict) -> str:
  hora = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e.get("ts_ms", 0) / 1000))
  extra = " ".join(f"{k}={e[k]}" for k in ("origen", "destino", "veces") if e.get(k))
  return f"[{hora}] {e.get('nivel', '?').upper()} {e.get('fase', '?')} {e.get('modelo_id') or '-'} {extra}\n    {e.get('detalle', '')}"


if __name__ == "__main__":
  from openpilot.common.params import Params
  lista = leer(Params())
  print("\n".join(formatear(e) for e in lista) if lista else "sin errores registrados")
