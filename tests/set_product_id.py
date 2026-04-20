import ilo
from ilo import ConnectionType

ilo.check_robot_on_serial()
robot = ilo.robot("default", connect_with=ConnectionType.BLUETOOTH, debug=False)

PRODUCT_ID = "12345"
print(robot._send_msg(f"<151s{PRODUCT_ID}>"))
