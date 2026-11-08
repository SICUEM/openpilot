import pytest

from openpilot.orbit import sim_obstaculos as so


def test_vacio_o_basura_da_escenario_inactivo():
  for raw in (None, "x", 3, [], {"obstaculos": "no"}):
    esc, desc = so.normalizar(raw)
    assert esc == so.escenario_vacio()
    assert desc == []


def test_normaliza_y_recorta():
  esc, desc = so.normalizar({"rev": 4, "activo": True, "obstaculos": [
    {"tipo": "cono", "s": -5, "carril": 2, "lateral": 9, "giro": 270},
  ]})
  assert esc["rev"] == 4 and esc["activo"] is True and desc == []
  assert esc["obstaculos"] == [{"tipo": "cono", "s": 0.0, "carril": 2, "lateral": so.LATERAL_MAX, "giro": -90.0}]


def test_carril_por_defecto_es_el_del_ego():
  esc, _ = so.normalizar({"activo": True, "obstaculos": [{"tipo": "coche", "s": 60}]})
  assert esc["obstaculos"][0]["carril"] == so.CARRIL_EGO


@pytest.mark.parametrize("obst, motivo", [
  ({"tipo": "peaton", "s": 10}, "tipo desconocido"),
  ({"tipo": "cono"}, "falta s"),
  ({"tipo": "cono", "s": True}, "falta s"),
  ({"tipo": "cono", "s": 10, "carril": 0}, "carril invalido"),
  ({"tipo": "cono", "s": 10, "carril": "izq"}, "carril invalido"),
  ({"tipo": "cono", "s": float("nan")}, "falta s"),
  ("cono", "no es un objeto"),
])
def test_descarta_con_motivo(obst, motivo):
  esc, desc = so.normalizar({"activo": True, "obstaculos": [{"tipo": "cono", "s": 5}, obst]})
  assert len(esc["obstaculos"]) == 1
  assert desc[0]["i"] == 1 and motivo in desc[0]["motivo"]


def test_activo_solo_con_true_literal():
  assert so.normalizar({"activo": 1})[0]["activo"] is False
  assert so.normalizar({"activo": "true"})[0]["activo"] is False


def test_limite_de_obstaculos():
  raw = {"activo": True, "obstaculos": [{"tipo": "cono", "s": i} for i in range(so.MAX_OBSTACULOS + 2)]}
  esc, desc = so.normalizar(raw)
  assert len(esc["obstaculos"]) == so.MAX_OBSTACULOS and len(desc) == 2


def test_cambios_suben_rev_y_no_mutan():
  base = so.escenario_vacio()
  a = so.con_obstaculo(base, {"tipo": "cono", "s": 30})
  b = so.con_obstaculo(a, {"tipo": "coche", "s": 50, "carril": 1}, indice=0)
  c = so.sin_obstaculo(b, 0)
  d = so.con_activo(c, True)
  assert [x["rev"] for x in (base, a, b, c, d)] == [0, 1, 2, 3, 4]
  assert base["obstaculos"] == [] and a["obstaculos"][0]["tipo"] == "cono"
  assert b["obstaculos"][0]["tipo"] == "coche" and c["obstaculos"] == [] and d["activo"] is True


def test_con_obstaculo_rechaza_invalido():
  with pytest.raises(ValueError):
    so.con_obstaculo(so.escenario_vacio(), {"tipo": "ovni", "s": 1})


def test_presets_validos_y_activan():
  for nombre in so.PRESETS:
    esc = so.con_preset(so.escenario_vacio(), nombre)
    assert esc["activo"] is True
    assert so.normalizar(esc)[1] == []
    assert all(o["carril"] == so.CARRIL_EGO for o in esc["obstaculos"])


def test_tipos_coherentes():
  for tipo in so.TIPOS.values():
    assert set(tipo) == {"nombre", "clase", "modelo", "vehiculo"}
  assert so.TIPOS["triangulo"]["modelo"] is None      # el unico que trae el MetaDrive minimal


def test_describir():
  assert so.describir({"tipo": "cono", "s": 80, "carril": 1, "lateral": 0.0, "giro": 0}) == "Cono • 80 m • carril 1 • +0,0 m"
  assert so.describir({"tipo": "coche", "s": 60, "carril": "ego", "lateral": -0.5, "giro": 90}) \
    == "Coche • 60 m • mi carril • -0,5 m • 90°"


def test_estado_conectado():
  assert so.estado_conectado({"ts_ms": 1000}, 5000)
  assert not so.estado_conectado({"ts_ms": 1000}, 1000 + so.ESTADO_MAX_EDAD_MS + 1)
  assert not so.estado_conectado({"ts_ms": 9000}, 5000)
  assert not so.estado_conectado(None, 5000)
  assert not so.estado_conectado({"ts_ms": True}, 5000)
