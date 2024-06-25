import json
import math
import os
import requests
import threading

from cereal import log
from openpilot.common.api import Api
from openpilot.common.params import Params
from openpilot.selfdrive.navd.helpers import (Coordinate, coordinate_from_param)
from openpilot.common.swaglog import cloudlog

# Constantes para la lógica de recomputación de rutas
REROUTE_DISTANCE = 25
REROUTE_COUNTER_MIN = 3

# Método independiente para recomputar la ruta
def recompute_route(route_engine, new_destination=None):
    # Si no hay una última posición conocida, no hacer nada
    if route_engine.last_position is None:
        return

    # Obtener parámetros del sistema
    params = Params()

    # Obtener nuevo destino si no se pasa como parámetro
    if new_destination is None:
        new_destination = coordinate_from_param("NavDestination", params)
    
    # Si no hay nuevo destino, limpiar la ruta y resetear los límites de recomputación
    if new_destination is None:
        route_engine.clear_route()
        route_engine.reset_recompute_limits()
        return

    # Determinar si se debe recomputar la ruta
    should_recompute = route_engine.should_recompute()

    # Verificar si el nuevo destino es diferente del actual
    if new_destination != route_engine.nav_destination:
        cloudlog.warning(f"Got new destination from NavDestination param {new_destination}")
        should_recompute = True
        route_engine.nav_destination = new_destination

    # No recomputar cuando el GPS no es confiable y step_idx no es None
    if not route_engine.gps_ok and route_engine.step_idx is not None:
        return

    # Verificar si se debe recomputar la ruta
    if route_engine.recompute_countdown == 0 and should_recompute:
        # Realizar el cálculo de la ruta con el nuevo destino
        route_engine.recompute_countdown = 2 ** route_engine.recompute_backoff
        route_engine.recompute_backoff = min(6, route_engine.recompute_backoff + 1)
        route_engine.calculate_route(route_engine.nav_destination)
        route_engine.reroute_counter = 0
    else:
        # Reducir el contador de recomputación
        route_engine.recompute_countdown = max(0, route_engine.recompute_countdown - 1)
