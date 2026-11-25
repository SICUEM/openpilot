"""Gramatica mici de las tarjetas de texto: minuscula inicial, sin vinetas, siglas intactas."""
from openpilot.selfdrive.ui.sunnypilot.mici.widgets.orbit_widgets import minuscula, trozos_mici


def test_minuscula_baja_solo_el_inicio_de_frase():
  assert minuscula("Este comma está vinculado. Si lo desvinculas, para.") == "este comma está vinculado. si lo desvinculas, para."
  assert minuscula("¿Volver a los valores seguros?") == "¿volver a los valores seguros?"
  assert minuscula("GPS y QR siguen igual") == "GPS y QR siguen igual"
  assert minuscula("Posición (GPS)") == "posición (GPS)"


def test_las_listas_van_una_por_tarjeta_sin_vineta():
  assert trozos_mici("Pregunta\n\n- Modo de volante: Comma\n- Modo taller: desarmado") == [
    "pregunta", "modo de volante: Comma", "modo taller: desarmado"]
