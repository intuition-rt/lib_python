import ilo, time

ilo.connection()
print('ilo est connecte')
ilo.stop()


print('test rot')

ilo.move("rot_trigo", 36)
time.sleep(1)
ilo.stop()

time.sleep(1)
ilo.move("rot_trigo", 36)
time.sleep(1)
ilo.stop()

time.sleep(1)
ilo.move("rot_clock", 36)
time.sleep(1)
ilo.stop()

time.sleep(1)
ilo.move("rot_clock", 36)
time.sleep(1)
ilo.stop()




'''

print('test right / left')

ilo.move("right", 45)
time.sleep(1)
ilo.stop()

time.sleep(1)
ilo.move("right", 45)
time.sleep(1)
ilo.stop()

time.sleep(1)
ilo.move("left", 45)
time.sleep(1)
ilo.stop()

time.sleep(1)
ilo.move("left", 45)
time.sleep(1)
ilo.stop()

'''

'''

print('test front / back')

ilo.move("back", 45)
time.sleep(1)
ilo.stop()
time.sleep(1)
ilo.move("back", 45)
time.sleep(1)
ilo.stop()
time.sleep(1)
ilo.move("front", 45)
time.sleep(1)
ilo.stop()
time.sleep(1)
ilo.move("front", 45)
time.sleep(1)
ilo.stop()

'''