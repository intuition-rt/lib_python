from functools import wraps, singledispatch

from .ilo import (
    robot,
    info,
    list_function,
    check_robot_on_wifi,
    check_robot_on_serial,
    check_robot_on_bluetooth,
    ConnectionType
)

__all__ = (
    'robot',
    'info', 
    'list_function',
    'check_robot_on_wifi',
    'check_robot_on_serial',
    'check_robot_on_bluetooth',
    'ConnectionType'
)
