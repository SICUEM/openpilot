"""Sondas del servidor ORBIT: Funnel (https + TCP a host:puerto) vs IP legacy."""
from openpilot.selfdrive.ui.widgets import orbit_server as os_


class _Resp:
  status = 200

  def __enter__(self):
    return self

  def __exit__(self, *a):
    return False


def _espiar(monkeypatch, cfg):
  llamadas = {"urls": [], "tcp": []}
  monkeypatch.setattr(os_, "_read_config", lambda: cfg)

  def urlopen(url, timeout=None, context=None):
    llamadas["urls"].append((url, context is not None))
    return _Resp()

  def tcp(ip, port, timeout=2.0):
    llamadas["tcp"].append((ip, port))
    return True

  monkeypatch.setattr(os_.urllib.request, "urlopen", urlopen)
  monkeypatch.setattr(os_, "probe_server", tcp)
  return llamadas


def test_sondear_funnel_https_y_tcp_8443(monkeypatch):
  ll = _espiar(monkeypatch, {"servidor": {"host": "h.ts.net", "puerto": 8443}})
  assert os_.sondear_funnel() == (True, True)
  assert ll["urls"] == [("https://h.ts.net/api/health", True)]
  assert ll["tcp"] == [("h.ts.net", 8443)]


def test_sondear_funnel_sin_host_no_hace_red(monkeypatch):
  ll = _espiar(monkeypatch, {"servidor": {"host": ""}})
  assert os_.sondear_funnel() == (False, False)
  assert not ll["urls"] and not ll["tcp"]


def _esperar_ip(m):
  for _ in range(200):
    if m.ip:
      return
    m._stop.wait(0.01)


def test_monitor_con_host_usa_funnel(monkeypatch):
  ll = _espiar(monkeypatch, {"servidor": {"host": "h.ts.net", "puerto": 8443}, "broker": "1.2.3.4"})
  m = os_.ServerMonitor(interval=0.01)
  try:
    _esperar_ip(m)
    assert m.ip == "h.ts.net"
  finally:
    m.stop()
  assert ll["urls"][0][0].startswith("https://h.ts.net")
  assert ("h.ts.net", 8443) in ll["tcp"]


def test_monitor_sin_host_es_legacy(monkeypatch):
  ll = _espiar(monkeypatch, {"servidor": {"host": ""}, "broker": "1.2.3.4", "broker_port": 1883, "backend_port": 8010})
  m = os_.ServerMonitor(interval=0.01)
  try:
    _esperar_ip(m)
    assert m.ip == "1.2.3.4"
  finally:
    m.stop()
  assert ll["urls"][0] == ("http://1.2.3.4:8010/api/health", False)
  assert ("1.2.3.4", 1883) in ll["tcp"]


def test_probar_servidor_usa_siempre_la_ip_dada(monkeypatch):
  ll = _espiar(monkeypatch, {"servidor": {"host": "h.ts.net"}, "backend_port": 8010})
  assert os_.probar_servidor("9.9.9.9", 1883) == (True, True)
  assert ll["urls"] == [("http://9.9.9.9:8010/api/health", False)]
  assert ll["tcp"] == [("9.9.9.9", 1883)]
