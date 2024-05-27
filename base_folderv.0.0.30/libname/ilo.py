# This python scrip is the library for using the robot ilo with python command on WiFi
# INTUITION ROBOTIQUE ET TECHNOLOGIES ALL RIGHT RESERVED
# 27/05/2024
# code work with 1.2.7 version of c++
#-----------------------------------------------------------------------------
version = "0.31"
print("ilo robot library version ", version)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")

#-----------------------------------------------------------------------------
import socket, time, keyboard, subprocess, platform
from prettytable import PrettyTable

tab_IP = []

#-------------------------------------------------------------------------
def info():
    """
    Print info about ilorobot
    :return:
    """
    print("ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command line")
    print("You are using the version ", version)
#-------------------------------------------------------------------------
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
    print("get_color_rgb                                 -> return RGB color under the robot with list form as [color_left, color_middle, color_right]")
    print("")
    print("get_color_clear                               -> return lightness under the robot with list from as [light_left, light_middle, light_right]")
    print("")
    print("get_line                                      -> detects whether the robot is on a line or not and return a list from as [line_left, line_center, line_right]")
    print("")
    print("set_line_threshold_value                      -> set the threshold value for the line detector")
    print("")
    print("get_distance                                  -> return distance around the robot with list from as [front, right, back, left]")
    print("")
    print("get_angle                                     -> return angle of the robot with list from as [roll, pitch, yaw]")
    print("")
    print("reset_angle                                   -> reset the angle of the robot")
    print("")
    print("get_imu                                       -> return from as ")
    print("")
    print("get_battery                                   -> return info about the battery of the robot with list from as [battery status, battery pourcentage]")
    print("")
    print("get_led_color                                 -> ")
    print("")
    print("set_led_color(red,green,blue)                 -> set ilorobot leds colors")
    print("                                                 red, green and blue are integers and must be between 0 and 255")
    print("")
    print("set_led_shape(value)                          -> set ilorobot leds shape")
    print("                                                 value is an integer and must be between 0 and 19")
    print("                                                 0 = smiley          1 = play      2 = back arrow      3 = pause")
    print("                                                 4 = left arrow      5 = stop      6 = right arrow     7 = rot_trigo arrow")
    print("                                                 8 = front arrow     9 = rot_clock arrow        10 to 19 = number 0 to 9")
    print("")
    print("set_led_anim(value, repetition)               -> set ilorobot leds animations")
    print("                                                 value is an integer and must be between 0 and 9")
    print("                                                 repetition is an integer and represents the number of times the animation will loop")
    print("                                                 0 = waving          1 = cercle rotation      2 =      3 = cercle stars")
    # print("                                                 4 =       5 =                  6 =      7 = ")
    # print("                                                 8 =      9 =     ")
    print("")
    print("set_led_captor(bool)                          -> turns on/off the lights under the robot")
    print("")
    print("get_acc_motor()                               -> return info about the acceleration of the robot")
    print("")
    print("set_acc_motor(val)                            -> set the acceleration of ilo")
    print("                                                 val is an integer")
    print("")
    print("drive_single_motor(id, value)                 -> control only one motor at a time")
    print("                                                 id is a integer and must be between 0 and 255")
    print("                                                 value is a integer and must be between -7000 and 7000")
    print("")
    print("set_autonomous_mode(number)                   -> launches the robot in autonomous mode")
    print("                                                 number is an integer and must be between 0 and 5")
    print("                                                 1 = labyrinth          2 = color with displacement      3 = line tracking")
    print("                                                 4 = IMU water mode     5 = distance sensor led")
    print("test_connection()                             -> stop the robot if it is properly connected")
#-------------------------------------------------------------------------
def socket_send(msg, IP, Port):
    #print(msg)
    global s
    try:
        s = socket.socket()
        s.connect((IP, Port))
        s.send(msg.encode())
        #deviceIP = s.getsockname()[0]     # IP of the machine
        #print('device_control_IP', deviceIP)
        time.sleep(0.1)           #  10Hz
        return True
    except:
        print('Error of connection with ilo to send message')
        return False
#-------------------------------------------------------------------------
def socket_read(IP, Port):
    #print(msg)
    global s
    try:
        # s.connect((IP, Port))
        s.bind(IP, Port)
        s.listen()
        conn, addr = s.accept()

        data = str(conn.recv(1024))[1:]
    
        print(data)
        time.sleep(0.05)           #  20Hz
        return data
    except:
        print('Error of connection with ilo to receive message')
        return False
#-------------------------------------------------------------------------
def classification(trame, IP, Port):
    try: 
        global s
        socket_send(trame, IP, Port)
        #print('trame envoyée: ', trame)
        data = str(s.recv(1024))[1:]

        #data = socket_read(IP, Port)
        print ('data reçu:   ', data)
        #print ('data indice: ', data[2])
        #print (str(data[2:4]))
        if data[2:4] == "10":
            red_color   = data[data.find('r')+1 : data.find('g')]
            green_color = data[data.find('g')+1 : data.find('b')]
            blue_color  = data[data.find('b')+1 : data.find('o')]
            return red_color, green_color, blue_color

        if data[2:4] == "11":
            clear_left   = int(data[data.find('l')+1 : data.find('m')])
            clear_center = int(data[data.find('m')+1 : data.find('r')])
            clear_right  = int(data[data.find('r')+1 : data.find('o')])
            return clear_left, clear_center, clear_right
        
        if data[2:4] == "12":
            line_left   = int(data[data.find('l')+1 : data.find('m')])
            line_center = int(data[data.find('m')+1 : data.find('r')])
            line_right  = int(data[data.find('r')+1 : data.find('o')])
            return line_left, line_center, line_right            

        if data[2:4] == "20":
            front = data[data.find('f')+1 : data.find('r')]
            right = data[data.find('r')+1 : data.find('b')]
            back  = data[data.find('b')+1 : data.find('l')]
            left  = data[data.find('l')+1 : data.find('o')]
            return front, right, back, left
            
        if data[2:4] == "30":
            roll  = int(data[data.find('r')+1 : data.find('p')])
            pitch = int(data[data.find('p')+1 : data.find('y')])
            yaw   = int(data[data.find('y')+1 : data.find('o')])
            return roll, pitch, yaw
            
        if data[2:4] == "32":
            accelX  = int(data[data.find('x')+1 : data.find('y')])
            accelY  = int(data[data.find('y')+1 : data.find('z')])
            accelZ  = int(data[data.find('z')+1 : data.find('t')])
            gyroX   = int(data[data.find('t')+1 : data.find('r')])
            gyroY   = int(data[data.find('r')+1 : data.find('l')])
            gyroZ   = int(data[data.find('l')+1 : data.find('o')])
            return accelX, accelY, accelZ, gyroX, gyroY, gyroZ

        if data[2:4] == "40":
            status_battery      = int(data[data.find('s')+1 : data.find('p')])
            pourcentage_battery = int(data[data.find('p')+1 : data.find('o')]) 
            return status_battery, pourcentage_battery
        
        if data[2:4] == "50":
            red_led   = int(data[data.find('r')+1 : data.find('g')])
            green_led = int(data[data.find('g')+1 : data.find('b')])
            blue_led  = int(data[data.find('b')+1 : data.find('o')])
            return red_led, green_led, blue_led
        
        if data[2:4] == "60":
            acc_motor  = int(data[data.find('a')+1 : data.find('o')])
            return acc_motor
        
    except:
        print('Communication Err: classification')
        return -1
#-------------------------------------------------------------------------
def ping_ip(ip, count=2, timeout=5):
    
    """
    Ping une adresse IP pour vérifier si elle est active.
    
    Paramètres:
    ip (str): L'adresse IP à pinger.
    count (int): Nombre de tentatives de ping (par défaut 1).
    timeout (int): Délai d'attente pour chaque ping en secondes (par défaut 1).
    
    Retourne:
    bool: True si l'adresse IP est joignable, False sinon.
    """
    # Détermine la commande en fonction du système d'exploitation
    param_count = '-n' if platform.system().lower() == 'windows' else '-c'
    param_timeout = '-w' if platform.system().lower() == 'windows' else '-W'
    
    command = ['ping', param_count, str(count), param_timeout, str(timeout), ip]
    
    try:
        # Exécute la commande ping et capture la sortie
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Vérifie la sortie en fonction du système d'exploitation
        if platform.system().lower() == 'windows':
            return 'TTL=' in output.stdout
        else:
            return '1 packets received' in output.stdout or '1 received' in output.stdout
    except Exception as e:
        print(f"Erreur lors de l'exécution de la commande ping: {e}")
        return False
#-------------------------------------------------------------------------
def check_ilo_on_network():
    print("Looking for ilo on your network ...")
    global tab_IP

    Port = 81
    # Check if we are using ilo on AP
    if ping_ip("192.168.4.1") == True:
        tab_IP.append(["192.168.4.1", 1])
    else:
        base_ip = "170.20.1."
        ilo_ID  = 1
        tab_IP  = []
        c = 5                             # checking 5 more IP address after

        for i in range(100, 200):         # between 192.168.1.100 and 192.168.1.200
            ip_check = f"{base_ip}{i}"
            if ping_ip(ip_check) == True:
                IP = ip_check
                if (socket_send("ilo", IP, Port)):
                    tab_IP.append([IP, ilo_ID])
                    ilo_ID +=1 
                else:
                    c -=1
                    if c==0:
                        break
            else:
                c -=1
                if c==0:
                    break

    #display the IP and ID
    #print(tab_IP)
    table = PrettyTable()
    table.field_names = ["IP Address", "ID of ilo"]
    for row in tab_IP:
        table.add_row(row)
    
    if len(tab_IP) != 0:
        print(table)
        print("")
        print("Use for exemple: my_ilo = ilo.robot(1) to created object my_ilo with the ID = 1")
    else:
        print("Unfornutaly no one ilo is present on your current network, check you connection.")
#-------------------------------------------------------------------------   
def get_IP_from_ID(ID):
    for item in tab_IP:
        if item[1] == ID:
            return item[0]
    return None
#-------------------------------------------------------------------------
#exemple of creation of object robot
#my_ilo = ilo.robot(1)

class robot(object):
    
    def __init__(self, ID):
        self.ID = ID
        self.Port = 81
        self.connect = False
        if get_IP_from_ID(self.ID):
            self.IP = get_IP_from_ID(self.ID)
            print(self.IP)
            self.connection()
        else:
            print("You have to run before the command line to know the robot present our your network: ilo.check_ilo_on_network()")

    #-----------------------------------------------------------------------------
    def connection(self):
    
        """
        Connection of your machine to robot object 
        
        """
        
        if self.connect == True:
            print('Your robot is already connected')
            return None

        else:
            print('Connecting...')
            try:
                socket_send("ilo", self.IP, self.Port)
                time.sleep(1)
                socket_send("io", self.IP, self.Port)
                print('Connected')
                self.connect == True
                '''
                ping = socket.socket()
                ping.connect((self.IP, self.Port))
                
                msg = "ilo"
                ping.send(msg.encode())
                ping.close()

                inform = socket.socket()
                inform.bind((deviceIP, self.Port))

                time.sleep(1)

                s = socket.socket()
                msg = "io"
                s.connect((self.IP, self.Port))
                s.send(msg.encode())
                '''

            except:
                print("Error connection: you have to be connect to the ilo wifi network")
                print(" --> If the disfonction continu, switch off and switch on ilo")
    #-----------------------------------------------------------------------------
    def test_connection(self):
        """
        Test the connection to the robot via a try of stop method
        :return: True or False 
        """
        try:
            self.stop()
            return True
        except:
            print("Error connection to the robot")
            return False
    #-----------------------------------------------------------------------------
    def stop(self):
        """
        Stop the robot
        :return:
        """
        socket_send("io", self.IP, self.Port)
    #-----------------------------------------------------------------------------
    def step(self, direction):
        """
        Move by step ilorobot with selected direction during 2 seconds
        :param direction:
        :return: Is a string and should be (front, back, left, right, rot_trigo or rot_clock)
        """
        #ilo.step('front')
        if self.connect:
            if isinstance(direction, str) == False:
                print ('direction should be an string as front, back, left, rot_trigo, rot_clock','stop')
                return None

            if direction == 'front':
                socket_send("iavpx110yro", self.IP, self.Port)
            elif direction == 'back':
                socket_send("iavpx010yro", self.IP, self.Port)
            elif direction == 'left':
                socket_send("iavpxy010ro", self.IP, self.Port)
            elif direction == 'right':
                socket_send("iavpxy110ro", self.IP, self.Port)
            elif direction == 'rot_trigo':
                socket_send("iavpxyr090o", self.IP, self.Port)
            elif direction == 'rot_clock':
                socket_send("iavpxyr190o", self.IP, self.Port)
            elif direction == 'stop':
                self.stop()
            else:
                print('direction name is not correct')
        else:
            print("You are not connected !")
    #-----------------------------------------------------------------------------
    def list_order(self, ilo_list):
        """
        ilo will execute a list of successive displacment define in ilo_list
        :param ilo_list: example : ['front', 'left', 'front', 'rot_trigo', 'back'] (value of ilo_list are a string)
        :return: 
        """
        if isinstance(ilo_list, list) == False:
            print ('the variable should be a list, with inside string as front, back, left, rot_trigo, rot_clock')
            return None

        for i in range(len(ilo_list)):
            self.step(ilo_list[i])
    #-----------------------------------------------------------------------------
    def correction_command(self, list_course):

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
        #-----------------------------------------------------------------------------
    #-----------------------------------------------------------------------------
    def move(self, direction, speed):
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

        corrected_command = self.correction_command(command)
        socket_send(corrected_command, self.IP, self.Port)
    #-----------------------------------------------------------------------------
    def direct_control(self, axial, radial, rotation):
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
        corrected_command = self.correction_command(command)
        socket_send(corrected_command, self.IP, self.Port)
    #-----------------------------------------------------------------------------
    def game(self):
        """
        Control ilo using arrow or numb pad of your keyboard. \n
        Available keyboard touch: 8,2,4,6,1,3 | space = stop | esc = quit
        :return:
        """

        if self.test_connection() == True:
            axial_value = 128
            radial_value = 128
            rotation_value = 128
            self.stop()
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
                elif keyboard.is_pressed("5"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    axial_value = 128
                    radial_value = 128
                    rotation_value = 128
                elif keyboard.is_pressed("esc"):
                    self.stop()
                    break

                if new_keyboard_instruction == True:
                    self.direct_control(axial_value, radial_value, rotation_value)
                    new_keyboard_instruction = False
        else:
            print("You have to be connected to ILO before play with it, use ilo.connection()")
    #-----------------------------------------------------------------------------
    def get_color_clear(self):
        return classification("i11o", self.IP, self.Port)
    
    def get_color_clear_left(self):
        return self.get_color_clear()[0]
    
    def get_color_clear_center(self):
        return self.get_color_clear()[1]

    def get_color_clear_right(self):
        return self.get_color_clear()[2]
    #-----------------------------------------------------------------------------
    def get_line(self):
        return classification("i12o", self.IP, self.Port)

    def set_line_threshold_value(self):
        socket_send("i13o", self.IP, self.Port)

    def get_distance(self):
        return classification("i20o", self.IP, self.Port)

    def get_angle():
        return classification("i30o")

    def reset_angle():
        socket_send("i31o")

    def get_imu():
        return classification("i32o")

    def get_battery():
        return classification("i40o")

    def get_led_color():
        return classification("150o")
            
    def set_led_color(r, g, b):
        # make integer test and test min and max value
        msg = "i51r"+str(r)+"g"+str(g)+"b"+str(b)+"o"
        socket_send(msg, self.IP, self.Port)    

    def set_led_shape(val):
        msg = "i52v"+str(val)+"o"
        socket_send(msg, self.IP, self.Port) 
        
    def set_led_anim(val, rep):
        msg = "i53v"+str(val)+"r"+str(rep)+"o"
        socket_send(msg, self.IP, self.Port) 

    def set_led_captor(bool):
        if (bool == True):
            msg = "i54l1o"
        elif (bool == False) :
            msg = "i54l0o"
        socket_send(msg, self.IP, self.Port) 
        
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
    def get_acc_motor():
        return classification("i60o")

    def set_acc_motor(val: int):
        # make integer test and test min and max value
        if val < 10 : val = 10
        elif val > 100 : val = 100
        msg = "i61a"+str(val)+"o"
        socket_send(msg, self.IP, self.Port) 

    def drive_single_motor(id: int, value: int):        # à mettre en pourcentage
        if id < 0 : id = 0
        elif id > 255 : id = 255
        if value < -7000 : value = -7000
        elif value > 7000 : value = 7000
        msg = "i70d"+str(id)+"v"+str(value)+"o"
        socket_send(msg, self.IP, self.Port) 

    def set_autonomous_mode(number: int):
        msg = "i80n"+str(number)+"o"
        socket_send(msg, self.IP, self.Port) 

    def get_vmax():
        pass

    def set_vmax(vmax):
        pass
            
    def led_bottom_ON():
        pass

    def led_bottom_OFF():
        pass

    def control_single_motor_front_left(value: int):  # de -100 à 100
        drive_single_motor(1,value)
        
        # if isinstance(pourcentage, int) == False:
        #     print ('value should be an integer between -100 to 100')
        # pass

    def control_single_motor_front_right(value: int):
        drive_single_motor(2,value)

    def control_single_motor_back_left(value: int):
        drive_single_motor(4, value)

    def control_single_motor_back_right(value: int):
        drive_single_motor(3, value)

    def free_motor():
        #to disconnected power on engine
        pass
        
    def set_mode_motor():
        #between positio or wheel mode
        pass
#---------------------------------------------------------------------------------



