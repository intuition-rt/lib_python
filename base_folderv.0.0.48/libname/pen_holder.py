import ilo
import time

ilo.check_robot_on_wifi()

my_ilo = ilo.robot(1)

my_ilo.drive_single_motor_speed(5,50,20)
    #my_ilo.get_torque_single_motor(5)[1]
torque = 0
while (torque<300):  # add time safety (5 seconds)
    torque =  abs(my_ilo.get_torque_single_motor(5)[1])
    print(torque)
    time.sleep(0.2)
my_ilo.drive_single_motor_speed(5,50,0)
print("limite value get")
