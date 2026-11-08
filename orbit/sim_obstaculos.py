#!/usr/bin/env python3
"""Escenario de obstaculos ESTATICOS para la simulacion MetaDrive del PC.

Diseno: docs/superpowers/specs/2026-11-08-sim-obstaculos-design.md.

La UI (seccion Simulacion del panel ORBIT) escribe el escenario en OrbitSimObstaculos y
la sim (tools/sim, GestorObstaculos) lo lee y escribe lo que ha hecho en OrbitSimEstado.
Este modulo es la UNICA definicion del formato para los dos lados.

Es PURO: no importa metadrive, ni pyray, ni Params. Asi se prueba sin levantar nada y la
UI no arrastra el simulador.

Convenciones (las de quien lo configura, no las de MetaDrive):
  - s: metros a lo largo de la ruta del ego desde la salida, medidos sobre el propio carril.
  - carril: 1 = el de la derecha EN ESE PUNTO de la ruta (cambia de numero de carriles
    segun el mapa y el tramo), o "ego" = el carril por el que sale el coche. Los presets
    usan "ego" para caer en el carril del coche en cualquier mapa.
  - lateral: metros respecto al centro del carril, positivo hacia la IZQUIERDA.
  - giro: grados sobre el rumbo del carril.
La traduccion a MetaDrive (indices y signos) la hace la sim, no este modulo.
"""
import copy
import math

PARAM_ESCENARIO = "OrbitSimObstaculos"
PARAM_ESTADO = "OrbitSimEstado"

VERSION = 1
MAX_OBSTACULOS = 30
S_MAX = 5000.0
LATERAL_MAX = 3.0
CARRIL_MAX = 6
CARRIL_EGO = "ego"
# La sim escribe el estado con latido; mas viejo que esto = no hay sim conectada.
ESTADO_MAX_EDAD_MS = 10_000

# tipo -> nombre en pantalla, clase de MetaDrive, carpeta del modelo en tools/sim/assets
# (None = viene en el MetaDrive minimal) y si es un vehiculo (se crea distinto).
TIPOS = {
  "cono":      {"nombre": "Cono",      "clase": "TrafficCone",    "modelo": "traffic_cone", "vehiculo": False},
  "barrera":   {"nombre": "Barrera",   "clase": "TrafficBarrier", "modelo": "barrier",      "vehiculo": False},
  "triangulo": {"nombre": "Triangulo", "clase": "TrafficWarning", "modelo": None,           "vehiculo": False},
  "coche":     {"nombre": "Coche",     "clase": "DefaultVehicle", "modelo": "ferra",        "vehiculo": True},
  "compacto":  {"nombre": "Compacto",  "clase": "SVehicle",       "modelo": "beetle",       "vehiculo": True},
  "suv":       {"nombre": "SUV",       "clase": "MVehicle",       "modelo": "130",          "vehiculo": True},
  "furgoneta": {"nombre": "Furgoneta", "clase": "LVehicle",       "modelo": "lada",         "vehiculo": True},
  "camion":    {"nombre": "Camion",    "clase": "XLVehicle",      "modelo": "truck",        "vehiculo": True},
}
ORDEN_TIPOS = list(TIPOS)


def escenario_vacio() -> dict:
  return {"v": VERSION, "rev": 0, "activo": False, "obstaculos": []}


def _num(valor, defecto=None):
  # bool es int en Python: "s": true no puede colarse como 1 m.
  if isinstance(valor, bool) or not isinstance(valor, (int, float)):
    return defecto
  valor = float(valor)
  return valor if math.isfinite(valor) else defecto


def normalizar_obstaculo(raw) -> tuple[dict | None, str]:
  """Devuelve (obstaculo limpio, "") o (None, motivo). Recorta en vez de rechazar cuando
  el valor tiene un arreglo obvio (lateral fuera de rango), y rechaza cuando no lo tiene
  (tipo desconocido, s ausente)."""
  if not isinstance(raw, dict):
    return None, "no es un objeto"
  tipo = raw.get("tipo")
  if tipo not in TIPOS:
    return None, f"tipo desconocido: {tipo!r}"
  s = _num(raw.get("s"))
  if s is None:
    return None, "falta s"
  carril = raw.get("carril", CARRIL_EGO)
  if carril != CARRIL_EGO and (isinstance(carril, bool) or not isinstance(carril, int)
                               or not 1 <= carril <= CARRIL_MAX):
    return None, f"carril invalido: {carril!r}"
  lateral = _num(raw.get("lateral", 0.0), 0.0)
  giro = _num(raw.get("giro", 0.0), 0.0)
  return {
    "tipo": tipo,
    "s": round(min(max(s, 0.0), S_MAX), 2),
    "carril": carril,
    "lateral": round(min(max(lateral, -LATERAL_MAX), LATERAL_MAX), 2),
    "giro": round(((giro + 180.0) % 360.0) - 180.0, 1),
  }, ""


def normalizar(raw) -> tuple[dict, list[dict]]:
  """Escenario valido a partir de lo que haya en el Param (puede ser None o basura).

  Devuelve (escenario, descartados). Cada descartado es {"i": indice original, "motivo"}:
  la sim los pasa al estado para que la UI enseñe POR QUE no aparece un obstaculo.
  """
  esc = escenario_vacio()
  descartados: list[dict] = []
  if not isinstance(raw, dict):
    return esc, descartados
  rev = raw.get("rev", 0)
  esc["rev"] = rev if isinstance(rev, int) and not isinstance(rev, bool) else 0
  esc["activo"] = raw.get("activo") is True
  lista = raw.get("obstaculos")
  if not isinstance(lista, list):
    return esc, descartados
  for i, item in enumerate(lista):
    if len(esc["obstaculos"]) >= MAX_OBSTACULOS:
      descartados.append({"i": i, "motivo": f"mas de {MAX_OBSTACULOS} obstaculos"})
      continue
    obst, motivo = normalizar_obstaculo(item)
    if obst is None:
      descartados.append({"i": i, "motivo": motivo})
    else:
      esc["obstaculos"].append(obst)
  return esc, descartados


# ---- cambios (los usa la UI): siempre devuelven un escenario NUEVO con rev+1 ----------

def _con_rev(esc: dict) -> dict:
  nuevo = copy.deepcopy(esc)
  nuevo["v"] = VERSION
  nuevo["rev"] = int(esc.get("rev", 0)) + 1
  return nuevo


def con_activo(esc: dict, activo: bool) -> dict:
  nuevo = _con_rev(esc)
  nuevo["activo"] = bool(activo)
  return nuevo


def con_obstaculo(esc: dict, obst: dict, indice: int | None = None) -> dict:
  """Anade (indice=None) o sustituye el obstaculo `indice`. Lanza ValueError si no es valido."""
  limpio, motivo = normalizar_obstaculo(obst)
  if limpio is None:
    raise ValueError(motivo)
  nuevo = _con_rev(esc)
  if indice is None:
    if len(nuevo["obstaculos"]) >= MAX_OBSTACULOS:
      raise ValueError(f"maximo {MAX_OBSTACULOS} obstaculos")
    nuevo["obstaculos"].append(limpio)
  else:
    nuevo["obstaculos"][indice] = limpio
  return nuevo


def sin_obstaculo(esc: dict, indice: int) -> dict:
  nuevo = _con_rev(esc)
  del nuevo["obstaculos"][indice]
  return nuevo


def con_preset(esc: dict, nombre: str) -> dict:
  """Sustituye la lista por un preset y activa el escenario."""
  nuevo = _con_rev(esc)
  nuevo["obstaculos"] = [normalizar_obstaculo(o)[0] for o in PRESETS[nombre]["obstaculos"]]
  nuevo["activo"] = True
  return nuevo


PRESETS = {
  "coche_parado": {
    "nombre": "Coche parado en mi carril",
    "obstaculos": [{"tipo": "coche", "s": 60.0, "carril": CARRIL_EGO}],
  },
  "slalom": {
    "nombre": "Slalom de conos",
    "obstaculos": [{"tipo": "cono", "s": 40.0 + 15.0 * k, "carril": CARRIL_EGO, "lateral": 1.0 if k % 2 else -1.0}
                   for k in range(5)],
  },
  "obra": {
    "nombre": "Obra (barrera + conos)",
    "obstaculos": [{"tipo": "cono", "s": 60.0 + 4.0 * k, "carril": CARRIL_EGO, "lateral": -1.5 + 0.5 * k} for k in range(4)]
                  + [{"tipo": "barrera", "s": 80.0, "carril": CARRIL_EGO}],   # con giro 0 ya corta el carril
  },
  "vacio": {
    "nombre": "Borrar todo",
    "obstaculos": [],
  },
}


# ---- textos -------------------------------------------------------------------------

def describir(obst: dict) -> str:
  """'Cono · 80 m · carril 1 · +0,0 m' (coma decimal, como el resto de la UI ORBIT)."""
  nombre = TIPOS.get(obst.get("tipo"), {}).get("nombre", str(obst.get("tipo")))
  carril = "mi carril" if obst["carril"] == CARRIL_EGO else f"carril {obst['carril']}"
  texto = f"{nombre} · {obst['s']:.0f} m · {carril} · {obst['lateral']:+.1f} m".replace(".", ",")
  if obst.get("giro"):
    texto += f" · {obst['giro']:.0f}°"
  return texto


def estado_conectado(estado, ahora_ms: int, max_edad_ms: int = ESTADO_MAX_EDAD_MS) -> bool:
  if not isinstance(estado, dict):
    return False
  ts = estado.get("ts_ms")
  if isinstance(ts, bool) or not isinstance(ts, int):
    return False
  return 0 <= ahora_ms - ts <= max_edad_ms
