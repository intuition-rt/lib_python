from .copy_to_clipboard import copy_to_clipboard
from .discovery import (
    check_robot_on_wifi,
    check_robot_on_serial,
    check_robot_on_bluetooth,
    ConnectionType
)

from .facade import robot
from .help import info, list_function

__version__ = "0.1.0"

print("ilo robot library version: ", __version__)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")

copy_to_clipboard("""ilo.check_robot_on_bluetooth()""")

__all__ = (
    'robot',
    'info', 
    'list_function',
    'check_robot_on_wifi',
    'check_robot_on_serial',
    'check_robot_on_bluetooth',
    'ConnectionType'
)
