#!/usr/bin/env python3
"""orbit_modelos: con el coche APAGADO, deja listos para chestnut los modelos del equipo que hay
en el comma y publica en OrbitModelos (JSON) el estado de cada uno.

Detecta el dispositivo (chestnut.perfil): en el comma four y el 3X compila para la AMD de
chestnut con la camara de cada uno; en el PC, para el chestnut simulado con la GPU NVIDIA.

Corre only_offroad (system/manager/process_config.py) porque compilar abre la GPU de chestnut
en exclusiva y modeld la necesita en marcha. Si el coche arranca a mitad de una compilacion,
el manager mata este proceso: compile_modeld escribe en un .tmp que nunca se da por bueno, y en
el siguiente offroad se vuelve a intentar.

Un modelo que ya fallo con las mismas entradas no se reintenta (compilar.preparar); se vuelve a
intentar solo si cambian sus ficheros o el tinygrad del repo. Cada fallo NUEVO (validar o
compilar) queda con su motivo en OrbitModeloErrores (errores.py).

OrbitModelos se escribe solo cuando cambia algo (sin contar ts_ms): el coche puede pasar dias
apagado y no hace falta escribir en la flash cada 5 s.

OrbitModelos:
  {"v": 1, "ts_ms": ..., "dispositivo": "mici", "nombre_dispositivo": "comma four",
   "oficial": true, "chestnut": true, "usb_mbps": 10000, "avisos": [...],
   "destino": "usbgpu", "camara": "1344x760",
   "modelos": [{"id", "nombre", "version", "estado", "origen", "detalle"}]}
  estado: listo | compilando | pendiente_chestnut | error | sin_modelo
"""
import json
import time

from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware import HARDWARE
from openpilot.orbit.modelos import chestnut as cn
from openpilot.orbit.modelos import compilar
from openpilot.orbit.modelos import errores
from openpilot.orbit.modelos import paquete as pq

PARAM_MODELOS = "OrbitModelos"
PERIODO_S = 5.0
COMPILANDO = "compilando"

def entrada(paq: pq.Paquete, estado: str, origen: str = "", detalle: str = "") -> dict:
  return {"id": paq.modelo_id, "nombre": paq.nombre, "version": paq.version,
          "estado": estado, "origen": origen, "detalle": detalle[:300]}


_ultimo_publicado: dict | None = None


def publicar(params, perfil: cn.Perfil, chestnut: bool, mbps: int | None, modelos: list[dict]) -> None:
  global _ultimo_publicado
  datos = {
    "v": 1,
    "dispositivo": perfil.dispositivo,
    "nombre_dispositivo": perfil.nombre,
    "oficial": perfil.oficial,
    "chestnut": chestnut,
    "usb_mbps": mbps,
    "avisos": cn.avisos(perfil, chestnut, mbps),
    "destino": perfil.destino,
    "camara": pq.camara_str(perfil.camara),
    "modelos": modelos,
  }
  if datos == _ultimo_publicado:
    return
  params.put(PARAM_MODELOS, json.dumps({**datos, "ts_ms": time.time_ns() // 1_000_000}, sort_keys=True))
  _ultimo_publicado = datos


# Resultados que no cambian mientras no cambien las entradas: no se recalculan cada ciclo
# (validar un .pkl o un ONNX es leer cientos de MB). LISTO no hace falta: su marcador es barato.
_ESTABLES = (compilar.PENDIENTE_CHESTNUT, compilar.ERROR, compilar.SIN_MODELO)


def ciclo(params, perfil: cn.Perfil, chestnut: bool, mbps: int | None, memoria: dict) -> list[dict]:
  """`memoria`: {id: (clave, Resultado)} del ciclo anterior; se actualiza aqui."""
  cam, destino = perfil.camara, perfil.destino
  paquetes = pq.listar_paquetes()
  modelos = [entrada(p, "") for p in paquetes]
  for i, paq in enumerate(paquetes):
    clave = (pq.huella_entradas(paq, destino, cam), chestnut)
    previo = memoria.get(paq.modelo_id)
    if previo is not None and previo[0] == clave and previo[1].estado in _ESTABLES:
      r = previo[1]
    else:
      def al_compilar(i=i, paq=paq):
        modelos[i] = entrada(paq, COMPILANDO)
        publicar(params, perfil, chestnut, mbps, modelos)
        cloudlog.warning(f"orbit_modelos: compilando {paq.modelo_id} para {destino} {pq.camara_str(cam)}")
      try:
        r = compilar.preparar(paq, destino, cam, gpu_disponible=chestnut, al_compilar=al_compilar)
      except Exception as e:
        cloudlog.exception(f"orbit_modelos: fallo inesperado preparando {paq.modelo_id}")
        r = compilar.Resultado(compilar.ERROR, errores.describir(e), fase=compilar.FASE_VALIDAR)
      if previo is None or previo[1].estado != r.estado:
        cloudlog.warning(f"orbit_modelos: {paq.modelo_id} -> {r.estado} {r.origen} {r.detalle}")
      if r.estado == compilar.ERROR and not r.cacheado:
        errores.registrar(params, r.fase or compilar.FASE_VALIDAR, r.detalle, paq.modelo_id,
                          destino=destino, camara=pq.camara_str(cam), version=paq.version)
    memoria[paq.modelo_id] = (clave, r)
    modelos[i] = entrada(paq, r.estado, r.origen, r.detalle if r.estado != compilar.LISTO else "")
  for modelo_id in set(memoria) - {p.modelo_id for p in paquetes}:
    del memoria[modelo_id]
  return modelos


def main() -> None:
  params = Params()
  perfil = cn.perfil()
  if perfil is None:
    cloudlog.warning(f"orbit_modelos: dispositivo {HARDWARE.get_device_type()} sin chestnut, no hago nada")
    return
  cloudlog.warning(f"orbit_modelos: {perfil.nombre} -> destino {perfil.destino}, camara {pq.camara_str(perfil.camara)}")
  memoria: dict = {}
  while True:
    chestnut = cn.presente()
    mbps = cn.velocidad_usb_mbps() if chestnut else None
    publicar(params, perfil, chestnut, mbps, ciclo(params, perfil, chestnut, mbps, memoria))
    time.sleep(PERIODO_S)


if __name__ == "__main__":
  main()
