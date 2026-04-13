import ilo
import time

# ilo.check_robot_on_bluetooth()
# ilo.check_robot_on_wifi(ap_mode=False)
ilo.check_robot_on_serial()

from ilo import ConnectionType

robot = ilo.robot("Sigma", connect_with=ConnectionType.SERIAL, debug=True)
robot2 = ilo.robot("Sigma", connect_with=ConnectionType.SERIAL, debug=True)


# <56wHELLOd100/3>
while True:
    try:
        msg = input()
    except KeyboardInterrupt:
        break

    robot._send_msg(msg)
    time.sleep(2)
