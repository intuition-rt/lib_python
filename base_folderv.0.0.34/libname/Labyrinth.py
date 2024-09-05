import ilo
import time

my_ilo = ilo.robot(2)

def check_obstacle():
    while my_ilo.get_distance_front() < 60:
        my_ilo.stop
        print("je me stop")
        while my_ilo.get_distance_front() < 60:
            my_ilo.step("rot_trigo")
            time.sleep(1.5)
            print("je tourne")
    my_ilo.move("front", 50)
    print("j'avance")


while True :
    
    if my_ilo.get_distance_front() <= 60:
        my_ilo.stop()
        print("stop")
        
        my_ilo.step("rot_trigo")
        print("rot_trigo")
        time.sleep(2)
        
        
    else :
        my_ilo.move("front", 5)
        print("front")
        
    time.sleep(0.2)