import os

from openpilot.tools.sim.bridge.metadrive import metadrive_assets as a

OBSTACLE_MODELS = ["traffic_cone", "barrier", "ferra", "beetle", "130", "lada", "truck"]


def test_repo_has_every_obstacle_model():
  assert a.missing_models(OBSTACLE_MODELS) == []


def test_vehicle_style_path_resolves_to_repo():
  # vehicles pass "folder/file" as a single component
  p = a.local_model_path("models", "ferra/vehicle.gltf")
  assert p == os.path.join(a.MODELS_DIR, "ferra", "vehicle.gltf")
  assert os.path.isfile(p)


def test_split_path_resolves_to_repo():
  p = a.local_model_path("models", "traffic_cone", "scene.gltf")
  assert os.path.isfile(p)


def test_models_not_in_repo_fall_through():
  assert a.local_model_path("models", "warning", "warning.gltf") is None
  assert a.local_model_path("models", "box.bam") is None


def test_non_model_assets_fall_through():
  assert a.local_model_path("textures", "sky", "sky.jpg") is None
  assert a.local_model_path("models") is None


def test_patch_prefers_repo_and_keeps_package_for_the_rest():
  from metadrive.engine.asset_loader import AssetLoader
  a.patch_asset_loader()
  a.patch_asset_loader()                     # idempotent
  assert AssetLoader.file_path("models", "barrier", "scene.gltf").startswith(a.MODELS_DIR)
  assert not AssetLoader.file_path("models", "warning", "warning.gltf").startswith(a.MODELS_DIR)
