# This python scrip is the libery for python
# SIMON LE BERRE
# 26/04/2024
# pip install ilo
version = "0.20"
#-----------------------------------------------------------------------------

print("ilo robot library version ", version)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")

#-----------------------------------------------------------------------------
import socket, time, keyboard #,sys

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
    """
    Print info about ilorobot
    :return:
    """
    print("ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command line")
    print("You are using the version ", version)

def list_function():
    print("info()                                        -> print info about ilorobot")
    print(" ")
    print("connection()                                  -> connection your machine to ilorobot")
    print(" ")
    print("stop()                                        -> stop the robot")
    print("")
    print("step(direction)                               -> move by step ilorobot with selected direction during 2 seconds")
    print("                                                 direction is a string and should be (front, back, left, right, rot_trigo or rot_clock)")
    print(" ")
    print("move(direction, speed)                        -> move ilorobot with selected direction speed and time control")
    print("                                                 direction is a string and should be (front, back, left or right)")
    print("                                                 speed is an integer from 0 to 100 as a pourcentage ")
    print(" ")
    print("direct_contol(axial, radial, rotation)        -> control ilorobot with full control ")
    print("                                                 axial, radial and roation are 3 integer from 0 to 255")
    print("                                                 value from 0 to 128 are negative, value from 128 to 255 are positve")
    print(" ")
    print("list_order(ilo_list)                          -> ilo will execute a list of successive displacment define in ilo_list")
    print("                                                 example of list ['front', 'left', 'front', 'rot_trigo', 'back'] ")
    print("                                                 value of ilo_list are a string")
    print(" ")
    print("game()                                        -> control ilo using arrow or numb pad of your keyboard")
    print("                                                 available keyboard touch: 8,2,4,6,1,3   space = stop    esc = quit")
    print("")
    print("get_color_clear                               -> return lightness under the robot with list form as [light_left, light_middle, light_right]")
    print("")
    print("get_color_rgb                                 -> return RGB color under the robot with list form as [color_left, color_middle, color_right]")
    print("")
    print("set_led_color(red,green,blue)                 -> set ilorobot leds colors")
    print("                                                 red, green and blue are integers and must be between 0 and 255")
    print("")
    print("set_led_shape(value)                          -> set ilorobot leds shape")
    print("                                                 value is an integer and must be between 0 and 19")
    print("                                                 0 = smiley      1 = play      2 = back arrow      3 = pause")
    print("                                                 4 = left arrow  5 = stop      6 = right arrow     7 = rot_trigo arrow")
    print("                                                 4 = left arrow  5 = stop      6 = right arrow     7 = rot_trigo arrow")
    print("")
    print("set_led_anim(value, repetition)               -> set ilorobot leds animations")
    print("")
    print("get_distance                                  -> return distance around the robot with list from as [front, right, back, left]")
    print("")
    print("get_angle                                     -> return angle of the robot with list from as [roll, pitch, yaw]")
    print("")
    print("reset_angle                                   -> reset the angle of the robot")
    print("")
    print("get_battery_info                              -> return info about the battery of the robot with list from as [battery status, battery pourcentage]")
    print("")
    print("test_connection()                             -> stop the robot if it is properly connected")

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
    """
    Connection your machine to ilorobot
    :return:
    """
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
    """
    Stop the robot
    :return:
    """
    socket_send("io")

def test_connection():
    try:
        return socket_send("io")
    except:
        print("Error connection: you have to be connect to the robot")
        return False

#------------------------------------------- ---------------------------------
def step(direction):
    """
    Move by step ilorobot with selected direction during 2 seconds
    :param direction:
    :return: Is a string and should be (front, back, left, right, rot_trigo or rot_clock)
    """
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
    """
    ilo will execute a list of successive displacment define in ilo_list
    :param ilo_list:
    :return: example : ['front', 'left', 'front', 'rot_trigo', 'back'] (value of ilo_list are a string)
    """
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
    """
    Move ilorobot with selected direction, speed and time control
    :param direction: is a string and should be (front, back, left, right, rot_trigo or rot_clock)
    :param speed: is an integer from 0 to 100, as a pourcentage
    :return:
    """

    #ilo.move('front', 50)

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
    """
    Control ilorobot with full control
    :param axial, radial, rotation: is an integer from 0 to 255. Value from 0 to 128 are negative and value from 128 to 255 are positive
    :return:
    """

    if isinstance(axial, int) == False:
        print ('axial should be an integer')
        return None
    if axial> 255 or axial<0:
        print ('axial should be include between 0 and 255')
        return None
    if isinstance(radial, int) == False:
        print ('Radial should be an integer')
        return None
    if radial> 255 or radial<0:
        print ('Radial should be include between 0 and 255')
        return None
    if isinstance(rotation, int) == False:
        print ('rotation should be an integer')
        return None
    if rotation> 255 or rotation<0:
        print ('rotation should be include between 0 and 255')
        return None

    command = [axial, radial, rotation]
    corrected_command = correction_command(command)
    socket_send(corrected_command)

#-----------------------------------------------------------------------------
def game():
    """
    Control ilo using arrow or numb pad of your keyboard. \n
    Available keyboard touch: 8,2,4,6,1,3 | space = stop | esc = quit
    :return:
    """

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

def classification(trame):
    try: 
        print('trame envoyée: ', trame)
    
        global s
        socket_send(trame)
        
        data = str(s.recv(1024))[1:]
        print ('data reçu:   ', data)
        print ('data indice: ', data[2])
        
        if int(data[2]) == 0:
            clear_left   = int(data[data.find('l')+1 : data.find('m')])
            clear_middle = int(data[data.find('m')+1 : data.find('r')])
            clear_right  = int(data[data.find('r')+1 : data.find('o')])
            return clear_left, clear_middle, clear_right
        
        if int(data[2]) == 1:
            red_color   = data[data.find('r')+1 : data.find('g')]
            green_color = data[data.find('g')+1 : data.find('b')]
            blue_color  = data[data.find('b')+1 : data.find('o')]
            return red_color, green_color, blue_color
        
        if int(data[2]) == 2:
            front = data[data.find('f')+1 : data.find('r')]
            right = data[data.find('r')+1 : data.find('b')]
            back  = data[data.find('b')+1 : data.find('l')]
            left  = data[data.find('l')+1 : data.find('o')]
            return front, right, back, left
            
        if int(data[2]) == 3:
            roll  = int(data[data.find('r')+1 : data.find('p')])
            pitch = int(data[data.find('p')+1 : data.find('y')])
            yaw   = int(data[data.find('y')+1 : data.find('o')])
            return roll, pitch, yaw
            
        if int(data[2]) == 4:
            status_battery      = int(data[data.find('s')+1 : data.find('p')])
            pourcentage_battery = int(data[data.find('p')+1 : data.find('o')]) 
            return status_battery, pourcentage_battery
        
        if int(data[2]) == 5:
            red_led   = int(data[data.find('r')+1 : data.find('g')])
            green_led = int(data[data.find('g')+1 : data.find('b')])
            blue_led  = int(data[data.find('b')+1 : data.find('o')])
            return red_led, green_led, blue_led
        
        if int(data[2]) == 6:
            acc_motor  = int(data[data.find('a')+1 : data.find('o')])
            return acc_motor
        
        
    
    except:
        print('Communication Err: classification')
        return -1
    
        
def get_color_clear():
    return classification("i0o")

def get_color_clear_left():
    return get_color_clear()[0]

def get_color_clear_middle():
    return get_color_clear()[1]

def get_color_clear_right():
    return get_color_clear()[2]

def get_color_rgb():
    return classification("i1o")

def get_distance():
    return classification("i2o")

def get_angle():
    return classification("i30o")

def reset_angle():
    socket_send("i31o")

def get_battery_info():
    return classification("i4o")

def get_led_color():
    return classification("i5o")

def set_led_color(r, g, b):
    # make integer test and test min and max value
    msg = "i51r"+str(r)+"g"+str(g)+"b"+str(b)+"o"
    socket_send(msg)
    
def set_led_shape(val):
    msg = "i52"+str(val)+"o"
    socket_send(msg)
    
def set_led_anim(val, rep):
    msg = "i53v"+str(val)+"r"+str(rep)+"o"
    socket_send(msg)
    
'''
def set_led_color_rgb(red,green,blue):

    if isinstance(red, int) == False:
        print ('red should be an integer')
        return None
    if red> 255 or red<0:
        print('red should be include between 0 and 255')
        return None
    if isinstance(green, int) == False:
        print('green should be an integer')
        return None
    if green> 255 or green<0:
        print('green should be include between 0 and 255')
        return None
    if isinstance(blue, int) == False:
        print('blue should be an integer')
        return None
    if blue> 255 or blue<0:
        print('blue should be include between 0 and 255')
        return None
    
    msg = "i7r"+str(red)+"g"+str(green)+"b"+str(blue)+"o"
    socket_send(msg)

'''
def get_acceleration():
    return classification("i6o")

def set_acceleration(acc):
    # make integer test and test min and max value
    msg = "i61a"+str(acc)+"o"
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
