import ilo
ilo.check_robot_on_serial()


from ilo import ilo, ConnectionType

robot = ilo.robot("Sigma", connect_with=ConnectionType.SERIAL, debug=True)
print(robot.get_distance())
