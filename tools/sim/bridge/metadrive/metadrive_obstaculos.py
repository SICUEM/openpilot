import math
import time

from openpilot.orbit import sim_obstaculos as so
from openpilot.tools.sim.bridge.metadrive.metadrive_assets import missing_models

POLL_FRAMES = 100          # re-read the scenario Param once a second at the 100 Hz loop rate
HEARTBEAT_S = 3.0          # the UI treats an estado older than so.ESTADO_MAX_EDAD_MS as "no sim"
MIN_DIST_EGO = 8.0         # never drop an obstacle on top of the car


# ---- route geometry (pure: works on anything with .length/.position/.heading_theta_at) ----
# MetaDrive orders lanes left to right (index 0 = leftmost) and its lateral axis points RIGHT.
# The scenario counts lanes from the right and its lateral points LEFT (orbit/sim_obstaculos.py).

def route_segments(road_network, checkpoints):
  return [road_network.graph[a][b] for a, b in zip(checkpoints[:-1], checkpoints[1:], strict=False)]


def lane_index_for(n_lanes, carril, ego_index):
  idx = ego_index if carril == so.CARRIL_EGO else n_lanes - carril
  return idx if 0 <= idx < n_lanes else None


def locate(segments, s0, obst, ego_index):
  """(lane, local_s) where the obstacle falls, walking `s` metres from s0 on the first segment.

  Each segment is measured on the obstacle's own lane (inner and outer lanes of a curve differ).
  Returns (None, reason) when it falls past the route or on a lane that segment does not have.
  """
  remaining = s0 + obst["s"]
  for lanes in segments:
    idx = lane_index_for(len(lanes), obst["carril"], ego_index)
    lane = lanes[idx] if idx is not None else None
    length = (lane or lanes[0]).length
    if remaining <= length:
      if lane is None:
        return None, f"el carril {obst['carril']} no existe en ese tramo ({len(lanes)} carriles)"
      return (lane, remaining), ""
    remaining -= length
  return None, "fuera de la ruta"


def route_length(segments, s0, ego_index):
  total = 0.0
  for lanes in segments:
    idx = lane_index_for(len(lanes), so.CARRIL_EGO, ego_index)
    total += (lanes[idx] if idx is not None else lanes[0]).length
  return max(total - s0, 0.0)


def obstacle_pose(lane, local_s, obst):
  limit = lane.width_at(local_s) if hasattr(lane, "width_at") else so.LATERAL_MAX
  md_lateral = -min(max(obst["lateral"], -limit), limit)
  position = lane.position(local_s, md_lateral)
  heading = lane.heading_theta_at(local_s) + math.radians(obst["giro"])
  return position, heading


def _metadrive_class(name):
  from metadrive.component.static_object import traffic_object
  from metadrive.component.vehicle import vehicle_type
  return getattr(traffic_object, name, None) or getattr(vehicle_type, name)


class GestorObstaculos:
  """Places the static obstacles of OrbitSimObstaculos along the ego's route.

  Lives in the metadrive process. Objects spawned with engine.spawn_object are not owned by
  any manager and env.reset() asserts none remain, so the process must call clear() BEFORE
  every reset and place() after it (same rule as ModMenu).
  """

  def __init__(self, env, map_name, params=None):
    if params is None:
      from openpilot.common.params import Params
      params = Params()
    self.env = env
    self.params = params
    self.map_name = map_name
    self.ids = []
    self.applied = None          # (rev, activo) of the scenario currently in the world
    self.estado = {}
    self.last_heartbeat = 0.0
    self.missing = set(missing_models([t["modelo"] for t in so.TIPOS.values() if t["modelo"]]))

  def read(self):
    try:
      raw = self.params.get(so.PARAM_ESCENARIO)
    except Exception:
      raw = None
    return so.normalizar(raw)

  # ---- lifecycle -----------------------------------------------------------------------
  def clear(self):
    if self.ids:
      self.env.engine.clear_objects(list(self.ids))
    self.ids = []

  def place(self):
    """(Re)build the world from the current Param. Call right after env.reset()."""
    self.clear()
    esc, descartados = self.read()
    self.applied = (esc["rev"], esc["activo"])
    self.estado = self._place(esc, descartados)
    self.write_estado()

  def tick(self, frame):
    if frame % POLL_FRAMES == 0:
      esc, _ = self.read()
      if (esc["rev"], esc["activo"]) != self.applied:
        self.place()
        return
    if time.monotonic() - self.last_heartbeat >= HEARTBEAT_S:
      self.write_estado()

  def write_estado(self):
    self.estado["ts_ms"] = time.time_ns() // 1_000_000
    self.last_heartbeat = time.monotonic()
    try:
      self.params.put(so.PARAM_ESTADO, self.estado)
    except Exception:
      pass

  # ---- placement -----------------------------------------------------------------------
  def _place(self, esc, descartados):
    ego = self.env.vehicle
    segments = route_segments(self.env.current_map.road_network, ego.navigation.checkpoints)
    ego_index = ego.lane_index[2]
    s0 = ego.lane.local_coordinates(ego.position)[0]
    n_start = len(segments[0]) if segments else 0
    estado = {
      "v": so.VERSION,
      "rev": esc["rev"],
      "activo": esc["activo"],
      "mapa": self.map_name,
      "ruta_m": round(route_length(segments, s0, ego_index), 1),
      "carriles": n_start,
      "carril_ego": n_start - ego_index,     # counted from the right, like the scenario
      "colocados": 0,
      "omitidos": [],
      "descartados": descartados,
      "faltan_modelos": sorted(self.missing),
    }
    if not esc["activo"]:
      return estado

    for i, obst in enumerate(esc["obstaculos"]):
      motivo = self._spawn(obst, segments, s0, ego_index, ego)
      if motivo:
        estado["omitidos"].append({"i": i, "motivo": motivo})
      else:
        estado["colocados"] += 1
    return estado

  def _spawn(self, obst, segments, s0, ego_index, ego):
    tipo = so.TIPOS[obst["tipo"]]
    if tipo["modelo"] in self.missing:
      return f"falta el modelo 3D {tipo['modelo']}"
    found, motivo = locate(segments, s0, obst, ego_index)
    if found is None:
      return motivo
    position, heading = obstacle_pose(*found, obst)
    if math.dist(position[:2], ego.position[:2]) < MIN_DIST_EGO:
      return f"a menos de {MIN_DIST_EGO:.0f} m del coche"
    try:
      cls = _metadrive_class(tipo["clase"])
      if tipo["vehiculo"]:
        obj = self.env.engine.spawn_object(cls, vehicle_config=dict(
          spawn_position_heading=(position, heading), spawn_velocity=None, render_vehicle=True))
      else:
        obj = self.env.engine.spawn_object(cls, lane=found[0], position=position, heading_theta=heading, static=True)
    except Exception as e:
      return f"error al crearlo: {e}"
    self.ids.append(obj.id)
    return ""
