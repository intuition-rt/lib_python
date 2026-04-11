from .discovery import ConnectionType, find_in_candidates
from .robot import Robot


def robot(
    name: str | int,
    connect_with: ConnectionType | None = None,
    debug=False,
) -> Robot:
    if isinstance(name, int):
        raise ValueError("La création de robot par ID n'est plus possible.")

    candidate = find_in_candidates(name, use_connection_type=connect_with)
    if candidate is None:
        raise ValueError("Aucun robot correspondant")

    robot = Robot._robots_connected.get(candidate.address)
    if robot is not None:
        return robot

    return Robot(candidate, debug)
