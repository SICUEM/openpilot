import os

# Modelos 3D de los obstaculos que no trae commaai/metadrive@minimal (ver el README de la carpeta).
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "metadrive", "models"))


def local_model_path(*path_string, models_dir=MODELS_DIR):
  # ("models", "ferra/vehicle.gltf") o ("models", "ferra", "right_tire_front.gltf") -> ruta en el repo,
  # solo si esa carpeta de modelo existe aqui. Cualquier otro asset sigue saliendo del paquete.
  if len(path_string) < 2 or path_string[0] != "models":
    return None
  rel = os.path.join(*path_string[1:])
  folder = rel.replace("\\", "/").split("/")[0]
  if not os.path.isdir(os.path.join(models_dir, folder)):
    return None
  return os.path.join(models_dir, rel)


def missing_models(folders, models_dir=MODELS_DIR):
  return [f for f in folders if not os.path.isdir(os.path.join(models_dir, f))]


def patch_asset_loader():
  from metadrive.engine.asset_loader import AssetLoader

  if getattr(AssetLoader, "_orbit_patched", False):
    return
  original = AssetLoader.file_path

  def file_path(*path_string, unix_style=True):
    local = local_model_path(*path_string)
    return local if local is not None else original(*path_string, unix_style=unix_style)

  AssetLoader.file_path = staticmethod(file_path)
  AssetLoader._orbit_patched = True
