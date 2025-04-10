import ilo
import time

# Connexion au robot
print("Recherche du robot...")
ilo.check_robot_on_bluetooth()
my_ilo = ilo.robot(1)

# Allumage des LEDs
my_ilo.set_led_captor(True)
time.sleep(1)

# Calibration automatique
my_ilo.set_line_threshold_value()

def drive_left_side(speed):
    my_ilo.drive_single_motor_speed_front_left(speed)
    my_ilo.drive_single_motor_speed_back_left(speed)

def drive_right_side(speed):
    my_ilo.drive_single_motor_speed_front_right(speed)
    my_ilo.drive_single_motor_speed_back_right(speed)

def check_cases(line_left, line_center, line_right):
    if line_left and not line_center and not line_right:
        print("Ligne à gauche (cas 1)")
        return 1  # Ligne à gauche
    elif not line_left and line_center and not line_right:
        print("Ligne au centre (cas 2)")
        return 2  # Ligne au centre
    elif not line_left and not line_center and line_right:
        print("Ligne à droite (cas 3)")
        return 3  # Ligne à droite
    elif line_left and line_center and not line_right:
        print("Ligne à gauche et au centre (cas 4)")
        return 4  # Ligne à gauche et au centre
    elif line_left and not line_center and line_right:
        print("Ligne à gauche et à droite (cas 5)")
        return 5  # Ligne à gauche et à droite
    elif not line_left and line_center and line_right:
        print("Ligne au centre et à droite (cas 6)")
        return 6  # Ligne au centre et à droite
    elif line_left and line_center and line_right:
        print("Ligne à gauche, au centre et à droite (cas 7)")
        return 7  # Ligne à gauche, au centre et à droite
    else:
        print("Pas de ligne détectée (cas 0)")
        return 0  # Pas de ligne détectée

def action_case(case):
    if case == 1: # Ligne à gauche
        while not my_ilo.get_line_center():
            drive_left_side(5)
            drive_right_side(10)

    elif case == 2 or case == 7: # Ligne au centre et Ligne à gauche, au centre et à droite
        my_ilo.move('front', 10)



try:
    print("Début du suivi de ligne - Ctrl+C pour arrêter")
    while True:
         # Lecture des capteurs
        line_left, line_center, line_right = my_ilo.get_line()
        

except KeyboardInterrupt:
    print("\nArrêt du robot...")
    my_ilo.stop()
    print("Programme terminé")







try:
    print("Début du suivi de ligne - Ctrl+C pour arrêter")
    while True:
        # Lecture des capteurs
        line_left, line_center, line_right = my_ilo.get_line()
        
        # Logique améliorée de détection
        if line_center:
            # Cas 1: Ligne centrée - avancer tout droit
            if not line_left and not line_right:
                left_speed = - CONSTANT_SPEED
                right_speed = CONSTANT_SPEED
            # Cas 2: Ligne à droite - tourner à droite
            elif line_right:
                error = 1
                correction = KP * error
                left_speed = CONSTANT_SPEED + correction
                right_speed = CONSTANT_SPEED - correction
            # Cas 3: Ligne à gauche - tourner à gauche
            elif line_left:
                error = -1
                correction = KP * error
                left_speed = CONSTANT_SPEED + correction
                right_speed = CONSTANT_SPEED - correction
        else:
            # Cas 4: Aucun capteur - arrêt ou recherche
            left_speed = 0
            right_speed = 0
        
        # Limitation des vitesses
        left_speed = max(min(left_speed, CONSTANT_SPEED*1.5), 0)
        right_speed = max(min(right_speed, CONSTANT_SPEED*1.5), 0)
        
        print(f"Capteurs: L{line_left} C{line_center} R{line_right} | Vitesses: L{left_speed} R{right_speed}")
        
        # Commande des moteurs
        my_ilo.drive_single_motor_speed(1, ACCELERATION, int(left_speed))  # Avant gauche
        my_ilo.drive_single_motor_speed(2, ACCELERATION, int(right_speed)) # Avant droit
        my_ilo.drive_single_motor_speed(4, ACCELERATION, int(left_speed))  # Arrière gauche
        my_ilo.drive_single_motor_speed(3, ACCELERATION, int(right_speed)) # Arrière droit
        
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nArrêt du robot...")
    my_ilo.stop()
    print("Programme terminé")