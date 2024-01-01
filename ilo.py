# This python scrip is the libery for python
# SIMON LE BERRE
# 21/08/2023
# pip install ilo
version = "0.14"
#-----------------------------------------------------------------------------

print("ilo robot library version ", version)
print("For any help or support contact us on our website, ilorobot.com ")
print(" ")

#-----------------------------------------------------------------------------
import socket,time,keyboard #,sys

#-----------------------------------------------------------------------------
'''
if 'ilo' in sys.modules:
    print ('ilo library is already imported')
else:    
    print('ilo library is importing ...')
'''    

global IP,Port,s,preview_stop,connect
IP = '192.168.4.1'
preview_stop = True
connect = False

#-------------------------------------------------------------------------
def info():
    print("Ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command")
    print("You are using the version ", version)

def list_function():
    print("info()                                        -> print info about ilorobot")
    print(" ")
    print("connection()                                  -> connection your machine to ilorobot")
    print(" ")
    print("step(direction)                               -> move by step ilorobot with selected direction during 2 seconds")
    print("                                                 direction is a string and should be (front, back, left, right, rot_trigo or rot_clock)")
    print(" ")
    print("move(direction, speed, time)                  -> move ilorobot with selected direction speed and time control")
    print("                                                 direction is a string and should be (front, back, left or right)")
    print("                                                 speed is an integer from 0 to 100 as a pourcentage ")
    print(" ")
    print("direct_contol(axial, radial, rotation, stop)) -> control ilorobot with full control ")
    print("                                                 axial, radial and roation are 3 integer from 0 to 255")
    print("                                                 value from 0 to 128 are negative, value from 128 to 255 are positve")
    print("                                                 stop is a boolean value, to don't stop after the command the robot use stop==False")                                
    print(" ")
    print("calculatrice(ilo_calcul)                      -> ilo will execute your calculus, ilo_calcul is a string")
    print("                                                 example of calcul: '3+2-1.5' ")
    print(" ")
    print("list_order(ilo_list)                          -> ilo will execute a list of displacment define my your ilo_list")
    print("                                                 example of list ['front', 'left', 'front', 'rot_trigo', 'back'] ")
    print("                                                 value of ilo_list are a string")
    print(" ")
    print("game()                                        -> control ilo using arrow or numb pad of your keyboard")
    print("                                                 avaible keyboard touch: 8,2,4,6,1,3   space = stop    esc = quit")
    print(" ")
    print("detection()                                   -> return list of state captor as [capteur_front, capteur_back, capteur_left, capteur_right]")
    print(" ")

#-----------------------------------------------------------------------------
def socket_send(msg):
    #print(msg)
    global s, IP, Port, connect
    try:
        s = socket.socket()
        s.connect((IP, Port))
        s.send(msg.encode())
        time.sleep(0.1)           #  10Hz
        return True
    except:
        print('Error of connection with ilo to send message')
        time.sleep(3)
        connect = False
        return False
    
def socket_read():
    #print(msg)
    global s, IP, Port, connect
    try:
        s = socket.socket()
        s.connect((IP, Port))
        data = str(s.recv(1024))[2:-1]
        time.sleep(0.1)           #  10Hz
        return data
    except:
        print('Error of connection with ilo to receive message')
        time.sleep(3)
        connect = False
        return False
#-----------------------------------------------------------------------------
def connection():
    # idea of improvement, be able to connect to witch ilo you want function of is name, or color
    global IP,Port,connect, preview_stop,deviceIP
    preview_stop = True
    
    if connect == True:
        print('ilo already connected')
        return None
    
    else:
        print('Connecting...')
        try:
            Port = 80
            ping = socket.socket()
            ping.connect((IP, Port))         
            deviceIP = ping.getsockname()[0]     # IP of the machine
            #print('deviceIP', deviceIP)
            msg="ilo"
            ping.send(msg.encode())
            ping.close()
    
            inform = socket.socket()
            inform.bind((deviceIP, Port)) 

            time.sleep(1)
    
            s = socket.socket() 
            msg="io"
            s.connect((IP, Port))
            s.send(msg.encode())
            print('Connected to ilo')
            
            time.sleep(1)
        except:
            print("Error connection: you have to be connect to the ilo wifi network")
            print(" --> If the disfonction continu, switch off and switch on ilo")

#-----------------------------------------------------------------------------
def stop():
    socket_send("io")

def test_connection():
    return socket_send("io")
#------------------------------------------- ---------------------------------
def step(direction):
    
    #ilo.step('front')
    
    if isinstance(direction, str) == False:
        print ('direction should be an string as front, back, left, rot_trigo, rot_clock','stop')
        return None
    
    if direction == 'front':
        socket_send("iavpx110yro")
    elif direction == 'back':
        socket_send("iavpx010yro")
    elif direction == 'left':
        socket_send("iavpxy010ro")
    elif direction == 'right':
        socket_send("iavpxy110ro")
    elif direction == 'rot_trigo':
        socket_send("iavpxyr090o")
    elif direction == 'rot_clock':
        socket_send("iavpxyr190o")
    elif direction == 'stop':
        stop()
    else:
        print('direction name is not correct')
    
#-----------------------------------------------------------------------------
def list_order(ilo_list):
    
    if isinstance(ilo_list, list) == False:
        print ('the variable should be a list, with inside string as front, back, left, rot_trigo, rot_clock')
        return None

    for i in range(len(ilo_list)):
        step(ilo_list[i])   
        
#------------------------------------------- ---------------------------------
def correction_command(list_course):
    
    #convert a list of 3 elements to a sendable string
    
    if int(list_course[0]) >= 100:
        list_course[0] = str(list_course[0])   
    elif 100 > int(list_course[0]) >= 10:
        list_course[0] = str('0') + str(list_course[0])
    elif 10 > int(list_course[0]) >= 1:
        list_course[0] = str('00') + str(list_course[0])
    else:
        list_course[0] = str('000')

    if int(list_course[1]) >= 100:
        list_course[1] = str(list_course[1])     
    elif 100 > int(list_course[1]) >= 10:
        list_course[1] = str('0') + str(list_course[1])
    elif 10  > int(list_course[1]) >= 1:
        list_course[1] = str('00') + str(list_course[1])
    else:
        list_course[1] = str('000')
        
    if int(list_course[2]) >= 100:
        list_course[2] = str(list_course[2])     
    elif 100 > int(list_course[2]) >= 10:
        list_course[2] = str('0') + str(list_course[2])
    elif 10  > int(list_course[2]) >= 1:
        list_course[2] = str('00') + str(list_course[2])
    else:
        list_course[2] = str('000')
        
    new_command = []
    str_command = str(list_course[0] + list_course[1] + list_course[2])
    new_command = "iav" + str_command +"pxyro"
    return new_command
    
def move(direction, speed):
    
    #ilo.move('front', 50, 3)
    
    #global preview_stop
    #preview_stop = True
    
    if isinstance(direction, str) == False:
        print ('direction should be an string as front, back, left, rot_trigo, rot_clock')
        return None
    if isinstance(speed, int) == False:
        print ('speed should be an integer between 0 to 100')
        return None
    if speed > 100:
        print ('speed should be an integer between 0 to 100')
        return None
    if speed < 0:
        print ('speed should be an integer between 0 to 100')
        return None

    if direction == 'front':
        command = [int((speed*1.28)+128),128,128]
    elif direction == 'back':
        command = [int(-(speed*1.28))+128,128,128]
    elif direction == 'left':
        command = [128,int((speed*1.28)+128),128]
    elif direction == 'right':
        command = [128,int(-(speed*1.28)+128),128]
    elif direction == 'rot_trigo':
        command = [128,128,int(-(speed*1.28)+128)]
    elif direction == 'rot_clock':
        command = [128,128,int((speed*1.28)+128)]
    else:
        print('direction is not correct')
        return None
    
    corrected_command = correction_command(command)
    socket_send(corrected_command)
    
def direct_control(axial, radial, rotation):

    if isinstance(axial, int) == False:
        print ('axial should be an interger')
        return None
    if axial> 255 or axial<0:
        print ('axial should be include between 0 and 255')
        return None
    if isinstance(radial, int) == False:
        print ('Radial should be an interger')
        return None
    if radial> 255 or radial<0:
        print ('Radial should be include between 0 and 255')
        return None
    if isinstance(rotation, int) == False:
        print ('rotation should be an interger')
        return None
    if rotation> 255 or rotation<0:
        print ('rotation should be include between 0 and 255')
        return None

    command = [axial, radial, rotation]
    corrected_command = correction_command(command)
    socket_send(corrected_command)
    
#-----------------------------------------------------------------------------  
def game():
 
    if test_connection() == True:
        axial_value = 128
        radial_value = 128
        rotation_value = 128
        stop()
        new_keyboard_instruction = False
        
        print('Game mode start, use keyboard arrow to control ilo')
        print("Press echap to leave the game mode")
        
        while (True):
            if keyboard.is_pressed("8"):
                new_keyboard_instruction = True
                time.sleep(0.05)
                axial_value = axial_value + 5
                if axial_value > 255:
                    axial_value = 255     
            elif keyboard.is_pressed("2"):
                new_keyboard_instruction = True
                time.sleep(0.05)
                axial_value = axial_value - 5
                if axial_value < 1:
                    axial_value = 0
            elif keyboard.is_pressed("6"):
                new_keyboard_instruction = True
                time.sleep(0.05)
                radial_value = radial_value + 5
                if radial_value > 255:
                    radial_value = 255  
            elif keyboard.is_pressed("4"):
                new_keyboard_instruction = True
                time.sleep(0.05)
                radial_value = radial_value - 5
                if radial_value < 1:
                    radial_value = 0
            elif keyboard.is_pressed("3"):
                new_keyboard_instruction = True
                time.sleep(0.05)
                rotation_value = rotation_value + 5
                if rotation_value > 255:
                    rotation_value = 255  
            elif keyboard.is_pressed("1"):
                new_keyboard_instruction = True
                time.sleep(0.05)
                rotation_value = rotation_value - 5
                if rotation_value < 1:
                    rotation_value = 0  
            elif keyboard.is_pressed("space"):
                stop
                axial_value = 128
                radial_value = 128
                rotation_value = 128
            elif keyboard.is_pressed("esc"):
                stop()
                break
            
            if new_keyboard_instruction == True:
                direct_control(axial_value, radial_value, rotation_value)
                new_keyboard_instruction = False
    else:
        print("You have to be connected to ILO before play with it, use ilo.connection()")

#-----------------------------------------------------------------------------        

clear_left = 0
clear_middle =0
clear_right = 0

def get_color_clear(display):
    try:
        socket_send("i0o")
        global s
        data = str(s.recv(1024))[2:-1]
        clear_left   = int(data[data.find('l')+1 : data.find('m')])   
        clear_middle = int(data[data.find('m')+1 : data.find('r')])
        clear_right  = int(data[data.find('r')+1 : data.find('o')])
        
        if (clear_left > 100):
            clear_left = 100
        
        if (clear_middle > 100):
            clear_middle = 100
            
        if (clear_right > 100):
            clear_right = 100

        if (clear_left < 0):
            clear_left = 0
        
        if (clear_middle < 0):
            clear_middle = 0
            
        if (clear_right < 0):
            clear_right = 0
            
        if (display ==  True):
            print(clear_left, clear_middle, clear_right)
            
        return clear_left, clear_middle, clear_right
        #make a test of type of clear value return
        
    except:
        return -1, -1, -1  
    
def get_color_rgb(display):
    try:
        socket_send("i1o")
        global s
        data = str(s.recv(1024))[1:]
        if (display ==  True):
            print("Color under ilo is : ", data)
        red_color   = data[data.find('r')+1 : data.find('g')]   
        green_color = data[data.find('g')+1 : data.find('b')]
        blue_color  = data[data.find('b')+1 : data.find('o')]
        return red_color, green_color, blue_color
    
    except:
            return -1, -1, -1 
        
def get_distance(display):
    socket_send("i2o")
    global s
    data = str(s.recv(1024))[1:]
    if (display ==  True):
        print("Distance around ilo is : ", data)
    front = 10
    right = 50
    back  = 30
    left  = 12
    return front, right, back, left

def get_angle(display):
    socket_send("i3o")
    global s
    data = str(s.recv(1024))[1:]
    if (display ==  True):
        print("Distance around ilo is : ", data)
    roll  = 10
    pitch = 50
    yaw   = 30
    return roll, pitch, yaw
    
def reset_angle():
    # could be angle per angle, with angle parameter ("roll", "pitch", "yaw")
    socket_send("i4o")

def get_battery_info(display):
    socket_send("i5o")
    global s
    data = str(s.recv(1024))[1:]
    if (display ==  True):
        print("Info ilo's battery is : ", data)  # arrangle the display form
    status = False #change
    pourcentage = 96 #change
    return status, pourcentage
    
def get_led_color(display):
    socket_send("i6o")
    global s
    data = str(s.recv(1024))[1:]
    if (display ==  True):
        print("Distance around ilo is : ", data)
    red_led   = 123
    green_led = 50
    blue_led  = 10
    return red_led, green_led, blue_led

def set_led_color(red,green,blue):
    msg = "i7r"+str(red)+"g"+str(green)+"b"+str(blue)+"o"
    socket_send(msg)

#other method are no yet implemented on the robot

def get_acceleration():
    pass

def set_acceleration(acc):
    # make integer test and test min and max value
    msg = "i8"+str(acc)+"o"
    socket_send(msg)

def get_vmax():
    pass

def set_vmax(vmax):
    pass

def set_autonous_mode():
    pass
        
def led_bottom_ON():
    pass

def led_bottom_OFF():
    pass

def control_single_motor_front_left(pourcentage):  # de -100 à 100
    if isinstance(pourcentage, int) == False:
        print ('value should be an integer between -100 to 100')
    pass

def control_single_motor_front_right(pourcentage):
    pass

def control_single_motor_back_left(pourcentage):
    pass

def control_single_motor_back_right(pourcentage):
    pass

def free_motor():
    #to disconnected power on engine
    pass
    
def set_mode_motor():
    #between positio or wheel mode
    pass