import ilo

ilo.check_robot_on_bluetooth()
ilo.check_robot_on_serial()
ilo.check_robot_on_wifi()

ilo.check_robot_on_wifi(ap_mode=False)


from ilo import ilo
print(ilo._tab_IP, ilo._tab_ADDRESS, ilo._tab_PORT)

robot = ilo.robot("SGAKQ")
robot.step("front")
