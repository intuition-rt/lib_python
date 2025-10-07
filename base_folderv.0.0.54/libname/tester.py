import ilo
import time

ilo.check_robot_on_bluetooth()

# check_robot_on_wifi() # dont forget to be connected to the AP of the robot

my_ilo = ilo.robot(1)


time.sleep(2)

my_ilo = ilo.robot(1)
# move front en checkant distance
# quand devant obstacle il s'arrete
# rot 270 trigo
# avance C temps/distance
# step left
# lecture carte couleur et met à jour ses leds
# tourne 90 degres clock
# slide right C temps/distance (same as etape précendente)
# avance jusqua ce que l'obstacle derriere lui est à X distance