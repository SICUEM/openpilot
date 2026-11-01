"""Paquetes de modelos de conduccion del equipo: donde viven en el comma, que contienen y
cuando estan LISTOS para que modeld los cargue en chestnut.

UN PAQUETE es una carpeta `<dir_modelos()>/<id>/` (el id es el nombre de la carpeta) con:

  driving_vision.onnx + driving_on_policy.onnx   fuente; se compila si no hay .pkl valido
  driving_tinygrad.pkl                            ya compilado por quien entrega (opcional)
  manifest.json                                   opcional: {"nombre", "version", "notas"}
  compilado/                                      lo escribe ORBIT, no se toca a mano

LISTO significa que existe el marcador `compilado/<destino>_<W>x<H>.json` y sigue siendo
verdad: el .pkl al que apunta no ha cambiado (tamano y mtime) y se compilo con el mismo
tinygrad que hay en el repo. Un .pkl de otro tinygrad no carga, asi que una actualizacion
de tinygrad_repo invalida todos los marcadores y el gestor vuelve a preparar los modelos.
modeld solo mira el marcador (barato); el trabajo caro (validar, compilar) es del gestor.

EL CONTRATO. "Mismo formato que openpilot" se comprueba contra los ONNX de serie de
selfdrive/modeld/models: mismas entradas, mismas imagenes, y al menos las mismas salidas
con nombre (las que leen parse_model_outputs y el resto de openpilot). El tamano del
estado oculto puede ser otro (un modelo mas potente), pero features_buffer de la politica
tiene que casar con el hidden_state de SU vision.

Sin cereal ni pyray: lo importan modeld, el gestor, la herramienta de PC y los tests.
"""
import hashlib
import io
import json
import os
import pickle
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from openpilot.common.file_chunker import get_manifest_path, read_file_chunked
from openpilot.system.hardware import PC
from openpilot.system.hardware.hw import Paths

DIR_MODELOS_DISPOSITIVO = "/data/orbit_models"
VISION_ONNX = "driving_vision.onnx"
POLICY_ONNX = "driving_on_policy.onnx"
PKL_ENTREGADO = "driving_tinygrad.pkl"
MANIFIESTO = "manifest.json"
DIR_COMPILADO = "compilado"

DESTINO_USBGPU = "usbgpu"  # chestnut: la GPU AMD por USB
DESTINO_LOCAL = "local"    # PC / simulador: el backend con el que se compilo el repo
DESTINO_GPU_PC = "gpu_pc"  # PC: chestnut simulado con la GPU NVIDIA (orbit/modelos/chestnut.py)

# id = nombre de carpeta. Se usa en rutas y llega desde la app: nada de "..", "/" ni vacios.
ID_VALIDO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

# Entradas que el modeld de serie le da al modelo. Si cambian, modeld no sabe alimentarlo.
ENTRADAS_VISION = ("img", "big_img")
ENTRADAS_POLITICA = ("features_buffer", "desire_pulse", "traffic_convention")
# compile_modeld tambien le pasa action_t (con la forma de traffic_convention); el modelo de
# serie no la declara y se ignora, pero un modelo nuevo puede usarla.
ENTRADAS_POLITICA_OPCIONALES = ("action_t",)
# Formas que fija el propio modeld (deseos, convencion de trafico): tienen que ser iguales.
FORMAS_FIJAS_POLITICA = ("desire_pulse", "traffic_convention")


def dir_modelos() -> Path:
  if d := os.getenv("ORBIT_MODELS_DIR"):
    return Path(d)
  if PC:
    return Path(Paths.comma_home()) / "orbit_models"
  return Path(DIR_MODELOS_DISPOSITIVO)


def id_valido(modelo_id) -> bool:
  return isinstance(modelo_id, str) and ID_VALIDO.match(modelo_id) is not None


def camara_str(cam: tuple[int, int]) -> str:
  return f"{cam[0]}x{cam[1]}"


@lru_cache(maxsize=1)
def tinygrad_ref() -> str | None:
  from openpilot.sunnypilot.models.tinygrad_ref import get_tinygrad_ref
  return get_tinygrad_ref()


def existe_pkl(ruta: Path) -> bool:
  return ruta.is_file() or os.path.isfile(get_manifest_path(str(ruta)))


def huella(ruta: Path) -> dict | None:
  """Tamano y mtime del .pkl (o de su chunkmanifest si va troceado). None si no existe."""
  for p in (ruta, Path(get_manifest_path(str(ruta)))):
    try:
      st = p.stat()
      return {"fichero": p.name, "tamano": st.st_size, "mtime_ns": st.st_mtime_ns}
    except FileNotFoundError:
      continue
  return None


def escribir_json_atomico(ruta: Path, datos: dict) -> None:
  ruta.parent.mkdir(parents=True, exist_ok=True)
  tmp = ruta.with_name(ruta.name + ".tmp")
  tmp.write_text(json.dumps(datos, indent=2, sort_keys=True))
  os.replace(tmp, ruta)


def leer_json(ruta: Path) -> dict | None:
  try:
    datos = json.loads(ruta.read_text())
  except (OSError, ValueError):
    return None
  return datos if isinstance(datos, dict) else None


# ------------------------------------------------------------------ inspeccion del paquete

@dataclass
class Paquete:
  modelo_id: str
  ruta: Path
  manifiesto: dict = field(default_factory=dict)
  tiene_onnx: bool = False
  tiene_pkl: bool = False

  @property
  def nombre(self) -> str:
    return str(self.manifiesto.get("nombre") or self.modelo_id)

  @property
  def version(self) -> str:
    return str(self.manifiesto.get("version") or "")

  @property
  def pkl_entregado(self) -> Path:
    return self.ruta / PKL_ENTREGADO

  @property
  def vision_onnx(self) -> Path:
    return self.ruta / VISION_ONNX

  @property
  def policy_onnx(self) -> Path:
    return self.ruta / POLICY_ONNX


def inspeccionar(ruta: Path) -> Paquete:
  ruta = Path(ruta)
  p = Paquete(modelo_id=ruta.name, ruta=ruta)
  p.manifiesto = leer_json(ruta / MANIFIESTO) or {}
  p.tiene_onnx = (ruta / VISION_ONNX).is_file() and (ruta / POLICY_ONNX).is_file()
  p.tiene_pkl = existe_pkl(ruta / PKL_ENTREGADO)
  return p


def listar_paquetes(base: Path | None = None) -> list[Paquete]:
  base = base or dir_modelos()
  if not base.is_dir():
    return []
  return [inspeccionar(d) for d in sorted(base.iterdir())
          if d.is_dir() and id_valido(d.name)]


# ------------------------------------------------------------------ contrato

def metadata_onnx(ruta: Path) -> dict:
  # tinygrad solo lee el protobuf (formas y metadata_props); no carga pesos en ninguna GPU
  from openpilot.selfdrive.modeld.get_model_metadata import make_metadata_dict
  return make_metadata_dict(str(ruta))


@lru_cache(maxsize=1)
def contrato_referencia() -> dict:
  from openpilot.selfdrive.modeld.helpers import MODELS_DIR
  return {"vision": metadata_onnx(MODELS_DIR / VISION_ONNX),
          "on_policy": metadata_onnx(MODELS_DIR / POLICY_ONNX)}


def _largo(s) -> int | None:
  if isinstance(s, slice) and s.stop is not None:
    return s.stop - (s.start or 0)
  return None


def comparar_contrato(vision: dict, politica: dict, ref: dict | None = None) -> tuple[list[str], list[str]]:
  """(errores, avisos). Con errores el modelo NO se carga; los avisos son diferencias admitidas."""
  ref = ref or contrato_referencia()
  errores: list[str] = []
  avisos: list[str] = []

  for parte, meta, entradas, opcionales in (("vision", vision, ENTRADAS_VISION, ()),
                                            ("on_policy", politica, ENTRADAS_POLITICA, ENTRADAS_POLITICA_OPCIONALES)):
    formas = meta.get("input_shapes") or {}
    if not set(entradas) <= set(formas) <= set(entradas) | set(opcionales):
      errores.append(f"{parte}: entradas {sorted(formas)}, se esperaban {sorted(entradas)}"
                     + (f" (opcional: {', '.join(opcionales)})" if opcionales else ""))
    # 'pad' es relleno del tensor de salida, nadie lo lee
    faltan = set(ref[parte].get("output_slices") or {}) - set(meta.get("output_slices") or {}) - {"pad"}
    if faltan:
      errores.append(f"{parte}: faltan salidas {sorted(faltan)}")

  ref_v = ref["vision"]["input_shapes"]
  for k in ENTRADAS_VISION:
    if k in vision.get("input_shapes", {}) and tuple(vision["input_shapes"][k]) != tuple(ref_v[k]):
      errores.append(f"vision: {k} con forma {tuple(vision['input_shapes'][k])}, modeld da {tuple(ref_v[k])}")

  ref_p = ref["on_policy"]["input_shapes"]
  formas_p = politica.get("input_shapes", {})
  for k in FORMAS_FIJAS_POLITICA:
    if k in formas_p and tuple(formas_p[k]) != tuple(ref_p[k]):
      errores.append(f"on_policy: {k} con forma {tuple(formas_p[k])}, modeld da {tuple(ref_p[k])}")
  if "action_t" in formas_p and tuple(formas_p["action_t"]) != tuple(ref_p["traffic_convention"]):
    errores.append(f"on_policy: action_t con forma {tuple(formas_p['action_t'])}, modeld da {tuple(ref_p['traffic_convention'])}")

  oculto = _largo((vision.get("output_slices") or {}).get("hidden_state"))
  fb = formas_p.get("features_buffer")
  if oculto is not None and fb is not None:
    if len(fb) != 3 or fb[2] != oculto:
      errores.append(f"on_policy: features_buffer {tuple(fb)} no casa con hidden_state de {oculto} de su vision")
    ref_oculto = _largo(ref["vision"]["output_slices"].get("hidden_state"))
    if oculto != ref_oculto:
      avisos.append(f"hidden_state de {oculto} (el de serie es {ref_oculto}): admitido")
    if len(fb) == 3 and tuple(fb) != tuple(ref_p["features_buffer"]):
      avisos.append(f"features_buffer {tuple(fb)} (el de serie es {tuple(ref_p['features_buffer'])}): admitido")
  return errores, avisos


# ------------------------------------------------------------------ .pkl sin tinygrad

class _Opaco:
  """Sustituto de cualquier clase que no sea un contenedor basico (JIT, buffers, tinygrad...).
  Acepta lo que pickle le haga (construir, __setstate__, append, setitem) y lo ignora."""
  def __init__(self, *args, **kwargs):
    pass

  def __setstate__(self, state):
    pass

  def __call__(self, *args, **kwargs):
    return _Opaco()

  def append(self, x):
    pass

  def extend(self, xs):
    pass

  def __setitem__(self, k, v):
    pass


_CLASES_SEGURAS = {("builtins", n) for n in ("slice", "set", "frozenset", "tuple", "list", "dict", "int", "float",
                                              "complex", "bytes", "bytearray", "str", "bool", "range")}
_CLASES_SEGURAS |= {("collections", "OrderedDict"), ("collections", "defaultdict")}


class _LectorMetadata(pickle.Unpickler):
  """Lee el diccionario del .pkl SIN ejecutar nada: toda clase que no sea un contenedor basico
  se cambia por _Opaco. Sirve para leer 'metadata' y las claves de camara en el PC (sin
  chestnut) y en el gestor, sin abrir la GPU ni importar tinygrad."""
  def find_class(self, module, name):
    if (module, name) in _CLASES_SEGURAS:
      return super().find_class(module, name)
    return type(name, (_Opaco,), {"__module__": module})

  def persistent_load(self, pid):
    return _Opaco()


def leer_pkl(ruta: Path) -> dict:
  """{'metadata', 'camaras', 'amd', 'run_policy'} de un .pkl de compile_modeld. Lanza
  ValueError si no tiene la estructura de compile_modeld."""
  datos = read_file_chunked(str(ruta))
  try:
    obj = _LectorMetadata(io.BytesIO(datos)).load()
  except Exception as e:
    raise ValueError(f"no se puede leer el .pkl: {type(e).__name__}: {e}") from e
  meta = obj.get("metadata") if isinstance(obj, dict) else None
  if not isinstance(meta, dict) or not isinstance(meta.get("vision"), dict) or not isinstance(meta.get("on_policy"), dict):
    raise ValueError("el .pkl no tiene metadata de vision y on_policy (no es de compile_modeld)")
  camaras = sorted(k for k in obj if isinstance(k, tuple) and len(k) == 2 and all(isinstance(x, int) for x in k))
  dispositivos = dispositivos_pkl(datos)
  return {
    "metadata": meta,
    "camaras": camaras,
    "dispositivos": dispositivos,
    "amd": any("AMD" in d for d in dispositivos),
    "run_policy": "run_policy" in obj,
  }


# Un texto corto en un pickle es SHORT_BINUNICODE: 0x8c, un byte de longitud y el texto. Los
# nombres de dispositivo de los buffers de los JIT van asi. Buscar b"AMD" a pelo no sirve: sale
# por azar dentro de los pesos (un .pkl de CUDA lo "contiene" tres veces).
_DISPOSITIVO_PKL = re.compile(rb"\x8c([\x02-\x20])((?:USB\+)?(?:AMD|CUDA|QCOM|CPU|NPY|CL|METAL|NV|GPU|DSP|DISK|PYTHON|LLVM)(?::[A-Z0-9]+)?)")


def dispositivos_pkl(datos: bytes) -> list[str]:
  return sorted({m.group(2).decode() for m in _DISPOSITIVO_PKL.finditer(datos) if m.group(1)[0] == len(m.group(2))})


# ------------------------------------------------------------------ marcador de LISTO

def ruta_marcador(paq_ruta: Path, destino: str, cam: tuple[int, int]) -> Path:
  return Path(paq_ruta) / DIR_COMPILADO / f"{destino}_{camara_str(cam)}.json"


def ruta_pkl_compilado(paq_ruta: Path, destino: str, cam: tuple[int, int]) -> Path:
  return Path(paq_ruta) / DIR_COMPILADO / f"{destino}_{camara_str(cam)}.pkl"


def escribir_marcador(paq_ruta: Path, destino: str, cam: tuple[int, int], pkl: Path, origen: str) -> None:
  escribir_json_atomico(ruta_marcador(paq_ruta, destino, cam), {
    "v": 1,
    "pkl": os.path.relpath(pkl, paq_ruta),
    "origen": origen,  # "entregado" (venia compilado) o "compilado" (lo compilo ORBIT)
    "destino": destino,
    "camara": camara_str(cam),
    "tinygrad": tinygrad_ref(),
    "huella": huella(Path(pkl)),
    "ts": time.time_ns() // 1_000_000_000,
  })


def pkl_listo(paq_ruta: Path, destino: str, cam: tuple[int, int]) -> Path | None:
  """Ruta del .pkl si el modelo esta listo para este destino y camara; None si no."""
  m = leer_json(ruta_marcador(paq_ruta, destino, cam))
  if not m or m.get("v") != 1 or not isinstance(m.get("pkl"), str):
    return None
  pkl = (Path(paq_ruta) / m["pkl"]).resolve()
  if Path(paq_ruta).resolve() not in pkl.parents:
    return None
  if m.get("tinygrad") != tinygrad_ref():
    return None
  if m.get("huella") is None or m.get("huella") != huella(pkl):
    return None
  return pkl


def huella_entradas(paq: Paquete, destino: str, cam: tuple[int, int]) -> str:
  """Resumen de todo lo que decide el resultado de preparar un modelo. Si un intento fallo
  con esta misma huella, no se repite: repetir solo vuelve a fallar (y a ocupar la GPU)."""
  partes = [destino, camara_str(cam), str(tinygrad_ref())]
  for p in (paq.pkl_entregado, paq.vision_onnx, paq.policy_onnx):
    partes.append(json.dumps(huella(p), sort_keys=True))
  return hashlib.sha256("|".join(partes).encode()).hexdigest()[:16]
