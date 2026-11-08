"""Logica del subpanel SIMULACION del panel ORBIT (obstaculos de la sim MetaDrive del PC).

Aqui no se pinta nada (no se importa pyray): textos, conversion entre un obstaculo y los
valores enteros de los controles +/- del editor, y lectura/escritura de los Params. Asi
se prueba con un Params falso, como orbit_ajustes.

El formato del escenario es de orbit/sim_obstaculos.py; este modulo solo lo presenta.
La seccion se ve SIEMPRE (decision del usuario, sin SIMULATION=1): en un comma real solo
escribe un Param que nadie lee y dice "Simulacion no conectada".
"""
from openpilot.orbit import sim_obstaculos as so

# ---- controles del editor (enteros, que es lo que manejan los +/-) ---------------------
DIST_MIN, DIST_MAX, DIST_PASO = 10, 1500, 10
DIST_DEFECTO = 60
CARRILES_EDITOR = 4                 # 0 = mi carril, 1..4 = contando desde la derecha
LATERAL_PASO = 0.25                 # metros por toque
LATERAL_PASOS = int(so.LATERAL_MAX / LATERAL_PASO)
GIRO_PASO = 45
GIRO_PASOS = 3                      # 0, 45, 90, 135 grados


def etiqueta_tipo(v: int) -> str:
  return so.TIPOS[so.ORDEN_TIPOS[v]]["nombre"]


def etiqueta_distancia(v: int) -> str:
  return f"{v} m"


def etiqueta_carril(v: int) -> str:
  if v == 0:
    return "Mi carril"
  return "1 (dcha)" if v == 1 else str(v)


def etiqueta_lateral(v: int) -> str:
  m = v * LATERAL_PASO
  if v == 0:
    return "centro"
  return f"{abs(m):.2f} m {'izq' if m > 0 else 'dcha'}".replace(".", ",")


def etiqueta_giro(v: int) -> str:
  return f"{v * GIRO_PASO}°"


def valores_de(obst: dict | None) -> dict:
  """Obstaculo -> enteros de los controles. None = valores de un obstaculo nuevo."""
  if obst is None:
    return {"tipo": 0, "dist": DIST_DEFECTO, "carril": 0, "lateral": 0, "giro": 0}
  dist = int(round(obst["s"] / DIST_PASO) * DIST_PASO)
  carril = 0 if obst["carril"] == so.CARRIL_EGO else min(int(obst["carril"]), CARRILES_EDITOR)
  return {
    "tipo": so.ORDEN_TIPOS.index(obst["tipo"]),
    "dist": min(max(dist, DIST_MIN), DIST_MAX),
    "carril": carril,
    "lateral": max(-LATERAL_PASOS, min(LATERAL_PASOS, int(round(obst["lateral"] / LATERAL_PASO)))),
    "giro": max(0, min(GIRO_PASOS, int(round((obst["giro"] % 180) / GIRO_PASO)))),
  }


def obstaculo_de(valores: dict) -> dict:
  return {
    "tipo": so.ORDEN_TIPOS[valores["tipo"]],
    "s": float(valores["dist"]),
    "carril": so.CARRIL_EGO if valores["carril"] == 0 else int(valores["carril"]),
    "lateral": valores["lateral"] * LATERAL_PASO,
    "giro": float(valores["giro"] * GIRO_PASO),
  }


# ---- Params -----------------------------------------------------------------------------

def leer_escenario(params) -> dict:
  try:
    raw = params.get(so.PARAM_ESCENARIO)
  except Exception:
    raw = None
  return so.normalizar(raw)[0]


def leer_estado(params):
  try:
    return params.get(so.PARAM_ESTADO)
  except Exception:
    return None


def guardar(params, esc: dict) -> list[str]:
  """block=True: el put por defecto de este arbol NO bloquea y el siguiente refresco
  leeria el escenario viejo (la fila volveria atras un instante)."""
  try:
    params.put(so.PARAM_ESCENARIO, esc, True)
  except Exception as e:
    return [f"{so.PARAM_ESCENARIO}: {e}"]
  return []


# ---- textos -----------------------------------------------------------------------------

def texto_estado(estado, esc: dict, ahora_ms: int) -> str:
  if not so.estado_conectado(estado, ahora_ms):
    return ("Simulación no conectada. Lo que configures aquí se aplica al arrancar la " +
            "simulación MetaDrive del PC y al reiniciar el mapa.")
  partes = [f"Mapa {estado.get('mapa', '?')} • ruta {estado.get('ruta_m', 0):.0f} m • " +
            f"{estado.get('carriles', '?')} carriles (sales por el {estado.get('carril_ego', '?')})"]
  if estado.get("rev") != esc["rev"]:
    partes.append("Aplicando cambios...")
  elif not estado.get("activo"):
    partes.append("Obstáculos desactivados.")
  else:
    n_omit = len(estado.get("omitidos", []))
    linea = f"{estado.get('colocados', 0)} colocados"
    if n_omit:
      linea += f" • {n_omit} sin colocar (mira su fila)"
    partes.append(linea)
  if estado.get("faltan_modelos"):
    partes.append("Faltan modelos 3D: " + ", ".join(estado["faltan_modelos"]))
  # La descripcion de un ListItem es HTML: un "\n" se pierde y las lineas salen pegadas.
  return "<br>".join(partes)


def motivo_omitido(estado, esc: dict, indice: int, ahora_ms: int) -> str:
  """Por que la sim no coloco el obstaculo `indice` ("" si se coloco o no se sabe)."""
  if not so.estado_conectado(estado, ahora_ms) or estado.get("rev") != esc["rev"] or not estado.get("activo"):
    return ""
  for o in estado.get("omitidos", []):
    if o.get("i") == indice:
      return f"No colocado: {o.get('motivo', '?')}"
  return ""
