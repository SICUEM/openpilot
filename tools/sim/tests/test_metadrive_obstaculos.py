import math

from openpilot.orbit import sim_obstaculos as so
from openpilot.tools.sim.bridge.metadrive import metadrive_obstaculos as mo


class FakeLane:
  """Straight lane along +x. MetaDrive convention: lateral points RIGHT (-y here)."""
  def __init__(self, x0, length, y=0.0, width=3.5):
    self.x0, self.length, self.y, self.width = x0, length, y, width

  def position(self, s, lateral):
    return (self.x0 + s, self.y - lateral)

  def heading_theta_at(self, s):
    return 0.0

  def width_at(self, s):
    return self.width

  def local_coordinates(self, pos):
    return pos[0] - self.x0, self.y - pos[1]


def straight_route(lengths, n_lanes=3, width=3.5):
  segs, x = [], 0.0
  for length in lengths:
    segs.append([FakeLane(x, length, y=-k * width, width=width) for k in range(n_lanes)])
    x += length
  return segs


def obst(**kw):
  return so.normalizar_obstaculo({"tipo": "cono", **kw})[0]


def test_lane_index_counts_from_the_right():
  assert mo.lane_index_for(3, 1, ego_index=0) == 2
  assert mo.lane_index_for(3, 3, ego_index=0) == 0
  assert mo.lane_index_for(3, 4, ego_index=0) is None
  assert mo.lane_index_for(2, so.CARRIL_EGO, ego_index=0) == 0
  assert mo.lane_index_for(2, so.CARRIL_EGO, ego_index=5) is None


def test_locate_walks_segments_from_ego_start():
  segs = straight_route([10, 40, 60])
  (lane, local), _ = mo.locate(segs, 5.0, obst(s=30, carril=so.CARRIL_EGO), ego_index=0)
  assert lane is segs[1][0] and math.isclose(local, 25.0)


def test_locate_past_route_and_missing_lane():
  segs = straight_route([10, 40])
  assert mo.locate(segs, 5.0, obst(s=100), ego_index=0) == (None, "fuera de la ruta")
  found, motivo = mo.locate(segs, 0.0, obst(s=20, carril=5), ego_index=0)
  assert found is None and "no existe" in motivo


def test_route_length_discounts_start():
  assert mo.route_length(straight_route([10, 40, 60]), 5.0, 0) == 105.0


def test_pose_flips_lateral_and_adds_giro():
  lane = FakeLane(0, 100)
  pos, heading = mo.obstacle_pose(lane, 20, obst(s=0, lateral=1.0, giro=90))
  assert pos == (20, 1.0)                     # +1 m to the LEFT = +y
  assert math.isclose(heading, math.pi / 2)


def test_pose_clamps_lateral_to_lane_width():
  pos, _ = mo.obstacle_pose(FakeLane(0, 100, width=3.0), 10, obst(s=0, lateral=-3.0))
  assert pos == (10, -3.0)


# ---- GestorObstaculos with a fake env ---------------------------------------------------

class FakeParams(dict):
  def get(self, key, *a, **kw):
    return dict.get(self, key)

  def put(self, key, value, *a, **kw):
    self[key] = value


class FakeObj:
  def __init__(self, i):
    self.id = f"obj{i}"


class FakeEngine:
  def __init__(self):
    self.spawned, self.cleared, self.n = [], [], 0

  def spawn_object(self, cls, **kw):
    self.n += 1
    self.spawned.append((cls.__name__, kw))
    return FakeObj(self.n)

  def clear_objects(self, ids):
    self.cleared.extend(ids)


class FakeEnv:
  def __init__(self, segs):
    graph = {}
    nodes = [f"n{i}" for i in range(len(segs) + 1)]
    for a, b, lanes in zip(nodes[:-1], nodes[1:], segs, strict=True):
      graph.setdefault(a, {})[b] = lanes
    self.current_map = type("M", (), {"road_network": type("R", (), {"graph": graph})()})()
    lane0 = segs[0][0]
    self.vehicle = type("V", (), {
      "navigation": type("N", (), {"checkpoints": nodes})(),
      "lane_index": (nodes[0], nodes[1], 0),
      "lane": lane0,
      "position": (5.0, 0.0),
    })()
    self.engine = FakeEngine()


def make(scenario, segs=None):
  params = FakeParams()
  if scenario is not None:
    params[so.PARAM_ESCENARIO] = scenario
  env = FakeEnv(segs or straight_route([10, 40, 200]))
  return mo.GestorObstaculos(env, "loop", params=params), env, params


def test_inactive_places_nothing_but_reports():
  g, env, params = make({"rev": 1, "activo": False, "obstaculos": [{"tipo": "cono", "s": 30}]})
  g.place()
  est = params[so.PARAM_ESTADO]
  assert env.engine.spawned == [] and est["colocados"] == 0 and est["activo"] is False
  assert est["mapa"] == "loop" and est["carriles"] == 3 and est["carril_ego"] == 3
  assert est["ruta_m"] == 245.0 and isinstance(est["ts_ms"], int)


def test_places_static_and_vehicle_and_reports_omitted():
  g, env, params = make({"rev": 2, "activo": True, "obstaculos": [
    {"tipo": "cono", "s": 30},
    {"tipo": "coche", "s": 60, "carril": 1},
    {"tipo": "barrera", "s": 999},
    {"tipo": "cono", "s": 2},
  ]})
  g.place()
  est = params[so.PARAM_ESTADO]
  names = [n for n, _ in env.engine.spawned]
  assert names == ["TrafficCone", "DefaultVehicle"]
  assert env.engine.spawned[0][1]["static"] is True
  assert env.engine.spawned[1][1]["vehicle_config"]["render_vehicle"] is True
  assert est["colocados"] == 2
  assert [o["i"] for o in est["omitidos"]] == [2, 3]
  assert "fuera de la ruta" in est["omitidos"][0]["motivo"] and "menos de" in est["omitidos"][1]["motivo"]


def test_missing_model_is_omitted_not_fatal():
  g, env, params = make({"rev": 1, "activo": True, "obstaculos": [{"tipo": "cono", "s": 30}, {"tipo": "triangulo", "s": 40}]})
  g.missing = {"traffic_cone"}
  g.place()
  assert [n for n, _ in env.engine.spawned] == ["TrafficWarning"]
  assert "traffic_cone" in params[so.PARAM_ESTADO]["omitidos"][0]["motivo"]


def test_tick_replaces_only_when_rev_or_activo_changes():
  g, env, params = make({"rev": 1, "activo": True, "obstaculos": [{"tipo": "cono", "s": 30}]})
  g.place()
  g.tick(mo.POLL_FRAMES)
  assert len(env.engine.spawned) == 1 and env.engine.cleared == []
  params[so.PARAM_ESCENARIO] = {"rev": 2, "activo": True, "obstaculos": [{"tipo": "cono", "s": 50}]}
  g.tick(mo.POLL_FRAMES * 2 + 1)              # not a poll frame: nothing yet
  assert len(env.engine.spawned) == 1
  g.tick(mo.POLL_FRAMES * 2)
  assert len(env.engine.spawned) == 2 and env.engine.cleared == ["obj1"]
  params[so.PARAM_ESCENARIO] = {"rev": 2, "activo": False, "obstaculos": []}
  g.tick(mo.POLL_FRAMES * 3)
  assert env.engine.cleared == ["obj1", "obj2"] and g.ids == []


def test_clear_before_reset_empties_ids():
  g, env, _ = make({"rev": 1, "activo": True, "obstaculos": [{"tipo": "cono", "s": 30}]})
  g.place()
  g.clear()
  g.clear()                                   # idempotent: second call clears nothing
  assert env.engine.cleared == ["obj1"] and g.ids == []


def test_no_param_is_inactive():
  g, env, params = make(None)
  g.place()
  assert env.engine.spawned == [] and params[so.PARAM_ESTADO]["activo"] is False
