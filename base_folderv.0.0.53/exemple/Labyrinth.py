import ilo
import time

ilo.check_robot_on_wifi()

my_ilo = ilo.robot(1)



def check_obstacle():
    while my_ilo.get_distance_front() < 60:
        my_ilo.stop
        print("ilo stops")
        while my_ilo.get_distance_front() < 60:
            my_ilo.step("rot_trigo")
            time.sleep(1.5)
            print("ilo turns")
    my_ilo.move("front", 50)
    print("ilo moves forward")


while True :
    
    if my_ilo.get_distance_front() < 60:
        my_ilo.stop()
        print("ilo stops")
        
        my_ilo.step("rot_trigo")
        print("ilo makes a rot_trigo turn")
        time.sleep(2)
        
        
    else :
        my_ilo.move("front", 5)
        print("ilo moves forward")
        
    time.sleep(0.2)
