import ilo

ilo.check_robot_on_bluetooth()
ilo.check_robot_on_serial()
ilo.check_robot_on_wifi()
# ilo.check_robot_on_wifi(ap_mode=False)


from ilo import ilo

robot = ilo.robot("Sigma")
robot2 = ilo.robot("Sigma")
robot = ilo.robot("Sigma")

robot2.set_led_word("slide", "robot", 300)
robot.step("front")
robot2.step("front")
robot.set_led_word("slide", "robot", 300)
