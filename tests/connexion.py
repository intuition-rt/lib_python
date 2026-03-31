import ilo

ilo.check_robot_on_bluetooth()
ilo.check_robot_on_serial()
ilo.check_robot_on_wifi()

from ilo import ilo, ConnectionType

robot = ilo.robot("Sigma", connect_with=ConnectionType.BLUETOOTH)
robot2 = ilo.robot("Sigma", connect_with=ConnectionType.SERIAL)

robot.set_led_word("slide", "robot", 300)
robot2.step('front')
