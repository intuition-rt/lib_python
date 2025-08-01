import ilo
import time

""" Ilo robot """

print('Maze start')

ilo.check_robot_on_wifi()

my_ilo = ilo.robot(1)

my_ilo.set_tempo_pos(0)
my_ilo.set_acc_motor(60)

# distance en mm
distance_gauche_max = 100
distance_avant_max = 60 # distance plus faible car il n'y a pas l'offset des roues
distance_droite_max = 100

def check_cases(distance_gauche, distance_avant, distance_droite):
  global distance_gauche_max
  global distance_avant_max
  global distance_droite_max
  
  if distance_gauche <= distance_gauche_max and distance_avant > distance_avant_max:
    print('Mur à gauche (cas 1)')
    return 1

  elif distance_gauche <= distance_gauche_max and distance_avant <= distance_avant_max :
    print('Mur devant et  gauche(cas 2)')
    return 2

  elif distance_gauche <= distance_gauche_max and distance_avant <= distance_avant_max and distance_droite <= distance_droite_max:
    print('cul de sac (cas 3)')
    return 3

  else:
    print('Cas 0')
    return 0

def left_adjustment(distance_gauche):
    if distance_gauche < 40 or distance_gauche > 60:  # pas la bonne distance du mur
        my_ilo.pause()
        time.sleep(0.05)

        while (True):
            distance_gauche = my_ilo.get_distance_left()
            
            if distance_gauche > 200:
                break
            if distance_gauche > 100:
                my_ilo.move('left', 10)
            elif distance_gauche > 60:
                my_ilo.move('left', 3)
            elif distance_gauche < 40:
                my_ilo.move('right', 3)
            else:
                break
            time.sleep(0.05)
        
  

def action_case(case, dist_gauche):
  
  if case == 1:
    my_ilo.set_led_shape("11")
    print("case 1 ")
    my_ilo.move('front', 10)
    time.sleep(0.3)

  elif case == 2:
    my_ilo.set_led_shape("12")
    my_ilo.pause()
    time.sleep(0.05)
    my_ilo.step('rot_clock', True)
    if(my_ilo.get_distance_front() > 50):
      my_ilo.move('front', 10)
      time.sleep(0.5)
      print("case 4")

  elif case == 3:
    my_ilo.set_led_shape("13")
    my_ilo.pause()
    time.sleep(0.05)
    my_ilo.rotation(-180, True)
    if(my_ilo.get_distance_front() > 50):
      my_ilo.move('front', 10)
      time.sleep(0.5)
    print("case 7")
    
  elif case == 0:
        my_ilo.set_led_shape("10")
        my_ilo.pause()
        time.sleep(1)
        my_ilo.move('front', 10)
        time.sleep(3)
        my_ilo.step('rot_trigo', True)
        my_ilo.move('front', 10)
        time.sleep(3)
        
        

while True:
  left_adjustment(my_ilo.get_distance_left())
  distance_gauche = my_ilo.get_distance_left()
  distance_avant = my_ilo.get_distance_front()
  distance_droite = my_ilo.get_distance_right()
  print("Gauche:", distance_gauche, "Avant:", distance_avant, "Droite:", distance_droite)
  
  case = check_cases(distance_gauche, distance_avant, distance_droite)
  action_case(case, distance_gauche)
  


