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
        route_manager_instance.recompute_countdown = max(0, route_manager_instance.recompute_countdown - 1)
