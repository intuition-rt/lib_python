from ilo import *
from time import time, sleep

check_robot_on_wifi()

my_ilo = robot(1)

my_ilo.send_trame_s("accessory_angle")

start_time = time()  # Capture le temps de départ
duration = 10        # Durée de la boucle en secondes

while time() - start_time < duration:
    my_ilo.potard_value = round(((200/1023) * my_ilo.potard_value)-100) # adaptation de 0 à 1023 pour correspondre à -7000 à 7000
    if my_ilo.potard_value < -100:
        my_ilo.potard_value = -100
    if my_ilo.potard_value > 100:
        my_ilo.potard_value = -100
    my_ilo.drive_single_motor_speed(1, my_ilo.potard_value)
    sleep(0.1)

my_ilo.del_trame_s() # À la fin du temps déclaré suppression de la trame_s
my_ilo.stop()