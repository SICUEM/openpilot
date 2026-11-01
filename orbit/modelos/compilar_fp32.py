#!/usr/bin/env python3
"""compile_modeld.py con los pesos fp16 del ONNX subidos a fp32. Solo para el chestnut simulado
del PC (destino gpu_pc): las NVIDIA Pascal (GTX 10xx) hacen fp16 a una fraccion de su ritmo en
fp32. En la GTX 1050, el modelo pequeno de serie pasa de 124 ms a 22 ms.

  python3 orbit/modelos/compilar_fp32.py <los mismos argumentos que compile_modeld.py>
"""
import runpy
import sys

from tinygrad import Tensor, dtypes
import tinygrad.nn.onnx as onnx

from openpilot.orbit.modelos.compilar import COMPILE_MODELD


class OnnxRunnerFp32(onnx.OnnxRunner):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for k, v in self.graph_values.items():
      if isinstance(v, Tensor) and v.dtype == dtypes.half:
        self.graph_values[k] = v.cast(dtypes.float32)


if __name__ == "__main__":
  # compile_modeld importa OnnxRunner dentro de su __main__: basta con cambiarlo en el modulo
  onnx.OnnxRunner = OnnxRunnerFp32
  sys.argv = [COMPILE_MODELD, *sys.argv[1:]]
  runpy.run_path(COMPILE_MODELD, run_name="__main__")
