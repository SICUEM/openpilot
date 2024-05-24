import subprocess
import sys
import time

class InstallMqtt:

  def __init__(self):
    self.instalado = True
    try:
      import paho.mqtt.client
    except ImportError:
      self.instalado = False
    return

  def install(self) -> bool:
    if not self.instalado:
      try:
        import paho.mqtt.client
        self.instalado = True
      except ImportError:
        self.instalado = False
    if not self.instalado:
      try:
        subprocess.call([sys.executable, "-m", "pip", "install", "paho-mqtt"])
      except subprocess.CalledProcessError as e:
        None
      try:
        import paho.mqtt.client
        self.instalado = True
      except ImportError:
        self.instalado = False
    return self.instalado

if __name__ == '__main__':
  installMqtt = InstallMqtt()
  if installMqtt.instalado:
    exit(0)
  for i in range(15):
    code = installMqtt.install()
    if code == True:
      subprocess.Popen(["systemctl", "reboot", "-i"], shell=True)
      time.sleep(5)
      import Javi.Reset.Comma
    time.sleep(2)
