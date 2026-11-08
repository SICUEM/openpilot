from openpilot.orbit import sim_obstaculos as so
from openpilot.selfdrive.ui.widgets import orbit_sim as sim


class FakeParams(dict):
  def __init__(self, falla=False):
    super().__init__()
    self.falla = falla
    self.bloqueo = None

  def get(self, key, *a, **kw):
    return dict.get(self, key)

  def put(self, key, value, block=False):
    if self.falla:
      raise TypeError("boom")
    self.bloqueo = block
    self[key] = value


def test_obstaculo_nuevo_por_defecto_en_mi_carril():
  obst = sim.obstaculo_de(sim.valores_de(None))
  assert obst == {"tipo": "cono", "s": 60.0, "carril": so.CARRIL_EGO, "lateral": 0.0, "giro": 0.0}


def test_ida_y_vuelta_entre_obstaculo_y_controles():
  for obst in [
    {"tipo": "camion", "s": 120.0, "carril": 2, "lateral": -0.75, "giro": 90.0},
    {"tipo": "barrera", "s": 80.0, "carril": so.CARRIL_EGO, "lateral": 1.5, "giro": 45.0},
  ]:
    assert sim.obstaculo_de(sim.valores_de(obst)) == obst
    assert so.normalizar_obstaculo(sim.obstaculo_de(sim.valores_de(obst)))[1] == ""


def test_valores_recortan_lo_que_el_editor_no_puede_mostrar():
  v = sim.valores_de({"tipo": "cono", "s": 3.0, "carril": 6, "lateral": 2.9, "giro": -45.0})
  assert v["dist"] == sim.DIST_MIN and v["carril"] == sim.CARRILES_EDITOR
  assert v["lateral"] == sim.LATERAL_PASOS and v["giro"] == 3     # -45 = 135 sobre el carril


def test_etiquetas():
  assert sim.etiqueta_tipo(0) == "Cono"
  assert sim.etiqueta_carril(0) == "Mi carril" and sim.etiqueta_carril(1) == "1 (dcha)"
  assert sim.etiqueta_lateral(0) == "centro"
  assert sim.etiqueta_lateral(2) == "0,50 m izq" and sim.etiqueta_lateral(-3) == "0,75 m dcha"
  assert sim.etiqueta_giro(2) == "90°" and sim.etiqueta_distancia(60) == "60 m"


def test_guardar_bloquea_y_devuelve_fallos():
  p = FakeParams()
  esc = so.con_activo(so.escenario_vacio(), True)
  assert sim.guardar(p, esc) == [] and p.bloqueo is True
  assert sim.leer_escenario(p) == esc
  assert sim.guardar(FakeParams(falla=True), esc)[0].startswith(so.PARAM_ESCENARIO)


def test_leer_escenario_sin_param_o_basura():
  p = FakeParams()
  assert sim.leer_escenario(p) == so.escenario_vacio()
  p[so.PARAM_ESCENARIO] = "basura"
  assert sim.leer_escenario(p) == so.escenario_vacio()


ESC = {"v": 1, "rev": 3, "activo": True, "obstaculos": [
  {"tipo": "cono", "s": 30.0, "carril": "ego", "lateral": 0.0, "giro": 0.0},
  {"tipo": "coche", "s": 900.0, "carril": 1, "lateral": 0.0, "giro": 0.0},
]}
ESTADO = {"v": 1, "ts_ms": 10_000, "rev": 3, "activo": True, "mapa": "highway", "ruta_m": 307.2,
          "carriles": 3, "carril_ego": 3, "colocados": 1, "omitidos": [{"i": 1, "motivo": "fuera de la ruta"}],
          "descartados": [], "faltan_modelos": []}


def test_texto_estado_sin_sim():
  assert sim.texto_estado(None, ESC, 10_000).startswith("Simulación no conectada")
  assert sim.texto_estado(ESTADO, ESC, 10_000 + so.ESTADO_MAX_EDAD_MS + 1).startswith("Simulación no conectada")


def test_texto_estado_con_sim():
  t = sim.texto_estado(ESTADO, ESC, 11_000)
  assert "Mapa highway • ruta 307 m • 3 carriles (sales por el 3)" in t
  assert "1 colocados • 1 sin colocar" in t
  assert "Aplicando cambios" in sim.texto_estado(ESTADO, {**ESC, "rev": 4}, 11_000)
  assert "desactivados" in sim.texto_estado({**ESTADO, "activo": False}, ESC, 11_000)
  assert "traffic_cone" in sim.texto_estado({**ESTADO, "faltan_modelos": ["traffic_cone"]}, ESC, 11_000)


def test_motivo_omitido_solo_si_el_estado_es_de_este_escenario():
  assert sim.motivo_omitido(ESTADO, ESC, 1, 11_000) == "No colocado: fuera de la ruta"
  assert sim.motivo_omitido(ESTADO, ESC, 0, 11_000) == ""
  assert sim.motivo_omitido(ESTADO, {**ESC, "rev": 4}, 1, 11_000) == ""
  assert sim.motivo_omitido(None, ESC, 1, 11_000) == ""
