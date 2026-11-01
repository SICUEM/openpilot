"""Modelos del equipo en chestnut (orbit/modelos): contrato, .pkl, marcador LISTO, preparacion y
eleccion del modelo en modeld. Sin GPU ni compilaciones: metadata sintetica y ficheros falsos.

    Contrato ...................... mismo formato que el de serie; el estado oculto puede crecer
                                   si features_buffer casa con el hidden_state de su vision.
    .pkl sin ejecutar ............. se lee la metadata de un .pkl SIN ejecutar su contenido, y el
                                   dispositivo sale de las cadenas del pickle, no de bytes sueltos
                                   (un .pkl de CUDA "contiene" b"AMD" en los pesos).
    LISTO ......................... el marcador deja de valer si cambia el .pkl o el tinygrad.
    Preparar ...................... un .pkl entregado valido se acepta sin compilar; un fallo no
                                   se repite con las mismas entradas; sin chestnut no se compila.
    Eleccion ...................... pedido -> grande de serie -> pequeno de serie, con motivo.
    Dispositivo ................... comma four / 3X / PC: camara, destino y avisos de cada uno.
    Cambio en marcha .............. se aplica parado y desacoplado; sin chestnut, al momento.
    Registro ...................... Params registrados y el gestor solo offroad.
"""
import json
import os
import pickle

import pytest

from openpilot.common.basedir import BASEDIR
from openpilot.orbit.modelos import cambio
from openpilot.orbit.modelos import chestnut as cn
from openpilot.orbit.modelos import compilar
from openpilot.orbit.modelos import paquete as pq
from openpilot.orbit.modelos import seleccion as sel

CAM_MICI = (1344, 760)
CAM_TIZI = (1928, 1208)


def vision_meta(hidden=512, salidas=("meta", "plan_x", "hidden_state"), img=(1, 12, 128, 256)):
  slices = {k: slice(i * 10, i * 10 + 10) for i, k in enumerate(salidas) if k != "hidden_state"}
  if "hidden_state" in salidas:
    slices["hidden_state"] = slice(1000, 1000 + hidden)
  slices["pad"] = slice(0, None)
  return {"input_shapes": {"img": img, "big_img": img}, "output_slices": slices,
          "output_shapes": {"outputs": (1, 1000 + hidden)}}


def politica_meta(fb=(1, 25, 512), extra=None):
  formas = {"features_buffer": fb, "desire_pulse": (1, 25, 8), "traffic_convention": (1, 2), **(extra or {})}
  return {"input_shapes": formas, "output_slices": {"plan": slice(0, 990), "desire_state": slice(990, 998)},
          "output_shapes": {"outputs": (1, 1000)}}


REF = {"vision": vision_meta(), "on_policy": politica_meta()}


@pytest.fixture(autouse=True)
def entorno(monkeypatch, tmp_path):
  monkeypatch.setattr(pq, "contrato_referencia", lambda: REF)
  monkeypatch.setattr(pq, "tinygrad_ref", lambda: "tg-1")
  monkeypatch.setenv("ORBIT_MODELS_DIR", str(tmp_path / "orbit_models"))


class Malicioso:
  """Si se ejecutara al leer el .pkl, crearia el fichero."""
  def __init__(self, ruta):
    self.ruta = ruta

  def __reduce__(self):
    return (os.system, (f"touch {self.ruta}",))


class FalsoJit:
  """Un objeto cualquiera de una clase propia, como los TinyJit del .pkl real."""


def escribir_pkl(ruta, camaras=(CAM_MICI,), dispositivo="USB+AMD:LLVM", vision=None, politica=None, run_policy=True, trampa=None):
  obj = {"metadata": {"vision": vision or vision_meta(), "on_policy": politica or politica_meta()}}
  if run_policy:
    obj["run_policy"] = Malicioso(trampa) if trampa else FalsoJit()
  for c in camaras:
    obj[c] = {"device": dispositivo}
  ruta.parent.mkdir(parents=True, exist_ok=True)
  ruta.write_bytes(pickle.dumps(obj))
  return ruta


def paquete_con_pkl(base, modelo_id="m1", **kw):
  escribir_pkl(base / modelo_id / pq.PKL_ENTREGADO, **kw)
  return pq.inspeccionar(base / modelo_id)


# ------------------------------------------------------------------ contrato

def test_contrato_igual_que_serie_vale():
  assert pq.comparar_contrato(vision_meta(), politica_meta()) == ([], [])


def test_contrato_estado_oculto_mayor_se_admite_con_aviso():
  errores, avisos = pq.comparar_contrato(vision_meta(hidden=1024), politica_meta(fb=(1, 25, 1024)))
  assert errores == []
  assert any("hidden_state de 1024" in a for a in avisos)


def test_contrato_features_buffer_que_no_casa_con_su_vision():
  errores, _ = pq.comparar_contrato(vision_meta(hidden=1024), politica_meta(fb=(1, 25, 512)))
  assert any("features_buffer" in e for e in errores)


@pytest.mark.parametrize("vision,politica,trozo", [
  (vision_meta(salidas=("meta", "hidden_state")), politica_meta(), "faltan salidas ['plan_x']"),
  (vision_meta(img=(1, 12, 64, 128)), politica_meta(), "img con forma"),
  (vision_meta(), politica_meta(extra={"otra": (1, 4)}), "on_policy: entradas"),
  (vision_meta(), politica_meta(extra={"action_t": (1, 3)}), "action_t con forma"),
])
def test_contrato_rechaza(vision, politica, trozo):
  errores, _ = pq.comparar_contrato(vision, politica)
  assert any(trozo in e for e in errores), errores


def test_contrato_action_t_opcional_con_la_forma_buena():
  assert pq.comparar_contrato(vision_meta(), politica_meta(extra={"action_t": (1, 2)}))[0] == []


# ------------------------------------------------------------------ .pkl

def test_leer_pkl_no_ejecuta_su_contenido(tmp_path):
  trampa = tmp_path / "ejecutado"
  info = pq.leer_pkl(escribir_pkl(tmp_path / "m.pkl", camaras=(CAM_MICI, CAM_TIZI), trampa=trampa))
  assert not trampa.exists()
  assert info["camaras"] == [CAM_MICI, CAM_TIZI]
  assert info["run_policy"] and info["amd"]
  assert info["metadata"]["vision"]["output_slices"]["hidden_state"] == slice(1000, 1512)


def test_dispositivo_sale_de_las_cadenas_no_de_bytes_sueltos(tmp_path):
  ruta = escribir_pkl(tmp_path / "m.pkl", dispositivo="CUDA")
  ruta.write_bytes(ruta.read_bytes() + b"\x13AMD\x19B pesos al azar")
  info = pq.leer_pkl(ruta)
  assert info["dispositivos"] == ["CUDA"]
  assert not info["amd"]


def test_leer_pkl_que_no_es_de_compile_modeld(tmp_path):
  ruta = tmp_path / "m.pkl"
  ruta.write_bytes(pickle.dumps({"otra": 1}))
  with pytest.raises(ValueError):
    pq.leer_pkl(ruta)


# ------------------------------------------------------------------ marcador LISTO

def test_marcador_caduca_si_cambia_el_pkl_o_el_tinygrad(tmp_path, monkeypatch):
  paq = paquete_con_pkl(tmp_path)
  pq.escribir_marcador(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI, paq.pkl_entregado, "entregado")
  assert pq.pkl_listo(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI) == paq.pkl_entregado.resolve()
  assert pq.pkl_listo(paq.ruta, pq.DESTINO_USBGPU, CAM_TIZI) is None  # otra camara
  assert pq.pkl_listo(paq.ruta, pq.DESTINO_LOCAL, CAM_MICI) is None   # otro destino

  monkeypatch.setattr(pq, "tinygrad_ref", lambda: "tg-2")
  assert pq.pkl_listo(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI) is None
  monkeypatch.setattr(pq, "tinygrad_ref", lambda: "tg-1")

  paq.pkl_entregado.write_bytes(paq.pkl_entregado.read_bytes() + b"x")
  assert pq.pkl_listo(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI) is None


def test_marcador_no_sale_de_la_carpeta_del_modelo(tmp_path):
  paq = paquete_con_pkl(tmp_path)
  fuera = escribir_pkl(tmp_path / "fuera.pkl")
  pq.escribir_marcador(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI, fuera, "entregado")
  assert pq.pkl_listo(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI) is None


# ------------------------------------------------------------------ preparar

def test_pkl_entregado_valido_se_acepta_sin_compilar(tmp_path, monkeypatch):
  monkeypatch.setattr(compilar, "compilar_onnx", lambda *a: pytest.fail("no debia compilar"))
  paq = paquete_con_pkl(tmp_path)
  r = compilar.preparar(paq, pq.DESTINO_USBGPU, CAM_MICI, gpu_disponible=False)
  assert (r.estado, r.origen) == (compilar.LISTO, "entregado")
  assert compilar.preparar(paq, pq.DESTINO_USBGPU, CAM_MICI, gpu_disponible=False).estado == compilar.LISTO


@pytest.mark.parametrize("kw,trozo", [
  ({"camaras": (CAM_TIZI,)}, "camara 1344x760"),
  ({"dispositivo": "CUDA"}, "GPU AMD"),
  ({"run_policy": False}, "run_policy"),
  ({"politica": politica_meta(fb=(1, 25, 256))}, "features_buffer"),
])
def test_pkl_entregado_invalido_sin_onnx_es_error_y_no_se_repite(tmp_path, monkeypatch, kw, trozo):
  paq = paquete_con_pkl(tmp_path, **kw)
  r = compilar.preparar(paq, pq.DESTINO_USBGPU, CAM_MICI, gpu_disponible=True)
  assert r.estado == compilar.ERROR and trozo in r.detalle
  monkeypatch.setattr(compilar, "validar_pkl_entregado", lambda *a: pytest.fail("no debia revalidar"))
  assert compilar.preparar(paq, pq.DESTINO_USBGPU, CAM_MICI, gpu_disponible=True).estado == compilar.ERROR


def test_fallo_se_reintenta_si_cambian_las_entradas(tmp_path):
  paq = paquete_con_pkl(tmp_path, dispositivo="CUDA")
  assert compilar.preparar(paq, pq.DESTINO_USBGPU, CAM_MICI, True).estado == compilar.ERROR
  escribir_pkl(paq.pkl_entregado)  # el companero entrega uno bueno
  assert compilar.preparar(pq.inspeccionar(paq.ruta), pq.DESTINO_USBGPU, CAM_MICI, True).estado == compilar.LISTO


def paquete_con_onnx(base, modelo_id="m2"):
  d = base / modelo_id
  d.mkdir(parents=True)
  (d / pq.VISION_ONNX).write_bytes(b"v")
  (d / pq.POLICY_ONNX).write_bytes(b"p")
  return pq.inspeccionar(d)


def test_onnx_sin_chestnut_queda_pendiente(tmp_path, monkeypatch):
  monkeypatch.setattr(compilar, "validar_onnx", lambda paq: [])
  monkeypatch.setattr(compilar, "compilar_onnx", lambda *a: pytest.fail("no debia compilar"))
  r = compilar.preparar(paquete_con_onnx(tmp_path), pq.DESTINO_USBGPU, CAM_MICI, gpu_disponible=False)
  assert r.estado == compilar.PENDIENTE_CHESTNUT


def test_onnx_con_chestnut_se_compila_y_queda_listo(tmp_path, monkeypatch):
  monkeypatch.setattr(compilar, "validar_onnx", lambda paq: [])

  def compilar_falso(paq, destino, cam):
    return escribir_pkl(pq.ruta_pkl_compilado(paq.ruta, destino, cam))
  monkeypatch.setattr(compilar, "compilar_onnx", compilar_falso)
  avisado = []
  paq = paquete_con_onnx(tmp_path)
  r = compilar.preparar(paq, pq.DESTINO_USBGPU, CAM_MICI, gpu_disponible=True, al_compilar=lambda: avisado.append(1))
  assert (r.estado, r.origen, avisado) == (compilar.LISTO, "compilado", [1])
  assert pq.pkl_listo(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI) == pq.ruta_pkl_compilado(paq.ruta, pq.DESTINO_USBGPU, CAM_MICI).resolve()


def test_carpeta_sin_modelo(tmp_path):
  (tmp_path / "vacio").mkdir()
  assert compilar.preparar(pq.inspeccionar(tmp_path / "vacio"), pq.DESTINO_USBGPU, CAM_MICI, True).estado == compilar.SIN_MODELO


def test_flags_de_chestnut_son_los_del_sconscript(monkeypatch):
  monkeypatch.setattr(compilar, "get_tg_input_devices", lambda proc, usbgpu: {"WARP_DEV": "QCOM", "QUEUE_DEV": "AMD"})
  flags = compilar.flags_tinygrad(pq.DESTINO_USBGPU)
  assert flags["DEV"] == "USB+AMD:LLVM" and flags["WARP_DEV"] == "QCOM" and flags["FLOAT16"] == "1"


# ------------------------------------------------------------------ eleccion en modeld

def listo(base, modelo_id, destino, cam):
  paq = paquete_con_pkl(base, modelo_id, camaras=(cam,))
  pq.escribir_marcador(paq.ruta, destino, cam, paq.pkl_entregado, "entregado")
  return paq


def test_eleccion_modelo_pedido_en_chestnut(tmp_path):
  listo(tmp_path, "m1", pq.DESTINO_USBGPU, CAM_MICI)
  lista, motivos = sel.candidatos("m1", True, True, CAM_MICI, base=tmp_path, local=False)
  assert [c.origen for c in lista] == [sel.EQUIPO, sel.SERIE_GRANDE, sel.SERIE]
  assert lista[0].usbgpu and lista[0].modelo_id == "m1" and motivos == []
  assert not lista[-1].usbgpu


@pytest.mark.parametrize("deseado,chestnut,trozo", [
  ("m1", False, "chestnut no esta conectado"),
  ("otro", True, "no esta en el coche"),
  ("../etc", True, "id de modelo no valido"),
])
def test_eleccion_cae_al_de_serie_con_motivo(tmp_path, deseado, chestnut, trozo):
  listo(tmp_path, "m1", pq.DESTINO_USBGPU, CAM_MICI)
  lista, motivos = sel.candidatos(deseado, chestnut, False, CAM_MICI, base=tmp_path, local=False)
  assert [c.origen for c in lista] == [sel.SERIE]
  assert any(trozo in m for m in motivos), motivos


def test_eleccion_no_listo_para_esta_camara(tmp_path):
  listo(tmp_path, "m1", pq.DESTINO_USBGPU, CAM_TIZI)
  lista, motivos = sel.candidatos("m1", True, False, CAM_MICI, base=tmp_path, local=False)
  assert lista[0].origen == sel.SERIE and "no esta listo" in motivos[0]


def test_eleccion_en_pc_usa_el_destino_local(tmp_path):
  listo(tmp_path, "m1", pq.DESTINO_LOCAL, CAM_TIZI)
  lista, _ = sel.candidatos("m1", False, False, CAM_TIZI, base=tmp_path, local=True)
  assert lista[0].origen == sel.EQUIPO and not lista[0].usbgpu


def test_sin_pedir_nada_y_chestnut_conectado_va_el_grande_de_serie(tmp_path):
  lista, motivos = sel.candidatos(None, True, True, CAM_MICI, base=tmp_path, local=False)
  assert [c.origen for c in lista] == [sel.SERIE_GRANDE, sel.SERIE] and motivos == []


class ParamsFalsos:
  def __init__(self, valores=None):
    self.valores = dict(valores or {})

  def get(self, k):
    return self.valores.get(k)

  def put(self, k, v):
    self.valores[k] = v


@pytest.mark.parametrize("valor,esperado", [(None, None), ("", None), ("serie", None), (" m1 ", "m1"), (b"m1", "m1")])
def test_leer_deseado(valor, esperado):
  assert sel.leer_deseado(ParamsFalsos({sel.PARAM_DESEADO: valor})) == esperado


def test_estado_activo_publicado(tmp_path):
  params = ParamsFalsos()
  c = sel.Candidato(sel.SERIE, tmp_path / "x.pkl", pq.DESTINO_LOCAL)
  sel.publicar_activo(params, sel.estado_activo(c, "m1", False, ["chestnut no esta conectado"]))
  estado = json.loads(params.valores[sel.PARAM_ACTIVO])
  assert estado["origen"] == "serie" and estado["deseado"] == "m1" and "chestnut" in estado["motivo"]


# ------------------------------------------------------------------ dispositivo

def test_perfil_de_cada_dispositivo():
  four, tres_x, pc = cn.PERFILES["mici"], cn.PERFILES["tizi"], cn.PERFILES["pc"]
  assert (four.camara, four.destino, four.oficial) == (CAM_MICI, pq.DESTINO_USBGPU, True)
  assert (tres_x.camara, tres_x.destino, tres_x.oficial) == (CAM_TIZI, pq.DESTINO_USBGPU, False)
  assert any("GPS" in a for a in tres_x.avisos)
  assert pc.destino == pq.DESTINO_GPU_PC


def test_aviso_usb_lento_solo_si_esta_conectado():
  four = cn.PERFILES["mici"]
  assert cn.avisos(four, True, 10000) == []
  assert "lento" in cn.avisos(four, True, 480)[0]
  assert cn.avisos(four, False, None) == []


def test_chestnut_simulado_en_pc(tmp_path, monkeypatch):
  monkeypatch.setattr(cn, "PC", True)
  monkeypatch.setattr(cn, "archivo_simulado", lambda: tmp_path / "orbit_chestnut_sim")
  assert not cn.presente()
  (tmp_path / "orbit_chestnut_sim").touch()
  assert cn.presente()


def test_gpu_pc_va_en_cuda_con_el_warp_en_cpu():
  assert compilar.dispositivos_entrada(pq.DESTINO_GPU_PC) == {"WARP_DEV": "CPU", "QUEUE_DEV": "CUDA"}
  flags = compilar.flags_tinygrad(pq.DESTINO_GPU_PC)
  assert flags["DEV"] == "CUDA" and flags["WARP_DEV"] == "CPU"


def test_pkl_entregado_para_gpu_pc_tiene_que_ser_cuda(tmp_path):
  amd = paquete_con_pkl(tmp_path, "amd", camaras=(CAM_TIZI,))
  assert any("CUDA" in e for e in compilar.validar_pkl_entregado(amd, pq.DESTINO_GPU_PC, CAM_TIZI))
  cuda = paquete_con_pkl(tmp_path, "cuda", camaras=(CAM_TIZI,), dispositivo="CUDA")
  assert compilar.validar_pkl_entregado(cuda, pq.DESTINO_GPU_PC, CAM_TIZI) == []


def test_eleccion_con_chestnut_simulado(tmp_path):
  listo(tmp_path, "m1", pq.DESTINO_GPU_PC, CAM_TIZI)
  lista, motivos = sel.candidatos("m1", True, True, CAM_TIZI, pq.DESTINO_GPU_PC, base=tmp_path, local=True)
  # el grande de serie es para la AMD: con el chestnut simulado no se ofrece
  assert [(c.origen, c.destino) for c in lista] == [(sel.EQUIPO, pq.DESTINO_GPU_PC), (sel.SERIE, pq.DESTINO_LOCAL)]
  assert lista[0].en_chestnut and not lista[0].usbgpu and motivos == []


def test_eleccion_sin_chestnut_en_pc_usa_local_si_esta(tmp_path):
  listo(tmp_path, "m1", pq.DESTINO_GPU_PC, CAM_TIZI)
  lista, motivos = sel.candidatos("m1", False, False, CAM_TIZI, pq.DESTINO_GPU_PC, base=tmp_path, local=True)
  assert lista[0].origen == sel.SERIE and "chestnut no esta conectado" in motivos
  pq.escribir_marcador(tmp_path / "m1", pq.DESTINO_LOCAL, CAM_TIZI, tmp_path / "m1" / pq.PKL_ENTREGADO, "entregado")
  lista, _ = sel.candidatos("m1", False, False, CAM_TIZI, pq.DESTINO_GPU_PC, base=tmp_path, local=True)
  assert (lista[0].origen, lista[0].destino) == (sel.EQUIPO, pq.DESTINO_LOCAL)


# ------------------------------------------------------------------ cambio en marcha

SERIE_C = sel.Candidato(sel.SERIE, "serie.pkl", pq.DESTINO_LOCAL)
M1 = sel.Candidato(sel.EQUIPO, "m1.pkl", pq.DESTINO_USBGPU, "m1")
M2 = sel.Candidato(sel.EQUIPO, "m2.pkl", pq.DESTINO_USBGPU, "m2")


class Escena:
  """Un Vigilante con reloj, entrada y eleccion de mentira."""
  def __init__(self, activo, deseado, chestnut=True):
    self.t = 0.0
    self.entrada = cambio.Entrada(deseado, chestnut)
    self.params = ParamsFalsos()
    self.v = cambio.Vigilante(self.params, activo, self.entrada, {"origen": activo.origen},
                              lambda: self.entrada, self.objetivo, lambda: self.t)

  @staticmethod
  def objetivo(e):
    if not e.chestnut or e.deseado is None:
      return SERIE_C
    return {"m1": M1, "m2": M2}.get(e.deseado, SERIE_C)

  def paso(self, parado=False, acoplado=True, **cambios):
    if cambios:
      self.entrada = cambio.Entrada(**{"deseado": self.entrada.deseado, "chestnut": self.entrada.chestnut, **cambios})
    self.t += cambio.PERIODO_S
    return self.v.revisar(parado, acoplado)

  def publicado(self):
    return json.loads(self.params.valores.get(sel.PARAM_ACTIVO, "{}"))


def test_cambio_pedido_espera_a_parado_y_desacoplado():
  e = Escena(M1, "m1")
  assert e.paso(deseado="m2") is None
  assert e.v.pendiente == M2 and e.publicado()["pendiente"] == "equipo m2"
  assert e.paso(parado=True, acoplado=True) is None
  assert e.paso(parado=False, acoplado=False) is None
  assert e.paso(parado=True, acoplado=False) == cambio.CAMBIO_PEDIDO


def test_volver_a_pedir_el_que_corre_quita_el_pendiente():
  e = Escena(M1, "m1")
  e.paso(deseado="m2")
  e.paso(deseado="m1")
  assert e.v.pendiente is None and e.publicado()["pendiente"] == ""
  assert e.paso(parado=True, acoplado=False) is None


def test_cambio_que_no_cambia_de_modelo_no_recarga():
  e = Escena(SERIE_C, None, chestnut=False)
  assert e.paso(chestnut=True) is None and e.v.pendiente is None
  assert e.paso(parado=True, acoplado=False) is None


def test_chestnut_que_aparece_recarga_al_parar():
  e = Escena(SERIE_C, "m1", chestnut=False)
  e.paso(chestnut=True)
  assert e.v.pendiente == M1
  assert e.paso(parado=True, acoplado=False) == cambio.CAMBIO_PEDIDO


def test_chestnut_que_desaparece_recarga_al_momento():
  e = Escena(M1, "m1")
  assert e.paso(chestnut=False, parado=False, acoplado=True) == cambio.CHESTNUT_PERDIDO


def test_tras_recargar_no_se_reintenta_sin_cambios():
  e = Escena(M1, "m1")
  e.paso(deseado="m2")
  assert e.paso(parado=True, acoplado=False) == cambio.CAMBIO_PEDIDO
  # m2 no cargo: modeld cayo al de serie con la misma entrada
  e.v.cargado(SERIE_C, e.entrada, {"origen": "serie"})
  for _ in range(3):
    assert e.paso(parado=True, acoplado=False) is None


def test_solo_mira_una_vez_por_segundo():
  e = Escena(M1, "m1")
  e.entrada = cambio.Entrada("m2", True)
  e.t += cambio.PERIODO_S / 2
  assert e.v.revisar(True, False) is None and e.v.pendiente is None


@pytest.mark.parametrize("v,standstill,esperado", [(0.0, False, True), (5.0, True, True), (0.5, False, False)])
def test_parado(v, standstill, esperado):
  assert cambio.parado(v, standstill) == esperado


# ------------------------------------------------------------------ registro

def test_params_registrados():
  with open(os.path.join(BASEDIR, "common", "params_keys.h")) as f:
    claves = f.read()
  for k in (sel.PARAM_DESEADO, sel.PARAM_ACTIVO, "OrbitModelos"):
    assert f'{{"{k}",' in claves


def test_gestor_solo_offroad():
  with open(os.path.join(BASEDIR, "system", "manager", "process_config.py")) as f:
    texto = f.read()
  assert 'PythonProcess("orbit_modelos", "orbit.modelos.gestor", only_offroad' in texto
