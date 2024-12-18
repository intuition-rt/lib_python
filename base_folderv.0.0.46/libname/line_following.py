# Version moi
'''
from ilo import *
from time import sleep

check_robot_on_WiFi()

my_ilo = robot(1)

# my_ilo.set_line_treshold_value(10)
# my_ilo.set_led_captor(False)

while True:
    my_ilo.line_left = 0
    my_ilo.line_center = 0
    my_ilo.line_right = 0

    my_ilo.get_line()
    while my_ilo.line_left == 0 and my_ilo.line_center == 0 and my_ilo.line_right == 0:
        time.sleep(0.01)

    if my_ilo.line_left == 0:
        my_ilo.direct_control(50, 128, 128, 106)
        time.sleep(0.5)
        my_ilo.pause()

    elif my_ilo.line_right == 0:
        my_ilo.direct_control(50, 128, 128, 150)
        time.sleep(0.5)
        my_ilo.pause()

    elif my_ilo.line_center == 0:
        my_ilo.direct_control(50, 150, 128, 128)
        time.sleep(0.5)
        my_ilo.pause()

    else :
        my_ilo.stop()

    time.sleep(0.01)
'''


# Version chat gpt
'''  
import time
import ilo

def follow_line(ilo):
    """
    Fonction pour suivre une ligne noire.
    """
    while True:
        # Obtenir les valeurs des capteurs de ligne
        ilo.web_socket_send("<11l>")  # Demande les valeurs de 'clear_left', 'clear_center', 'clear_right'
        time.sleep(0.1)  # Attendre un peu pour que le robot ait le temps de répondre
        
        # Lire les valeurs des capteurs
        left = ilo.clear_left
        center = ilo.clear_center
        right = ilo.clear_right
        threshold = ilo.line_threshold_value
        
        print(f"Left: {left}, Center: {center}, Right: {right}, Threshold: {threshold}")

        # Analyser la ligne en fonction du seuil
        line_left = 1 if left > threshold else 0
        line_center = 1 if center > threshold else 0
        line_right = 1 if right > threshold else 0

        # Logique pour suivre la ligne
        if line_center == 1:
            # Avancer tout droit
            ilo.move('front', speed=50, acc=100)
        elif line_left == 1:
            # Tourner à gauche
            ilo.move('left', speed=30, acc=100)
        elif line_right == 1:
            # Tourner à droite
            ilo.move('right', speed=30, acc=100)
        else:
            # Si aucune ligne détectée, arrêter ou effectuer une correction
            ilo.stop()

        # Pause pour éviter une surcharge du CPU
        time.sleep(0.05)

if __name__ == "__main__":
    # Initialisation du robot avec l'ID correspondant
    ilo.check_robot_on_WiFi()

    my_ilo = ilo.robot(1)

    my_ilo.set_led_captor(True)

    # Vérifier la connexion
    if my_ilo.test_connection():
        print("Connexion établie avec le robot.")
        try:
            follow_line(my_ilo)
        except KeyboardInterrupt:
            print("Arrêt du suivi de ligne.")
            my_ilo.stop()
        finally:
            my_ilo.stop_reception()
    else:
        print("Échec de la connexion au robot.")
'''
    