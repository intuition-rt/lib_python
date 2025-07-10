import ilo
import time

""" Ilo robot """

print('Maze start')

ilo.check_robot_on_bluetooth()

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
  
  if distance_gauche <= distance_gauche_max and distance_avant > distance_avant_max and distance_droite > distance_droite_max:
    print('Mur à gauche (cas 1)')
    return 1
  elif distance_gauche > distance_gauche_max and distance_avant <= distance_avant_max and distance_droite > distance_droite_max:
    print('Mur devant (cas 2)')
    return 2
  elif distance_gauche > distance_gauche_max and distance_avant > distance_avant_max and distance_droite <= distance_droite_max:
    print('Mur à droite (cas 3)')
    return 3
  elif distance_gauche <= distance_gauche_max and distance_avant <= distance_avant_max and distance_droite > distance_droite_max:
    print('Mur à gauche et devant (cas 4)')
    return 4
  elif distance_gauche > distance_gauche_max and distance_avant <= distance_avant_max and distance_droite <= distance_droite_max:
    print('Mur à droite et devant (cas 5)')
    return 5
  elif distance_gauche <= distance_gauche_max and distance_avant > distance_avant_max and distance_droite <= distance_droite_max:
    print('Mur à gauche et à droite (cas 6)')
    return 6
  elif distance_gauche <= distance_gauche_max and distance_avant <= distance_avant_max and distance_droite <= distance_droite_max:
    print('Mur à gauche, devant et à droite (cas 7)')
    return 7
  elif distance_gauche > distance_gauche_max and distance_avant > distance_avant_max and distance_droite > distance_droite_max:
    print('Pas de mur (cas 8)')
    return 8
  else:
    print('Cas 0')
    return 0

def left_adjustment(distance_gauche):
    if distance_gauche < 40 or distance_gauche > 60:
        my_ilo.pause()
        time.sleep(0.05)

        while (True):
            distance_gauche = my_ilo.get_distance_left()

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
  
  if case == 1 or case == 6:
    print("case 1 or 6")
    my_ilo.move('front', 10)
    time.sleep(0.3)
    if my_ilo.get_distance_left() > 60:
        print("Left void detected")
        time.sleep(1.3)
        my_ilo.pause()
        time.sleep(0.05)
    #   if(my_ilo.get_distance_front() > 50):
        
        my_ilo.step('rot_trigo', True)
        my_ilo.step('front',0.75, True)

    time.sleep(0.5)



  elif case == 8: #move("front", 10)
    pass

  elif case == 3:
    pass
    # my_ilo.move('front', 10)

    # current_dist_f = my_ilo.get_distance_front()

    # if current_dist_f < 250:
    #   my_ilo.move('front', 10)
    #   new_case = check_cases(my_ilo.get_distance_left(), my_ilo.get_distance_front(), my_ilo.get_distance_right())
    #   if new_case != 3:
    #     return

    # else:
    #   if my_ilo.get_distance_back() < 100:
    #     tempo = 5
    #   else:
    #     tempo = 2
    #   for i in range(tempo):
    #     if my_ilo.get_distance_front() < 50:
    #       break
    #     else:
    #       time.sleep(0.5)
          
    #   if my_ilo.get_distance_left() > distance_gauche_max:
    #     my_ilo.pause()
    #     time.sleep(0.05)
    #     my_ilo.step('rot_trigo', True)
    #     if(my_ilo.get_distance_front() > 50):
    #       my_ilo.move('front', 10)
    #       time.sleep(0.5)
    # print("case 3")

  elif case == 2 or case == 5:
        pass
    # my_ilo.pause()
    # time.sleep(0.05)
    # my_ilo.step('rot_trigo', True)
    # if(my_ilo.get_distance_front() > 50):
    #   my_ilo.move('front', 10)
    #   time.sleep(0.5)
    #   print("case 2 or 5")

  elif case == 4:
    my_ilo.pause()
    time.sleep(0.05)
    my_ilo.step('rot_clock', True)
    if(my_ilo.get_distance_front() > 50):
      my_ilo.move('front', 10)
      time.sleep(0.5)
      print("case 4")

  elif case == 7:
    my_ilo.pause()
    time.sleep(0.05)
    my_ilo.rotation(-180, True)
    if(my_ilo.get_distance_front() > 50):
      my_ilo.move('front', 10)
      time.sleep(0.5)
    print("case 7")

while True:
  left_adjustment(my_ilo.get_distance_left())
  distance_gauche = my_ilo.get_distance_left()
  distance_avant = my_ilo.get_distance_front()
  distance_droite = my_ilo.get_distance_right()
  print("Gauche:", distance_gauche, "Avant:", distance_avant, "Droite:", distance_droite)
  
  case = check_cases(distance_gauche, distance_avant, distance_droite)
  action_case(case, distance_gauche)


