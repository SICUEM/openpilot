"""En que dispositivo estamos y que le toca con chestnut: la camara para la que se compila, el
destino de compilacion, si comma lo soporta oficialmente y los avisos conocidos. Tambien si
chestnut esta conectado y a que velocidad va su USB.

  comma four (mici) ... soporte OFICIAL de comma. Camara 1344x760.
  comma 3X (tizi) ..... SIN soporte oficial, pero funciona: lo probo comma y lo usa la
                        comunidad (y forks como StarPilot). Camara 1928x1208. Aviso conocido:
                        el cable USB puede tapar el GPS del 3X (cable optico o ferritas).
  comma 3 (tici) ...... sin soporte y sin pruebas conocidas. Se intenta igual.
  PC .................. chestnut SIMULADO con la GPU NVIDIA del PC (CUDA), para ver el flujo
                        entero en el simulador. "Conectado" = existe ~/.comma/orbit_chestnut_sim
                        (tools/orbit/chestnut_sim.py conectar | desconectar).

La deteccion USB (0xADD1:0x0001) y los flags de tinygrad son los mismos en los tres comma: lo que
cambia es la camara (el .pkl lleva el warp de UNA resolucion) y lo que se avisa.

comma da chestnut por lento por debajo de 5000 Mbps (system/hardware/chestnut/status.py en su
rama de desarrollo): con menos, subir los frames a la GPU no llega a tiempo.
"""
from dataclasses import dataclass
from pathlib import Path

from openpilot.common.transformations.camera import _ar_ox_fisheye, _os_fisheye
from openpilot.system.hardware import HARDWARE, PC
from openpilot.system.hardware.hw import Paths
from openpilot.selfdrive.modeld.helpers import USBGPU_PID, USBGPU_VID, usbgpu_present
from openpilot.orbit.modelos import paquete as pq

USB_MINIMO_MBPS = 5000


@dataclass(frozen=True)
class Perfil:
  dispositivo: str            # tipo de HARDWARE: mici | tizi | tici | pc
  nombre: str
  camara: tuple[int, int]     # camara de carretera: el .pkl lleva el warp de esta resolucion
  destino: str                # destino de compilacion de chestnut (paquete.DESTINO_*)
  oficial: bool               # comma lo soporta oficialmente
  avisos: tuple[str, ...] = ()


PERFILES = {
  "mici": Perfil("mici", "comma four", _os_fisheye.size, pq.DESTINO_USBGPU, True),
  "tizi": Perfil("tizi", "comma 3X", _ar_ox_fisheye.size, pq.DESTINO_USBGPU, False, (
    "comma 3X: chestnut sin soporte oficial de comma (probado por comma y la comunidad)",
    "comma 3X: el cable USB puede quitar el GPS; probar cable optico o ferritas en los dos extremos",
  )),
  "tici": Perfil("tici", "comma 3", _ar_ox_fisheye.size, pq.DESTINO_USBGPU, False, (
    "comma 3: chestnut sin soporte oficial y sin pruebas conocidas",
  )),
  # el simulador emite la camara del 3X
  "pc": Perfil("pc", "PC (chestnut simulado con la GPU NVIDIA)", _ar_ox_fisheye.size, pq.DESTINO_GPU_PC, False),
}


def perfil() -> Perfil | None:
  return PERFILES.get("pc" if PC else HARDWARE.get_device_type())


def archivo_simulado() -> Path:
  return Path(Paths.comma_home()) / "orbit_chestnut_sim"


def presente() -> bool:
  return archivo_simulado().exists() if PC else usbgpu_present()


def velocidad_usb_mbps() -> int | None:
  """Velocidad negociada del USB de chestnut, None si no esta (o en el PC)."""
  if PC:
    return None
  for d in Path("/sys/bus/usb/devices").glob("*"):
    try:
      if int((d / "idVendor").read_text(), 16) == USBGPU_VID and int((d / "idProduct").read_text(), 16) == USBGPU_PID:
        return int(float((d / "speed").read_text()))
    except Exception:
      continue
  return None


def avisos(p: Perfil, conectado: bool, mbps: int | None) -> list[str]:
  lista = list(p.avisos)
  if conectado and mbps is not None and mbps < USB_MINIMO_MBPS:
    lista.append(f"USB de chestnut lento: {mbps} Mbps (minimo {USB_MINIMO_MBPS}); revisar cable y puerto")
  return lista
