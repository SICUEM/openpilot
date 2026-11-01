"""Que modelo carga modeld: el que pide la app (Param OrbitModeloDeseado) si se puede, y si no,
el de serie. modeld prueba los candidatos EN ORDEN y se queda con el primero que carga; el
ultimo es siempre el modelo pequeno de serie en el comma, que no depende de chestnut ni de
ningun paquete.

  1. el modelo del equipo pedido ... si chestnut esta conectado y el paquete esta LISTO para el
                                      destino de chestnut de este dispositivo y su camara
                                      (chestnut.perfil); en el PC tambien vale LISTO para local
  2. el modelo grande de serie ..... si chestnut (el real) esta conectado y esta compilado (lo
                                      que ya hacia modeld antes de ORBIT)
  3. el modelo pequeno de serie .... siempre

Se elige al arrancar modeld y se vuelve a elegir EN MARCHA cuando cambian OrbitModeloDeseado o
la conexion de chestnut (orbit/modelos/cambio.py): el cambio se aplica con el coche parado y
openpilot desacoplado, sin reiniciar nada.

Lo que se cargo y por que se publica en OrbitModeloActivo (JSON) para la app y la pantalla.
"""
import json
import time
from dataclasses import dataclass
from pathlib import Path

from openpilot.system.hardware import PC
from openpilot.selfdrive.modeld.helpers import modeld_pkl_path
from openpilot.orbit.modelos import paquete as pq
from openpilot.orbit.modelos.compilar import dispositivos_entrada

PARAM_DESEADO = "OrbitModeloDeseado"
PARAM_ACTIVO = "OrbitModeloActivo"
# valores de OrbitModeloDeseado que significan "el de serie" (ademas de vacio / sin escribir)
DESEADO_SERIE = ("", "serie", "stock")

EQUIPO = "equipo"
SERIE_GRANDE = "serie_grande"
SERIE = "serie"


@dataclass(frozen=True)
class Candidato:
  origen: str              # EQUIPO | SERIE_GRANDE | SERIE
  pkl: Path
  destino: str             # paquete.DESTINO_*: en que se ejecuta (local = el comma)
  modelo_id: str | None = None

  @property
  def usbgpu(self) -> bool:
    return self.destino == pq.DESTINO_USBGPU

  @property
  def en_chestnut(self) -> bool:
    return self.destino in (pq.DESTINO_USBGPU, pq.DESTINO_GPU_PC)

  def dispositivos(self) -> dict[str, str]:
    return dispositivos_entrada(self.destino)


def leer_deseado(params) -> str | None:
  try:
    valor = params.get(PARAM_DESEADO)
  except Exception:
    return None
  if isinstance(valor, bytes):
    valor = valor.decode(errors="replace")
  valor = (valor or "").strip()
  return None if valor in DESEADO_SERIE else valor


def candidatos(deseado: str | None, chestnut: bool, grande_compilado: bool, cam: tuple[int, int],
               destino: str = pq.DESTINO_USBGPU, base: Path | None = None,
               local: bool = PC) -> tuple[list[Candidato], list[str]]:
  """(candidatos en orden, motivos por los que se descarto el modelo pedido). `destino`: el de
  chestnut en este dispositivo (chestnut.perfil). `local`: probar tambien el modelo compilado
  para el backend del PC (validar_modelo.py --compilar-local)."""
  lista: list[Candidato] = []
  motivos: list[str] = []

  if deseado is not None:
    ruta = (base or pq.dir_modelos()) / deseado if pq.id_valido(deseado) else None
    if ruta is None:
      motivos.append(f"id de modelo no valido: {deseado!r}")
    elif not ruta.is_dir():
      motivos.append(f"el modelo {deseado} no esta en el coche")
    else:
      if not chestnut:
        motivos.append("chestnut no esta conectado")
      elif (pkl := pq.pkl_listo(ruta, destino, cam)) is not None:
        lista.append(Candidato(EQUIPO, pkl, destino, deseado))
      else:
        motivos.append(f"el modelo {deseado} no esta listo para {destino} {pq.camara_str(cam)}")
      if not lista and local and (pkl := pq.pkl_listo(ruta, pq.DESTINO_LOCAL, cam)) is not None:
        lista.append(Candidato(EQUIPO, pkl, pq.DESTINO_LOCAL, deseado))

  if chestnut and grande_compilado and destino == pq.DESTINO_USBGPU:
    lista.append(Candidato(SERIE_GRANDE, modeld_pkl_path(usbgpu=True), pq.DESTINO_USBGPU))
  lista.append(Candidato(SERIE, modeld_pkl_path(usbgpu=False), pq.DESTINO_LOCAL))
  return lista, motivos


def estado_activo(cargado: Candidato, deseado: str | None, chestnut: bool, motivos: list[str]) -> dict:
  return {
    "v": 1,
    "origen": cargado.origen,
    "modelo_id": cargado.modelo_id,
    "deseado": deseado,
    "chestnut": chestnut,
    "destino": cargado.destino,
    "en_chestnut": cargado.en_chestnut,
    "usbgpu": cargado.usbgpu,
    # vacio = se cargo justo lo que se pidio
    "motivo": "; ".join(motivos),
    "ts_ms": time.time_ns() // 1_000_000,
  }


def publicar_activo(params, estado: dict) -> None:
  params.put(PARAM_ACTIVO, json.dumps(estado, sort_keys=True))
