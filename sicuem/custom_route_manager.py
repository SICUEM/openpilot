def recompute_route(route_manager_instance):
    # Lógica del método aquí
    if route_manager_instance.last_position is None:
        return

    if route_manager_instance.current_waypoint_idx >= len(route_manager_instance.waypoints):
        # Todos los waypoints han sido alcanzados
        route_manager_instance.clear_route()
        return

    new_destination = route_manager_instance.waypoints[route_manager_instance.current_waypoint_idx]  # Próximo destino
    should_recompute = route_manager_instance.should_recompute()
    if new_destination != route_manager_instance.nav_destination:
        # Se ha recibido un nuevo destino
        should_recompute = True

    if not route_manager_instance.gps_ok and route_manager_instance.step_idx is not None:
        # No recomputar si el GPS no es confiable y hay una ruta en curso
        return

    if route_manager_instance.recompute_countdown == 0 and should_recompute:
        # Recalcula la ruta si es necesario
        route_manager_instance.recompute_countdown = 2 ** route_manager_instance.recompute_backoff
        route_manager_instance.recompute_backoff = min(6, route_manager_instance.recompute_backoff + 1)
        route_manager_instance.calculate_route(new_destination)
        route_manager_instance.reroute_counter = 0
    else:
      # Decrementa el contador de recomputación
      self.recompute_countdown = max(0, self.recompute_countdown - 1)

  def calculate_route(self, destination):
    # Calcula la ruta desde la posición actual hasta el destino
    cloudlog.warning(f"Calculating route {self.last_position} -> {destination}")
    self.nav_destination = destination

    # Obtiene la configuración de idioma
    lang = self.params.get('LanguageSetting', encoding='utf8')
    if lang is not None:
      lang = lang.replace('main_', '')

    # Obtiene el token de Mapbox
    token = self.mapbox_token
    if token is None:
      token = self.api.get_token()

    # Parámetros para la solicitud de la ruta
    params = {
      'access_token': token,
      'annotations': 'maxspeed',
      'geometries': 'geojson',
      'overview': 'full',
      'steps': 'true',
      'banner_instructions': 'true',
      'alternatives': 'false',
      'language': lang,
    }

    coords = [
      (self.last_position.longitude, self.last_position.latitude),
      (destination.longitude, destination.latitude)
    ]
    params['waypoints'] = f'0;{len(coords)-1}'
    if self.last_bearing is not None:
      params['bearings'] = f"{(self.last_bearing + 360) % 360:.0f},90" + (';'*(len(coords)-1))

    coords_str = ';'.join([f'{lon},{lat}' for lon, lat in coords])
    url = self.mapbox_host + '/directions/v5/mapbox/driving-traffic/' + coords_str
    try:
      resp = requests.get(url, params=params, timeout=10)
      if resp.status_code != 200:
        cloudlog.event("API request failed", status_code=resp.status_code, text=resp.text, error=True)
      resp.raise_for_status()

      r = resp.json()
      if len(r['routes']):
        # Procesa la ruta recibida
        self.route = r['routes'][0]['legs'][0]['steps']
        self.route_geometry = []

        maxspeed_idx = 0
        maxspeeds = r['routes'][0]['legs'][0]['annotation']['maxspeed']

        # Convierte las coordenadas
        for step in self.route:
          coords = []

          for c in step['geometry']['coordinates']:
            coord = Coordinate.from_mapbox_tuple(c)

            # El último paso no tiene límite de velocidad
            if (maxspeed_idx < len(maxspeeds)):
              maxspeed = maxspeeds[maxspeed_idx]
              if ('unknown' not in maxspeed) and ('none' not in maxspeed):
                coord.annotations['maxspeed'] = maxspeed_to_ms(maxspeed)

            coords.append(coord)
            maxspeed_idx += 1

          self.route_geometry.append(coords)
          maxspeed_idx -= 1  # Cada segmento termina con la misma coordenada que el inicio del siguiente

        self.step_idx = 0
      else:
        cloudlog.warning("Got empty route response")
        self.clear_route()

    except requests.exceptions.RequestException:
      cloudlog.exception("failed to get route")
      self.clear_route()

    self.send_route()

  def send_route(self):
    # Envía la ruta calculada a la interfaz de usuario
    coords = []

    if self.route is not None:
      for path in self.route_geometry:
        coords += [c.as_dict() for c in path]

    msg = messaging.new_message('navRoute', valid=True)
    msg.navRoute.coordinates = coords
    self.pm.send('navRoute', msg)

  def clear_route(self):
    # Limpia la ruta actual
    self.route = None
    self.route_geometry = None
    self.step_idx = None
    self.nav_destination = None

  def reset_recompute_limits(self):
    # Resetea los límites de recomputación
    self.recompute_backoff = 0
    self.recompute_countdown = 0

  def should_recompute(self):
    # Determina si se debe recomputar la ruta
    if self.step_idx is None or self.route is None:
      return True

    if self.step_idx == len(self.route) - 1:
      return False

    min_d = REROUTE_DISTANCE + 1
    path = self.route_geometry[self.step_idx]
    for i in range(len(path) - 1):
      a = path[i]
      b = path[i + 1]

      if a.distance_to(b) < 1.0:
        continue

      min_d = min(min_d, minimum_distance(a, b, self.last_position))

    if min_d > REROUTE_DISTANCE:
      self.reroute_counter += 1
    else:
      self.reroute_counter = 0
    return self.reroute_counter > REROUTE_COUNTER_MIN

  def update(self):
    # Actualiza el estado del vehículo y la ruta
    self.sm.update(0)

    if self.sm.updated["managerState"]:
      ui_pid = [p.pid for p in self.sm["managerState"].processes if p.name == "ui" and p.running]
      if ui_pid:
        if self.ui_pid and self.ui_pid != ui_pid[0]:
          cloudlog.warning("UI restarting, sending route")
          threading.Timer(5.0, self.send_route).start()
        self.ui_pid = ui_pid[0]

    self.update_location()
    try:
      self.recompute_route()
      self.send_instruction()
    except Exception:
      cloudlog.exception("navd.failed_to_compute")

  def send_instruction(self):
    # Envía instrucciones de navegación
    msg = messaging.new_message('navInstruction', valid=True)

    if self.step_idx is None:
      msg.valid = False
      self.pm.send('navInstruction', msg)
      return

    step = self.route[self.step_idx]
    geometry = self.route_geometry[self.step_idx]
    along_geometry = distance_along_geometry(geometry, self.last_position)
    distance_to_maneuver_along_geometry = step['distance'] - along_geometry

    banner_step = step
    if not len(banner_step['bannerInstructions']) and self.step_idx == len(self.route) - 1:
      banner_step = self.route[max(self.step_idx - 1, 0)]

    msg.navInstruction.maneuverDistance = distance_to_maneuver_along_geometry
    instruction = parse_banner_instructions(banner_step['bannerInstructions'], distance_to_maneuver_along_geometry)
    if instruction is not None:
      for k,v in instruction.items():
        setattr(msg.navInstruction, k, v)

    maneuvers = []
    for i, step_i in enumerate(self.route):
      if i < self.step_idx:
        distance_to_maneuver = -sum(self.route[j]['distance'] for j in range(i+1, self.step_idx)) - along_geometry
      elif i == self.step_idx:
        distance_to_maneuver = distance_to_maneuver_along_geometry
      else:
        distance_to_maneuver = distance_to_maneuver_along_geometry + sum(self.route[j]['distance'] for j in range(self.step_idx+1, i+1))

      instruction = parse_banner_instructions(step_i['bannerInstructions'], distance_to_maneuver)
      if instruction is None:
        continue
      maneuver = {'distance': distance_to_maneuver}
      if 'maneuverType' in instruction:
        maneuver['type'] = instruction['maneuverType']
      if 'maneuverModifier' in instruction:
        maneuver['modifier'] = instruction['maneuverModifier']
      maneuvers.append(maneuver)

    msg.navInstruction.allManeuvers = maneuvers

    remaining = 1.0 - along_geometry / max(step['distance'], 1)
    total_distance = step['distance'] * remaining
    total_time = step['duration'] * remaining

    if step['duration_typical'] is None:
      total_time_typical = total_time
    else:
      total_time_typical = step['duration_typical'] * remaining

    for i in range(self.step_idx + 1, len(self.route)):
      total_distance += self.route[i]['distance']
      total_time += self.route[i]['duration']
      if self.route[i]['duration_typical'] is None:
        total_time_typical += self.route[i]['duration']
      else:
        total_time_typical += self.route[i]['duration_typical']

    msg.navInstruction.distanceRemaining = total_distance
    msg.navInstruction.timeRemaining = total_time
    msg.navInstruction.timeRemainingTypical = total_time_typical

    closest_idx, closest = min(enumerate(geometry), key=lambda p: p[1].distance_to(self.last_position))
    if closest_idx > 0:
      if along_geometry < distance_along_geometry(geometry, geometry[closest_idx]):
        closest = geometry[closest_idx - 1]

    if ('maxspeed' in closest.annotations) and self.localizer_valid:
      msg.navInstruction.speedLimit = closest.annotations['maxspeed']

    if 'speedLimitSign' in step:
      if step['speedLimitSign'] == 'mutcd':
        msg.navInstruction.speedLimitSign = log.NavInstruction.SpeedLimitSign.mutcd
      elif step['speedLimitSign'] == 'vienna':
        msg.navInstruction.speedLimitSign = log.NavInstruction.SpeedLimitSign.vienna

    self.pm.send('navInstruction', msg)

    if distance_to_maneuver_along_geometry < -MANEUVER_TRANSITION_THRESHOLD:
      if self.step_idx + 1 < len(self.route):
        self.step_idx += 1
        self.reset_recompute_limits()
      else:
        cloudlog.warning("Destination reached")
        self.current_waypoint_idx += 1
        if self.current_waypoint_idx < len(self.waypoints):
          self.recompute_route()
        else:
          self.clear_route()

def main():
  # Función principal para iniciar el gestor de rutas
  pm = messaging.PubMaster(['navInstruction', 'navRoute'])
  sm = messaging.SubMaster(['liveLocationKalman', 'managerState'])

  # Lista de waypoints como tuplas de coordenadas
  waypoints = [(longitude1, latitude1), (longitude2, latitude2), ...]

  # Crear una instancia del gestor de rutas personalizado
  route_manager = CustomRouteManager(sm, pm, waypoints)

  rk = Ratekeeper(1.0)
  while True:
    route_manager.update()
    rk.keep_time()

if __name__ == "__main__":
  main()
