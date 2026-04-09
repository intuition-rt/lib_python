import ilo

ilo.check_robot_on_bluetooth()

robot = ilo.robot("Sigma")
robot.print_diagnostics()
