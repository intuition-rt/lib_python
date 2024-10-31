import ilo
import time

ilo.check_robot_on_WiFi()

# code gif 3 robots

ilo1 = ilo.robot(1)
ilo2 = ilo.robot(2)
ilo3 = ilo.robot(3)

ilo1.direct_control(50, 170, 128, 128)
ilo2.direct_control(50, 110, 96, 128)
ilo3.direct_control(50, 110, 160, 128)

time.sleep(1.5)

ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(0.5)
ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(1)

ilo2.direct_control(50, 170, 128, 128)
ilo3.direct_control(50, 110, 96, 128)
ilo1.direct_control(50, 110, 160, 128)

time.sleep(1.5)

ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(0.5)
ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(1)

ilo3.direct_control(50, 170, 128, 128)
ilo1.direct_control(50, 110, 96, 128)
ilo2.direct_control(50, 110, 160, 128)

time.sleep(1.5)

ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(0.5)
ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(1)

ilo1.direct_control(50, 128, 160, 100)
ilo2.direct_control(50, 128, 160, 100)
ilo3.direct_control(50, 128, 160, 100)

time.sleep(5)

ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(0.5)
ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(1)

ilo1.direct_control(200, 50, 128, 100)
ilo2.direct_control(200, 50, 128, 100)
ilo3.direct_control(200, 50, 128, 100)

time.sleep(2)

ilo1.pause()
ilo2.pause()
ilo3.pause()
time.sleep(5)
ilo1.stop()
ilo2.stop()
ilo3.stop()

'''
my_ilo = ilo.robot(1)

my_ilo.direct_control(50, 170, 128, 128)

time.sleep(0.5)

my_ilo.direct_control(50, 128, 128, 155)

time.sleep(1)

my_ilo.direct_control(50, 170, 128, 128)

time.sleep(2.3)

my_ilo.direct_control(50, 128, 128, 101)

time.sleep(1.9)

my_ilo.direct_control(50, 170, 128, 128)

time.sleep(2.4)

my_ilo.direct_control(50, 128, 128, 155)

time.sleep(0.9)

my_ilo.direct_control(50, 170, 128, 128)

time.sleep(2.5)

my_ilo.pause()

'''

# my_ilo.direct_control(50, 128, 128, 140)

# time.sleep(2)

# my_ilo.pause()

# ilo_run = ilo.robot(2)

#couleur
'''
1. front
2. gauche
3. front
4. droite
5. 360
6. front
'''
# delay = 1.5

# while True :

#     ilo_run.set_led_color(255,165,0)
#     ilo_run.step("front")
#     time.sleep(delay)
#     ilo_run.pause()
    
#     ilo_run.set_led_color(65,105,225)
#     ilo_run.step("left")
#     time.sleep(delay)
#     ilo_run.pause()
    
#     ilo_run.set_led_color(255,165,0)
#     ilo_run.step("front")
#     time.sleep(delay)
#     ilo_run.pause()
    
#     ilo_run.set_led_color(255,0,255)
#     ilo_run.step("right")
#     time.sleep(delay)
#     ilo_run.pause()
    
#     ilo_run.set_led_color(255,165,0)
#     ilo_run.step("front")
#     time.sleep(delay)
    
#     ilo_run.set_led_color(0,255,10)
#     ilo_run.move("rot_trigo", 40)
#     ilo_run.set_led_shape(7)
#     time.sleep(10)
#     ilo_run.pause()
#     ilo_run.stop()
    
#     ilo_run.set_led_color(255,255,255)
#     ilo_run.set_led_anim(1)

