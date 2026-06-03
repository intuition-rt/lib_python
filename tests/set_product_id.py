import ilo
from ilo import ConnectionType
from ilo.discovery import get_all_candidates

ilo.check_robot_on_serial()

n = get_all_candidates()[0]
robot = ilo.robot(n.name, connect_with=ConnectionType.SERIAL, debug=False)

# PRODUCT_ID = "12345"
robot.set_debug_state(True)
# print(robot._send_msg(f"<151s{PRODUCT_ID}>"))
