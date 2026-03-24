import io
import json
import numpy as np
import os
import pyopencl as cl
import pyopencl.array as cl_array

from PIL import Image
from msgq.visionipc import VisionIpcServer, VisionStreamType
from cereal import messaging

from openpilot.common.basedir import BASEDIR
from openpilot.tools.sim.lib.common import W, H

THUMBNAIL_W = W // 4
THUMBNAIL_H = H // 4
THUMBNAIL_EVERY_N_FRAMES = 5
JETSON_CONFIG_FILE = os.path.join(BASEDIR, "sicuem/adripilot/config_jetson.json")

class Camerad:
  """Simulates the camerad daemon"""
  def __init__(self, dual_camera):
    self.pm = messaging.PubMaster(['roadCameraState', 'wideRoadCameraState', 'thumbnail'])
    self.zmq_client = None
    self._init_jetson_zmq()

    self.frame_road_id = 0
    self.frame_wide_id = 0
    self.vipc_server = VisionIpcServer("camerad")

    self.vipc_server.create_buffers(VisionStreamType.VISION_STREAM_ROAD, 5, False, W, H)
    if dual_camera:
      self.vipc_server.create_buffers(VisionStreamType.VISION_STREAM_WIDE_ROAD, 5, False, W, H)

    self.vipc_server.start_listener()

    # set up for pyopencl rgb to yuv conversion
    self.ctx = cl.create_some_context()
    self.queue = cl.CommandQueue(self.ctx)
    cl_arg = f" -DHEIGHT={H} -DWIDTH={W} -DRGB_STRIDE={W * 3} -DUV_WIDTH={W // 2} -DUV_HEIGHT={H // 2} -DRGB_SIZE={W * H} -DCL_DEBUG "

    kernel_fn = os.path.join(BASEDIR, "tools/sim/rgb_to_nv12.cl")
    with open(kernel_fn) as f:
      prg = cl.Program(self.ctx, f.read()).build(cl_arg)
      self.krnl = prg.rgb_to_nv12
    self.Wdiv4 = W // 4 if (W % 4 == 0) else (W + (4 - W % 4)) // 4
    self.Hdiv4 = H // 4 if (H % 4 == 0) else (H + (4 - H % 4)) // 4

  def _init_jetson_zmq(self):
    """Inicializa ZMQClient para enviar imágenes a la Jetson si está habilitado en config."""
    self._jpeg_quality = 60
    try:
      if not os.path.exists(JETSON_CONFIG_FILE):
        print("Camerad: config_jetson.json no encontrado, Jetson ZMQ deshabilitado")
        return

      with open(JETSON_CONFIG_FILE, 'r') as f:
        config = json.load(f)

      if not config.get("jetson_enabled", False):
        print("Camerad: Jetson ZMQ deshabilitado en config")
        return

      self._jpeg_quality = int(config.get("jpeg_quality", 60))

      from openpilot.sicuem.adripilot.zmq_client import ZMQClient
      self.zmq_client = ZMQClient(
        jetson_ip=config.get("jetson_ip", "127.0.0.1"),
        img_port=int(config.get("jetson_img_port", 5555)),
        torque_port=int(config.get("jetson_torque_port", 5556)),
        jpeg_quality=self._jpeg_quality,
      )
      self.zmq_client.start()
      print(f"Camerad: Jetson ZMQ activo -> {config.get('jetson_ip')}:{config.get('jetson_img_port')}")
    except Exception as e:
      print(f"Camerad: error iniciando Jetson ZMQ: {e}")
      self.zmq_client = None

  def cam_send_yuv_road(self, yuv, rgb=None):
    self._send_yuv(yuv, self.frame_road_id, 'roadCameraState', VisionStreamType.VISION_STREAM_ROAD)
    if rgb is not None:
      self._send_jetson_frame(rgb)
      if self.frame_road_id % THUMBNAIL_EVERY_N_FRAMES == 0:
        self._publish_thumbnail(rgb, self.frame_road_id)
    self.frame_road_id += 1

  def cam_send_yuv_wide_road(self, yuv):
    self._send_yuv(yuv, self.frame_wide_id, 'wideRoadCameraState', VisionStreamType.VISION_STREAM_WIDE_ROAD)
    self.frame_wide_id += 1

  # Returns: yuv bytes
  def rgb_to_yuv(self, rgb):
    assert rgb.shape == (H, W, 3), f"{rgb.shape}"
    assert rgb.dtype == np.uint8

    rgb_cl = cl_array.to_device(self.queue, rgb)
    yuv_cl = cl_array.empty_like(rgb_cl)
    self.krnl(self.queue, (self.Wdiv4, self.Hdiv4), None, rgb_cl.data, yuv_cl.data).wait()
    yuv = np.resize(yuv_cl.get(), rgb.size // 2)
    return yuv.data.tobytes()

  def _publish_thumbnail(self, rgb, frame_id):
    """Generates a JPEG thumbnail from the RGB frame and publishes it as a cereal 'thumbnail' message."""
    img = Image.fromarray(rgb)
    img = img.resize((THUMBNAIL_W, THUMBNAIL_H))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=50)
    jpeg_data = buf.getvalue()

    eof = int(frame_id * 0.05 * 1e9)
    dat = messaging.new_message('thumbnail')
    dat.thumbnail.frameId = frame_id
    dat.thumbnail.timestampEof = eof
    dat.thumbnail.thumbnail = jpeg_data
    self.pm.send('thumbnail', dat)

  def _send_jetson_frame(self, rgb):
    """Codifica el frame RGB como JPEG y lo envía a la Jetson via ZMQ cada frame."""
    if self.zmq_client is None:
      return
    try:
      img = Image.fromarray(rgb)
      buf = io.BytesIO()
      img.save(buf, format='JPEG', quality=self._jpeg_quality)
      self.zmq_client.send_image(buf.getvalue())
    except Exception as e:
      print(f"Camerad: error enviando frame a Jetson: {e}")

  def _send_yuv(self, yuv, frame_id, pub_type, yuv_type):
    eof = int(frame_id * 0.05 * 1e9)
    self.vipc_server.send(yuv_type, yuv, frame_id, eof, eof)

    dat = messaging.new_message(pub_type, valid=True)
    msg = {
      "frameId": frame_id,
      "transform": [1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0]
    }
    setattr(dat, pub_type, msg)
    self.pm.send(pub_type, dat)
