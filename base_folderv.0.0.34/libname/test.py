import ilo
import time

ilo_run = ilo.robot(2)

#couleur
'''
1. front
2. gauche
3. front
4. droite
5. 360
6. front
'''
delay = 1.5

while True :

    ilo_run.set_led_color(255,165,0)
    ilo_run.step("front")
    time.sleep(delay)
    ilo_run.pause()
    
    ilo_run.set_led_color(65,105,225)
    ilo_run.step("left")
    time.sleep(delay)
    ilo_run.pause()
    
    ilo_run.set_led_color(255,165,0)
    ilo_run.step("front")
    time.sleep(delay)
    ilo_run.pause()
    
    ilo_run.set_led_color(255,0,255)
    ilo_run.step("right")
    time.sleep(delay)
    ilo_run.pause()
    
    ilo_run.set_led_color(255,165,0)
    ilo_run.step("front")
    time.sleep(delay)
    
    ilo_run.set_led_color(0,255,10)
    ilo_run.move("rot_trigo", 40)
    ilo_run.set_led_shape(7)
    time.sleep(10)
    ilo_run.pause()
    ilo_run.stop()
    
    ilo_run.set_led_color(255,255,255)
    ilo_run.set_led_anim(1)

